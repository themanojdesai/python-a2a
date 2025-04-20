.PHONY: setup clean format lint test docs build publish

# Set up Python environment with UV and install dependencies
setup:
	@echo "Setting up development environment with UV..."
	@command -v uv >/dev/null 2>&1 || (echo "UV not found. Installing UV..." && curl -LsSf https://astral.sh/uv/install.sh | sh)
	@uv venv
	@. .venv/bin/activate && uv install -e ".[dev]"
	@echo "Development environment set up successfully!"

# Clean up Python artifacts and build directories
clean:
	@echo "Cleaning up Python artifacts and build directories..."
	@rm -rf build/ dist/ *.egg-info/ .pytest_cache/ __pycache__/ .coverage htmlcov/
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@find . -type f -name ".DS_Store" -delete
	@find . -type f -name "*.so" -delete
	@find . -name "*.coverage" -delete
	@echo "Cleanup complete!"

# Format code with black and isort
format:
	@echo "Formatting code with black and isort..."
	@black python_a2a
	@isort python_a2a
	@echo "Code formatting complete!"

# Lint code with flake8 and mypy
lint:
	@echo "Linting code with flake8 and mypy..."
	@flake8 python_a2a
	@mypy python_a2a
	@echo "Linting complete!"

# Run tests with pytest
test:
	@echo "Running tests with pytest..."
	@pytest -v
	@echo "Tests complete!"

# Build documentation with Sphinx
docs:
	@echo "Building documentation with Sphinx..."
	@cd docs && make html
	@echo "Documentation built successfully! Open docs/_build/html/index.html to view."

# Build distribution packages
build: clean
	@echo "Building distribution packages..."
	@python -m build
	@echo "Build complete! Packages are in the dist/ directory."

# Publish package to PyPI
publish: build
	@echo "Publishing package to PyPI..."
	@twine check dist/*
	@twine upload dist/*
	@echo "Package published successfully!"

# Install in development mode with UV
dev-install:
	@echo "Installing in development mode with UV..."
	@uv install -e ".[dev]"
	@echo "Development installation complete!"

# Run example program
run-example:
	@echo "Running example program..."
	@python examples/simple_agent.py

# Default target
help:
	@echo "Available commands:"
	@echo "  make setup         - Set up development environment with UV"
	@echo "  make clean         - Clean up Python artifacts and build directories"
	@echo "  make format        - Format code with black and isort"
	@echo "  make lint          - Lint code with flake8 and mypy"
	@echo "  make test          - Run tests with pytest"
	@echo "  make docs          - Build documentation with Sphinx"
	@echo "  make build         - Build distribution packages"
	@echo "  make publish       - Publish package to PyPI"
	@echo "  make dev-install   - Install in development mode with UV"
	@echo "  make run-example   - Run example program"