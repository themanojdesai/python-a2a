#!/bin/bash
# Advanced intelligent release script for python-a2a

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "==============================================="
echo "    🚀 Python A2A Intelligent Release Tool 🚀"
echo "==============================================="
echo -e "${NC}"

# Find Python executable
echo -e "${GREEN}Locating Python...${NC}"
if command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo "Found Python as 'python'"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "Found Python as 'python3'"
else
    echo -e "${RED}Error: Python not found. Please make sure Python is installed and in your PATH.${NC}"
    exit 1
fi

# Version check
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo "Using $PYTHON_VERSION"

# Check for required tools
echo -e "${GREEN}Checking for required tools...${NC}"
REQUIRED_TOOLS=("git" "grep" "sed" "awk" "perl")
MISSING_TOOLS=()

for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v $tool &> /dev/null; then
        MISSING_TOOLS+=("$tool")
    fi
done

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    echo -e "${RED}Error: Missing required tools: ${MISSING_TOOLS[*]}${NC}"
    exit 1
fi

# Check for UV availability
USE_UV=false
if command -v uv &> /dev/null; then
    USE_UV=true
    echo -e "${GREEN}✅ UV found - will use for dependency management${NC}"
else
    echo -e "${YELLOW}⚠️ UV not found - will use pip instead${NC}"
    echo -e "${YELLOW}   For better performance, install UV: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
fi

# Get the new version from user
echo -e "${YELLOW}Enter the new version number (e.g., 0.4.3):${NC}"
read VERSION

# Confirm version
echo -e "${GREEN}You entered: ${VERSION}${NC}"
read -p "Is this correct? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Release aborted.${NC}"
    exit 1
fi

# Clean up previous builds first
echo -e "${GREEN}Cleaning up previous builds...${NC}"
rm -rf dist/ build/ *.egg-info/
find . -type d -name "*.egg-info" -exec rm -rf {} +
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Function to safely update version in a file
update_version() {
    local file=$1
    local pattern=$2
    
    if [ ! -f "$file" ]; then
        echo -e "  ${YELLOW}Warning: $file not found${NC}"
        return 1
    fi
    
    echo "  Updating $file"
    
    # Create a backup before making changes
    cp "$file" "${file}.bak"
    
    # Use perl for reliable in-place editing with the provided pattern
    perl -pi -e "$pattern" "$file"
    
    # Verify nothing went wrong (line count should be the same)
    orig_lines=$(wc -l < "${file}.bak")
    new_lines=$(wc -l < "$file")
    
    if [ "$orig_lines" != "$new_lines" ]; then
        echo -e "  ${RED}ERROR: Line count changed. Restoring original file.${NC}"
        mv "${file}.bak" "$file"
        return 1
    fi
    
    # Check if any changes were actually made
    if diff -q "$file" "${file}.bak" > /dev/null; then
        echo -e "  ${YELLOW}Warning: No version patterns found in $file${NC}"
        rm -f "${file}.bak"
        return 1
    fi
    
    # Remove backup if all checks pass
    rm -f "${file}.bak"
    return 0
}

# Update version numbers in files
echo -e "${GREEN}Updating version numbers...${NC}"

# Files to check and update with their specific patterns
declare -a files_to_update=(
    "python_a2a/__init__.py:s/__version__ = \"[0-9]+\.[0-9]+\.[0-9]+[a-zA-Z0-9]*\"/__version__ = \"$VERSION\"/"
    "pyproject.toml:s/version = \"[0-9]+\.[0-9]+\.[0-9]+[a-zA-Z0-9]*\"/version = \"$VERSION\"/"
    "setup.py:s/version=\"[0-9]+\.[0-9]+\.[0-9]+[a-zA-Z0-9]*\"/version=\"$VERSION\"/"
    ".uv/UVManifest.toml:s/version = \"[0-9]+\.[0-9]+\.[0-9]+[a-zA-Z0-9]*\"/version = \"$VERSION\"/"
    "UVManifest.toml:s/version = \"[0-9]+\.[0-9]+\.[0-9]+[a-zA-Z0-9]*\"/version = \"$VERSION\"/"
)

# Files that were actually updated
files_to_commit=()

# Update each file
for file_entry in "${files_to_update[@]}"; do
    # Split the entry into file path and pattern
    file=$(echo "$file_entry" | cut -d':' -f1)
    pattern=$(echo "$file_entry" | cut -d':' -f2-)
    
    if update_version "$file" "$pattern"; then
        files_to_commit+=("$file")
    fi
