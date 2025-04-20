#!/bin/bash
# Automated release script for python-a2a

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the new version from user
echo -e "${YELLOW}Enter the new version number (e.g., 0.3.3):${NC}"
read VERSION

# Confirm version
echo -e "${GREEN}You entered: ${VERSION}${NC}"
read -p "Is this correct? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Release aborted.${NC}"
    exit 1
fi

# Check if we're in a clean git state
if [[ -n $(git status -s) ]]; then
    echo -e "${YELLOW}You have uncommitted changes.${NC}"
    echo -e "It's recommended to commit all changes before releasing."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Release aborted.${NC}"
        exit 1
    fi
fi

# Clean up previous builds first
echo -e "${GREEN}Cleaning up previous builds...${NC}"
rm -rf dist/ build/ *.egg-info/
find . -type d -name "*.egg-info" -exec rm -rf {} +
find . -type d -name "__pycache__" -exec rm -rf {} +

# Update version numbers in files
echo -e "${GREEN}Updating version numbers...${NC}"

# Update __init__.py
sed -i.bak "s/__version__ = \"[0-9.]*\"/__version__ = \"$VERSION\"/" python_a2a/__init__.py
rm python_a2a/__init__.py.bak

# Update pyproject.toml
sed -i.bak "s/version = \"[0-9.]*\"/version = \"$VERSION\"/" pyproject.toml
rm pyproject.toml.bak

# Update setup.py
sed -i.bak "s/version=\"[0-9.]*\"/version=\"$VERSION\"/" setup.py
rm setup.py.bak

# Update UVManifest.toml
sed -i.bak "s/version = \"[0-9.]*\"/version = \"$VERSION\"/" UVManifest.toml
rm UVManifest.toml.bak

echo -e "${GREEN}Version numbers updated to $VERSION${NC}"

# Commit changes
echo -e "${GREEN}Committing version changes...${NC}"
git add python_a2a/__init__.py pyproject.toml setup.py UVManifest.toml
git commit -m "Bump version to $VERSION"

# Push to GitHub
echo -e "${GREEN}Pushing changes to GitHub...${NC}"
git push origin main

# Install build dependencies
echo -e "${GREEN}Installing build dependencies...${NC}"
uv pip install build twine

# Build the package
echo -e "${GREEN}Building the package...${NC}"
uv pip run python -m build

# Check the distribution with twine
echo -e "${GREEN}Checking the distribution...${NC}"
uv pip run twine check dist/*

# Upload to PyPI
echo -e "${YELLOW}Ready to upload to PyPI.${NC}"
read -p "Upload to PyPI? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Uploading to PyPI...${NC}"
    uv pip run twine upload dist/*
    
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
echo -e "${GREEN}Verifying the published package...${NC}"
uv venv create --fresh .verify-env
source .verify-env/bin/activate
uv pip install python-a2a==$VERSION
INSTALLED_VERSION=$(python -c "import python_a2a; print(python_a2a.__version__)")

if [ "$INSTALLED_VERSION" == "$VERSION" ]; then
    echo -e "${GREEN}Verification successful!${NC}"
    echo -e "${GREEN}Package python-a2a v$VERSION is now available on PyPI.${NC}"
else
    echo -e "${RED}Verification failed!${NC}"
    echo -e "Expected version: $VERSION, got: $INSTALLED_VERSION"
fi

# Clean up
deactivate
rm -rf .verify-env

echo -e "${GREEN}Release process completed!${NC}"