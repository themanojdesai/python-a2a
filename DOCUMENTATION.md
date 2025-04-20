## Documentation

Documentation for Python A2A is available at [ReadTheDocs](https://python-a2a.readthedocs.io/).

### Building Documentation Locally

To build the documentation locally:

1. Install the required dependencies:

```bash
pip install -e ".[all]"
pip install -r docs/requirements.txt
```

2. Navigate to the `docs` directory:

```bash
cd docs
```

3. Build the HTML documentation:

```bash
make html
```

4. Open the generated documentation in your browser:

```bash
# On macOS
open _build/html/index.html

# On Linux
xdg-open _build/html/index.html

# On Windows
start _build/html/index.html
```

### Contributing to Documentation

If you want to contribute to the documentation, please follow the structure in the `docs` directory and write documentation in reStructuredText (.rst) format. The documentation system uses Sphinx and is automatically built and deployed to ReadTheDocs when changes are pushed to the main branch.