done

echo -e "${GREEN}Version numbers updated to $VERSION${NC}"

# Discover package structure
echo -e "${GREEN}Analyzing package structure...${NC}"

# Find all Python package directories
PACKAGE_DIRS=$(find python_a2a -type d -not -path "*/\.*" | sort)
echo "Discovered package directories:"
for dir in $PACKAGE_DIRS; do
    if [ -f "$dir/__init__.py" ]; then
        echo "  ✓ $dir (has __init__.py)"
    else
        echo "  ✗ $dir (missing __init__.py)"
        if [ "$dir" != "python_a2a/docs" ]; then  # Skip docs directory
            echo "    Creating __init__.py"
            touch "$dir/__init__.py"
            files_to_commit+=("$dir/__init__.py")
        fi
    fi
done

# Dynamically discover all submodules
echo -e "${GREEN}Discovering Python modules...${NC}"
MODULES=()
for dir in $PACKAGE_DIRS; do
    if [ -f "$dir/__init__.py" ]; then
        # Convert directory path to module path
        MODULE=$(echo $dir | sed 's/\//./g')
        MODULES+=("$MODULE")
        
        # Find all Python files in this directory
        for py_file in $(find "$dir" -maxdepth 1 -name "*.py" -not -name "__init__.py"); do
            # Extract module name from filename
            MODULE_FILE=$(basename "$py_file" .py)
            MODULES+=("$MODULE.$MODULE_FILE")
        done
    fi
done

echo "Discovered modules:"
for module in "${MODULES[@]}"; do
    echo "  $module"
done

# Verify MANIFEST.in exists
if [ ! -f "MANIFEST.in" ]; then
    echo -e "${YELLOW}Creating MANIFEST.in file...${NC}"
    cat > MANIFEST.in << 'EOF'
include LICENSE
include README.md
include CONTRIBUTING.md
include DOCUMENTATION.md
include PUBLICATION_GUIDE.md
include pyproject.toml
include requirements.txt
include *.md
include Makefile
include setup.py
include .readthedocs.yml

recursive-include python_a2a *.py
recursive-include python_a2a py.typed
recursive-include docs *.py *.rst

global-exclude *.pyc
global-exclude __pycache__
global-exclude *.so
global-exclude .DS_Store
EOF
    files_to_commit+=("MANIFEST.in")
fi

# Dynamically extract dependencies from package files
echo -e "${GREEN}Analyzing package dependencies...${NC}"

# Function to extract package names from requirement specs
extract_package_names() {
    # Remove version specifiers, quotes, and blank lines
    sed 's/>.*//;s/=.*//;s/<.*//;s/~.*//;s/\^.*//;s/"//g;s/'\''//g' | grep -v '^$' | grep -v '^#'
}

# Extract dependencies from pyproject.toml if it exists
if [ -f "pyproject.toml" ]; then
    echo "Extracting dependencies from pyproject.toml..."
    # This extracts lines between dependencies = [ and the next closing ]
    PYPROJECT_DEPS=$(awk '/dependencies *= *\[/,/\]/' pyproject.toml | 
                     grep -v "dependencies *= *\[" | 
                     grep -v "\]" | 
                     extract_package_names)
    echo "Found in pyproject.toml: "
    echo "$PYPROJECT_DEPS" | sed 's/^/  /'
else
    PYPROJECT_DEPS=""
fi

# Extract dependencies from setup.py
if [ -f "setup.py" ]; then
    echo "Extracting dependencies from setup.py..."
    # Look for install_requires list
    SETUP_DEPS=$(grep -A 50 "install_requires" setup.py | 
                 grep -B 50 -m 1 "\]" | 
                 grep "\"" | 
                 extract_package_names)
    echo "Found in setup.py: "
    echo "$SETUP_DEPS" | sed 's/^/  /'
else
    SETUP_DEPS=""
fi

# Extract dependencies from requirements.txt if it exists
if [ -f "requirements.txt" ]; then
    echo "Extracting dependencies from requirements.txt..."
    REQUIREMENTS_DEPS=$(grep -v "^#" requirements.txt | extract_package_names)
    echo "Found in requirements.txt: "
    echo "$REQUIREMENTS_DEPS" | sed 's/^/  /'
