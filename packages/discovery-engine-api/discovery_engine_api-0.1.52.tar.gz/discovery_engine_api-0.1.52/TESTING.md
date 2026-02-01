# Testing the Discovery Engine API SDK

This guide covers different ways to test the `discovery-engine-api` package before and after publishing.

## Testing Options

### 1. Test Locally (Before Publishing)

Test the package directly from the source code:

```bash
cd engine/packages/client

# Install in development mode (editable install)
pip install -e .

# Or install with pandas support
pip install -e ".[pandas]"

# Run the unit tests
pytest tests/

# Or run the integration test script from the repo root
cd ../../..
python test_sdk.py
```

### 2. Test from Local Build (Before Publishing)

Build the package locally and install from the built wheel:

```bash
cd engine/packages/client

# Build the package
python -m build

# Install from the local build
pip install dist/discovery_engine_api-*.whl

# Or with pandas
pip install dist/discovery_engine_api-*.whl[pandas]

# Test it
python -c "from discovery import Engine; print('SDK imported successfully!')"
```

### 3. Test from TestPyPI (After Publishing to TestPyPI)

After publishing to TestPyPI using `./publish.sh test`:

```bash
# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ discovery-engine-api[pandas]

# Note: --extra-index-url is needed because TestPyPI doesn't have all dependencies
# Test it
python test_sdk.py
```

### 4. Test from Production PyPI (After Publishing)

Once published to production PyPI:

```bash
# Simple install
pip install discovery-engine-api

# With pandas support
pip install discovery-engine-api[pandas]

# Test it
python test_sdk.py
```

## Running Unit Tests

The package includes comprehensive unit tests:

```bash
cd engine/packages/client

# Install test dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=discovery --cov-report=html

# Run specific test file
pytest tests/test_client.py

# Run with verbose output
pytest tests/ -v
```

## Integration Testing

Use the test script at the repo root to test against a real API:

```bash
# From repo root
python test_sdk.py
```

This script:
- Installs the SDK (from PyPI if available, or locally)
- Creates a test dataset
- Runs a full analysis
- Displays results

**Note**: Requires a valid API key. Update `API_KEY` in `test_sdk.py` with your key.

## Testing Different Installation Methods

The test script supports different installation sources via environment variable:

```bash
# Test from local build
INSTALL_FROM=local python test_sdk.py

# Test from TestPyPI
INSTALL_FROM=testpypi python test_sdk.py

# Test from production PyPI (default)
INSTALL_FROM=pypi python test_sdk.py

# Test from local editable install
INSTALL_FROM=editable python test_sdk.py
```

## Verifying Installation

Quick verification that the package is installed correctly:

```python
# Check import
from discovery import Engine
print(f"SDK version: {Engine.__module__}")

# Check version
import discovery
print(f"Version: {discovery.__version__}")

# Test engine initialization
engine = Engine(api_key="test-key")
print(f"Base URL: {engine.base_url}")
```

## Pre-Publishing Checklist

Before publishing to PyPI, verify:

- [ ] Package builds successfully: `python -m build`
- [ ] Package passes twine check: `python -m twine check dist/*`
- [ ] Unit tests pass: `pytest tests/`
- [ ] Can install from local build: `pip install dist/discovery_engine_api-*.whl`
- [ ] Can import and use: `from discovery import Engine`
- [ ] Version is updated in `pyproject.toml` and `discovery/__init__.py`
- [ ] README is up to date
- [ ] All examples in README work

## Troubleshooting

### Import Errors

If you get import errors after installing:

```bash
# Check if package is installed
pip list | grep discovery-engine-api

# Check installation location
python -c "import discovery; print(discovery.__file__)"

# Reinstall
pip uninstall discovery-engine-api
pip install discovery-engine-api
```

### Test Failures

If tests fail:

1. Check Python version (requires >= 3.10)
2. Install all dependencies: `pip install -e ".[dev]"`
3. Check API key is valid (for integration tests)
4. Verify network connectivity to API endpoint
