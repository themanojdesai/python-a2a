# Publication Guide for Python A2A

This document provides step-by-step instructions for publishing a new version of the Python A2A package.

## Prerequisites

1. Ensure you have the necessary permissions for the PyPI package
2. Install required tools:
   ```bash
   uv pip install build twine
   ```
3. Have a clean working directory (commit all changes)

## Step 1: Update Version Numbers

Update the version number in these files:

1. `python_a2a/__init__.py` - Update `__version__ = "0.3.3"`
2. `pyproject.toml` - Update `version = "0.3.3"` under `[project]`
3. `setup.py` - Update `version="0.3.3"`
4. `UVManifest.toml` - Update `version = "0.3.3"` under `[project]`

## Step 2: Update Documentation

1. Update `README.md` with any new features or changes
2. Update the `RELEASE_NOTES.md` with details about the new version
3. Update any relevant documentation pages in the `docs/` directory
4. Ensure the documentation builds successfully:
   ```bash
   cd docs
   uv pip install -r requirements.txt
   make html
   ```

## Step 3: Run Tests

Ensure all tests pass with UV:

```bash
uv pip run pytest
```

## Step 4: Build the Package

Build both wheel and sdist distributions:

```bash
rm -rf dist/ build/ *.egg-info/
uv pip run python -m build
```

This will create distribution files in the `dist/` directory.

## Step 5: Test the Distribution

Check the package with twine:

```bash
uv pip run twine check dist/*
```

## Step 6: Test on TestPyPI (Optional but Recommended)

Upload to TestPyPI to verify everything works:

```bash
uv pip run twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

Then test installation:

```bash
# Create a test environment
uv venv create --fresh .test-venv
source .test-venv/bin/activate

# Install from TestPyPI
uv pip install --index-url https://test.pypi.org/simple/ --no-deps python-a2a

# Test import
python -c "import python_a2a; print(python_a2a.__version__)"
```

## Step 7: Upload to PyPI

Once everything is confirmed working, upload to PyPI:

```bash
uv pip run twine upload dist/*
```

## Step 8: Tag the Release

Create a git tag for the release:

```bash
git tag -a "v0.3.3" -m "Release v0.3.3"
git push origin "v0.3.3"
```

## Step 9: Create a GitHub Release

1. Go to the GitHub repository
2. Click on "Releases"
3. Click "Draft a new release"
4. Select the tag you just created
5. Enter a title (e.g., "v0.3.3")
6. Copy the relevant section from `RELEASE_NOTES.md` into the description
7. If applicable, attach any additional files
8. Click "Publish release"

## Step 10: Announce the Release

Announce the new release in appropriate channels:
- Project documentation site
- Relevant community forums
- Social media
- Mailing lists

## Automated Publication

You can use the provided publication script to automate this process:

```bash
bash scripts/publish.sh
```

This script will:
1. Check version consistency
2. Clean previous builds
3. Build the package
4. Run checks
5. Upload to TestPyPI (optional)
6. Upload to PyPI (with confirmation)
7. Create git tags (with confirmation)

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Make sure you have a `.pypirc` file or set up a PyPI API token
2. **Version Conflicts**: Ensure the version number is unique and not already published
3. **Build Errors**: Check that all dependencies are properly installed and files are correctly included

### Need Help?

If you encounter issues during publication:
1. Check the PyPI documentation: https://packaging.python.org/tutorials/packaging-projects/
2. Consult the twine documentation: https://twine.readthedocs.io/
3. Open an issue on the GitHub repository