else
    REQUIREMENTS_DEPS=""
fi

# Combine all dependencies and remove duplicates
ALL_DEPS=$(echo -e "$PYPROJECT_DEPS\n$SETUP_DEPS\n$REQUIREMENTS_DEPS" | sort -u | grep -v '^$')
echo -e "${GREEN}All dependencies found:${NC}"
echo "$ALL_DEPS" | sed 's/^/  /'

# Auto-detect dependency categories by common patterns
echo -e "${GREEN}Auto-detecting dependency categories...${NC}"

# Function to check dependencies against a pattern
check_category() {
    local category=$1
    local patterns=$2
    local found=false
    
    for pattern in $patterns; do
        if echo "$ALL_DEPS" | grep -q "$pattern"; then
            echo -e "  ✅ $category: Found dependencies ($pattern)"
            found=true
            break
        fi
    done
    
    if ! $found; then
        echo -e "  ❌ $category: Missing dependencies! (needs one of: $patterns)"
        return 1
    fi
    
    return 0
}

# Auto-detect critical categories
MISSING_DEPS=false

# HTTP Clients
check_category "HTTP Clients" "requests httpx aiohttp" || MISSING_DEPS=true

# Server frameworks
check_category "Server Frameworks" "flask fastapi uvicorn" || MISSING_DEPS=true

# LLM Providers
check_category "LLM Providers" "openai anthropic boto3" || MISSING_DEPS=true

# Data Processing
check_category "Data Processing" "pydantic" || MISSING_DEPS=true

if $MISSING_DEPS; then
    echo -e "${RED}Critical dependencies missing. Please add these to your package configuration before releasing.${NC}"
    exit 1
fi

