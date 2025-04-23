#!/usr/bin/env python
"""
Diagnostic script for the python-a2a package.
"""

import sys
import importlib
import warnings
import pkg_resources

def check_import(module_name):
    try:
        module = importlib.import_module(module_name)
        print(f"✅ Successfully imported {module_name}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import {module_name}: {e}")
        return False

def check_package(package_name):
    try:
        pkg_resources.get_distribution(package_name)
        print(f"✅ Package {package_name} is installed")
        return True
    except pkg_resources.DistributionNotFound:
        print(f"❌ Package {package_name} is not installed")
        return False

def print_header(text):
    print(f"\n=== {text} ===")

print_header("Python A2A Diagnostics")
print(f"Python: {sys.version}")
print(f"Path: {sys.path}")

print_header("Package Installation Check")
python_a2a_installed = check_package("python-a2a")
print_header("Core Dependencies")
check_package("requests")

print_header("Optional Dependencies")
check_package("flask")
check_package("openai")
check_package("anthropic")
check_package("httpx")
check_package("fastapi")
check_package("boto3")

if python_a2a_installed:
    print_header("Basic Import Tests")
    check_import("python_a2a")
    check_import("python_a2a.models")
    check_import("python_a2a.client")
    check_import("python_a2a.server")
    
    print_header("Feature Tests")
    try:
        import python_a2a
        print(f"Version: {python_a2a.__version__}")
        
        # Check feature flags
        features = {
            "Models": getattr(python_a2a, "HAS_MODELS", False),
            "Advanced Models": getattr(python_a2a, "HAS_ADVANCED_MODELS", False),
            "HTTP Client": getattr(python_a2a, "HAS_HTTP_CLIENT", False),
            "LLM Clients": getattr(python_a2a, "HAS_LLM_CLIENTS", False),
            "Server": getattr(python_a2a, "HAS_SERVER", False),
            "MCP": getattr(python_a2a, "HAS_MCP", False),
            "Workflow": getattr(python_a2a, "HAS_WORKFLOW", False)
        }
        
        for feature, available in features.items():
            print(f"{feature}: {'✅ Available' if available else '❌ Not Available'}")
            
    except Exception as e:
        print(f"❌ Error checking python-a2a features: {e}")
else:
    print("\nPackage not installed. Install with:")
    print("  pip install python-a2a")
    print("  pip install \"python-a2a[all]\"  # For all features")

print("\nDiagnostics complete.")

if __name__ == "__main__":
    # Add optional feature to dump full import path information
    if "--debug" in sys.argv:
        print_header("Python Path Details")
        for i, path in enumerate(sys.path):
            print(f"{i}: {path}")
        
        print_header("Package Locations")
        try:
            import python_a2a
            print(f"python_a2a: {python_a2a.__file__}")
            
            try:
                import python_a2a.models
                print(f"python_a2a.models: {python_a2a.models.__file__}")
            except ImportError:
                print("python_a2a.models: Not found")
                
            try:
                import python_a2a.mcp
                print(f"python_a2a.mcp: {python_a2a.mcp.__file__}")
            except ImportError:
                print("python_a2a.mcp: Not found")
        except ImportError:
            print("python_a2a not installed")