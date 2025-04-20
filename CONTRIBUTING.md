# Contributing to Python A2A

First off, thank you for considering contributing to Python A2A! It's people like you that make Python A2A such a great tool.

## Quick Links

- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Project Documentation](#project-documentation)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Development Setup

Here's how to set up Python A2A for local development:

1. Fork the `python-a2a` repo on GitHub.
2. Clone your fork locally:
   ```bash
   git clone git@github.com:YOUR_USERNAME/python-a2a.git
   cd python-a2a
   ```
3. Create a virtual environment and install the development dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```
4. Create a branch for your changes:
   ```bash
   git checkout -b name-of-your-bugfix-or-feature
   ```
5. Make your changes and run the tests to ensure everything works:
   ```bash
   pytest
   ```

## Code Style

Python A2A follows these code style guidelines:

- We use [Black](https://github.com/psf/black) for code formatting
- We use [isort](https://pycqa.github.io/isort/) for import sorting
- We use [flake8](https://flake8.pycqa.org/) for linting

You can automatically format your code by running:

```bash
black python_a2a
isort python_a2a
```

And check for issues with:

```bash
flake8 python_a2a
```

## Pull Request Process

1. Update the documentation with details of changes to the interface.
2. Make sure all tests pass and the code follows the project's style guidelines.
3. Update the README.md or other relevant documentation if needed.
4. Submit a pull request to the main repository.
5. Your pull request will be reviewed by the maintainers. You may be asked to make changes before it's accepted.

## Project Documentation

For more detailed information about contributing to Python A2A, please read our [comprehensive contributing guide](https://python-a2a.readthedocs.io/en/latest/contributing.html) in the project documentation.

## License

By contributing to Python A2A, you agree that your contributions will be licensed under the project's MIT License.