# Commit changes locally - DO NOT PUSH until everything is verified
if [ ${#files_to_commit[@]} -gt 0 ]; then
    echo -e "${GREEN}Committing version changes locally...${NC}"
    git add "${files_to_commit[@]}"
    git commit -m "Bump version to $VERSION"
    echo "Changes committed locally. Will push only after all checks pass."
else
    echo -e "${YELLOW}No files updated. Will continue with existing files.${NC}"
fi

# Setup build environment
echo -e "${GREEN}Setting up build environment...${NC}"
BUILD_ENV=".build-env"

# Clean up any existing environments
rm -rf $BUILD_ENV

if $USE_UV; then
    echo "Creating virtual environment with UV..."
    uv venv $BUILD_ENV
    source $BUILD_ENV/bin/activate
    uv pip install build twine
else
    echo "Creating virtual environment with pip..."
    $PYTHON_CMD -m venv $BUILD_ENV
    source $BUILD_ENV/bin/activate
    $PYTHON_CMD -m pip install build twine
fi

# Build the package
echo -e "${GREEN}Building the package...${NC}"
$PYTHON_CMD -m build

# Check the distribution with twine
echo -e "${GREEN}Checking the distribution...${NC}"
twine check dist/*

# Create test script for verifying the package
echo -e "${GREEN}Creating package verification script...${NC}"
TEST_SCRIPT=$(mktemp)

# Write a dynamic test script based on discovered modules
cat > $TEST_SCRIPT << EOF
#!/usr/bin/env python
"""
Dynamic verification script for python-a2a package.
"""

import sys
import importlib
import pkgutil
import inspect
import os

def print_color(text, color_code):
    """Print colored text to the terminal."""
    if sys.stdout.isatty():
        print(f"\033[{color_code}m{text}\033[0m")
    else:
        print(text)

def print_success(text):
    print_color(f"✅ {text}", "0;32")

def print_warning(text):
    print_color(f"⚠️ {text}", "1;33")

def print_error(text):
    print_color(f"❌ {text}", "0;31")

def print_header(text):
    print_color(f"\n=== {text} ===", "0;34")

print_header("Python A2A Package Verification")
print(f"Python: {sys.version}")

# Track if all tests pass
all_passed = True

# First, check if the package is importable
try:
    import python_a2a
    print_success(f"Successfully imported python_a2a {python_a2a.__version__}")
except ImportError as e:
    print_error(f"Failed to import python_a2a: {e}")
    sys.exit(1)

# Dynamically discover all modules in the package
print_header("Module Discovery")

modules_to_check = []

# Start with the base package
modules_to_check.append("python_a2a")

# Discover all subpackages
for _, name, is_pkg in pkgutil.iter_modules(python_a2a.__path__, "python_a2a."):
    if is_pkg:
        modules_to_check.append(name)
        
        # Get the actual module
        try:
            subpkg = importlib.import_module(name)
            # Add modules from this subpackage
            subpkg_path = getattr(subpkg, "__path__", None)
            if subpkg_path:
                for _, subname, _ in pkgutil.iter_modules(subpkg_path, f"{name}."):
                    modules_to_check.append(subname)
        except ImportError:
            # Skip if we can't import the subpackage
            pass

print(f"Discovered {len(modules_to_check)} modules to check")

# Check each module
print_header("Module Import Tests")
import_results = {"success": [], "failure": []}

for module_name in sorted(modules_to_check):
    try:
        module = importlib.import_module(module_name)
        import_results["success"].append(module_name)
        print_success(f"{module_name}")
    except ImportError as e:
        import_results["failure"].append((module_name, str(e)))
        print_error(f"{module_name}: {e}")
        all_passed = False

print(f"\nSuccessfully imported {len(import_results['success'])} modules")
if import_results["failure"]:
    print_error(f"Failed to import {len(import_results['failure'])} modules")
    all_passed = False

# Dynamically identify feature flags and critical features
if hasattr(python_a2a, "HAS_MODELS"):
    print_header("Feature Flags")
    
    # Find all HAS_* attributes
    feature_flags = [attr for attr in dir(python_a2a) if attr.startswith("HAS_")]
    
    # Auto-detect critical features
    # Assume that any feature directly related to core components is critical
    core_components = ["MODELS", "CLIENT", "SERVER", "MCP"]
    critical_features = []
    
    for flag in feature_flags:
        for component in core_components:
            if component in flag:
                critical_features.append(flag)
                break
    
    # Check each feature flag
    for flag in sorted(feature_flags):
        value = getattr(python_a2a, flag, False)
        if value:
            print_success(f"{flag}: {value}")
        else:
            if flag in critical_features:
                print_error(f"{flag}: {value} (CRITICAL)")
                all_passed = False
            else:
                print_warning(f"{flag}: {value}")
    
    print("\nCritical features detected:", ", ".join(critical_features))

# Test getting actual instances of key classes
print_header("Class Instance Tests")

try:
    # Try to create a basic message
    from python_a2a.models import Message, TextContent, MessageRole
    msg = Message(
        content=TextContent(text="Test message"),
        role=MessageRole.USER
    )
    print_success("Created Message instance")
except Exception as e:
    print_error(f"Failed to create Message instance: {e}")
    all_passed = False

# MCP functionality if available
if getattr(python_a2a, "HAS_MCP", False):
    try:
        # Try to import MCP classes
        from python_a2a.mcp.fastmcp import text_response
        resp = text_response("Test response")
        print_success("Created MCP response")
    except Exception as e:
        print_error(f"Failed to create MCP response: {e}")
        all_passed = False

# Print summary
print_header("Verification Summary")
if all_passed:
    print_success("All tests passed - package is ready for release!")
    sys.exit(0)
else:
    print_error("Some tests failed - fix issues before releasing")
    sys.exit(1)
EOF

# Create a test environment to verify the package works correctly
echo -e "${GREEN}Testing package in a clean environment...${NC}"
TEST_ENV=".test-env"
deactivate

# Clean up any existing environments
rm -rf $TEST_ENV

if $USE_UV; then
    echo "Creating test environment with UV..."
    uv venv $TEST_ENV
    source $TEST_ENV/bin/activate
    uv pip install $(find dist -name "*.whl")
else
    echo "Creating test environment with pip..."
    $PYTHON_CMD -m venv $TEST_ENV
    source $TEST_ENV/bin/activate
    $PYTHON_CMD -m pip install $(find dist -name "*.whl")
fi

# Run verification script
echo -e "${GREEN}Running verification tests...${NC}"
$PYTHON_CMD $TEST_SCRIPT
VERIFICATION_RESULT=$?

# Clean up test script
rm -f $TEST_SCRIPT

if [ $VERIFICATION_RESULT -ne 0 ]; then
    echo -e "${RED}Package verification failed! Fix the issues before releasing.${NC}"
    deactivate
    exit 1
fi

echo -e "${GREEN}Package verification passed!${NC}"

# Deactivate and clean up test environment
deactivate
rm -rf $TEST_ENV

# NOW is the time to push changes, after verification has passed
echo -e "${GREEN}All checks passed! Pushing changes to GitHub...${NC}"
git push origin main

# Back to build environment
source $BUILD_ENV/bin/activate

# Upload to PyPI without prompting for credentials
echo -e "${YELLOW}Ready to upload to PyPI.${NC}"
read -p "Upload to PyPI? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Uploading to PyPI...${NC}"
    # Use twine without explicit credentials - will use .pypirc or prompt automatically
    twine upload dist/*
    
    echo -e "${GREEN}Package uploaded to PyPI successfully!${NC}"
    
    # Create and push a git tag
    echo -e "${GREEN}Creating git tag v$VERSION...${NC}"
    git tag -a "v$VERSION" -m "Release v$VERSION"
    git push origin "v$VERSION"
    
    echo -e "${GREEN}All done! Version $VERSION has been released.${NC}"
else
    echo -e "${RED}PyPI upload aborted.${NC}"
    exit 1
fi

# Verify the published package
echo -e "${GREEN}Verifying the published package from PyPI...${NC}"
VERIFY_ENV=".verify-env"
deactivate

# Clean up any existing environment
rm -rf $VERIFY_ENV

# Wait for PyPI to process the upload - may take some time
echo "Waiting for PyPI to process the package..."
# Longer initial wait
sleep 60

# Create verification environment
if $USE_UV; then
    echo "Creating verification environment with UV..."
    uv venv $VERIFY_ENV
    source $VERIFY_ENV/bin/activate
else
    echo "Creating verification environment with pip..."
    $PYTHON_CMD -m venv $VERIFY_ENV
    source $VERIFY_ENV/bin/activate
fi

# Try several times with increasing delays
MAX_ATTEMPTS=5
for (( attempt=1; attempt<=MAX_ATTEMPTS; attempt++ ))
do
    echo "Attempt $attempt/$MAX_ATTEMPTS to install $VERSION from PyPI..."
    
    if $USE_UV; then
        uv pip install "python-a2a==$VERSION" && break
    else
        $PYTHON_CMD -m pip install "python-a2a==$VERSION" && break
    fi
    
    echo "Package not available yet. Waiting longer..."
    # Exponential backoff
    sleep $((30 * attempt))
    
    if [ $attempt -eq $MAX_ATTEMPTS ]; then
        echo -e "${YELLOW}Could not verify the package after $MAX_ATTEMPTS attempts.${NC}"
        echo -e "${YELLOW}This is often normal - PyPI can take 5-15 minutes to process new packages.${NC}"
        echo -e "${YELLOW}You can verify manually later with: pip install python-a2a==$VERSION${NC}"
        deactivate
        rm -rf $VERIFY_ENV
        
        echo -e "${BLUE}"
        echo "==============================================="
        echo "    🎉 Release process completed! 🎉"
        echo "==============================================="
        echo -e "${NC}"
        exit 0
    fi
done

# If we got here, the installation was successful
echo -e "${GREEN}Successfully installed python-a2a $VERSION from PyPI!${NC}"

# Test core imports
$PYTHON_CMD -c "import python_a2a; print(f'Installed version: {python_a2a.__version__}')"
VERIFY_RESULT=$?

if [ $VERIFY_RESULT -eq 0 ]; then
    # Also check MCP availability dynamically
    $PYTHON_CMD -c "import python_a2a; print('MCP available: ' + str(getattr(python_a2a, 'HAS_MCP', False)))" 2>/dev/null
    MCP_RESULT=$?
    
    if [ $MCP_RESULT -eq 0 ]; then
        echo -e "${GREEN}Verification successful!${NC}"
        echo -e "${GREEN}Package python-a2a v$VERSION is now available on PyPI with all features.${NC}"
    else
        echo -e "${YELLOW}Basic verification successful, but full feature check failed.${NC}"
        echo -e "${YELLOW}Check if all dependencies were properly installed.${NC}"
    fi
else
    echo -e "${RED}Verification failed! The package may not be properly available on PyPI yet.${NC}"
    echo -e "${YELLOW}Wait a few minutes and try installing it manually.${NC}"
fi

# Clean up
deactivate
rm -rf $BUILD_ENV $VERIFY_ENV

echo -e "${BLUE}"
echo "==============================================="
echo "    🎉 Release process completed! 🎉"
echo "==============================================="
echo -e "${NC}"