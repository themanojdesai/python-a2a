Contributing
============

Thank you for your interest in contributing to Python A2A! This guide will help you get started.

Code of Conduct
--------------

Everyone participating in the Python A2A project is expected to treat other people with respect and follow these guidelines:

- Use welcoming and inclusive language
- Be respectful of different viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

Development Setup
---------------

Here's how to set up Python A2A for local development:

1. Fork the `python-a2a <https://github.com/themanojdesai/python-a2a>`_ repo on GitHub.

2. Clone your fork locally:

   .. code-block:: bash

      git clone git@github.com:YOUR_USERNAME/python-a2a.git
      cd python-a2a

3. Create a virtual environment and install the development dependencies:

   .. code-block:: bash

      python -m venv venv
      source venv/bin/activate  # On Windows: venv\Scripts\activate
      pip install -e ".[dev]"

4. Create a branch for your changes:

   .. code-block:: bash

      git checkout -b name-of-your-bugfix-or-feature

5. Make your changes and run the tests to ensure everything works:

   .. code-block:: bash

      pytest

Code Style
---------

Python A2A follows these code style guidelines:

- We use `Black <https://github.com/psf/black>`_ for code formatting
- We use `isort <https://pycqa.github.io/isort/>`_ for import sorting
- We use `flake8 <https://flake8.pycqa.org/>`_ for linting

You can automatically format your code by running:

.. code-block:: bash

   black python_a2a
   isort python_a2a

And check for issues with:

.. code-block:: bash

   flake8 python_a2a

Type Hints
---------

Python A2A uses type hints to improve code quality and IDE support. Please add type hints to your code following these guidelines:

- Add type hints to all function arguments and return values
- Use ``Optional[T]`` for arguments that could be ``None``
- Use ``Union[T1, T2]`` for arguments that could be multiple types
- Use ``Any`` sparingly, and only when necessary

Documentation
-----------

Documentation is written in reStructuredText (.rst) and built with Sphinx. To build the documentation locally:

1. Install the documentation dependencies:

   .. code-block:: bash

      pip install -r docs/requirements.txt

2. Build the documentation:

   .. code-block:: bash

      cd docs
      make html

3. View the documentation in your browser:

   .. code-block:: bash

      # On macOS
      open _build/html/index.html

      # On Linux
      xdg-open _build/html/index.html

      # On Windows
      start _build/html/index.html

When writing documentation:

- Use clear, concise language
- Include examples where appropriate
- Update documentation when you change code
- Add docstrings to all public functions, classes, and methods

Pull Request Process
------------------

1. Update the documentation with details of changes to the interface, including new environment variables, exposed ports, useful file locations, and container parameters.

2. Make sure all tests pass and the code follows the project's style guidelines.

3. Update the README.md or other relevant documentation if needed.

4. The versioning scheme we use is `SemVer <http://semver.org/>`_. 

5. Submit a pull request to the main repository. In your pull request description, explain the changes and reference any relevant issues.

6. Your pull request will be reviewed by the maintainers. You may be asked to make changes before it's accepted.

7. Once your pull request is approved, it will be merged into the main branch.

Adding New Features
-----------------

If you want to add a new feature to Python A2A, please follow these guidelines:

1. First, open an issue to discuss the feature before implementing it. This helps ensure that your work won't be rejected.

2. Keep new features modular and composable with existing functionality.

3. Add appropriate tests and documentation for your feature.

4. Ensure backward compatibility whenever possible.

Reporting Bugs
------------

When reporting bugs, please include:

1. The version of Python A2A you're using
2. Your operating system and Python version
3. Detailed steps to reproduce the bug
4. What you expected to happen
5. What actually happened
6. Any error messages or stack traces

License
------

By contributing to Python A2A, you agree that your contributions will be licensed under the project's MIT License.