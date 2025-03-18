# API Performance Test Suite

This directory contains tests for the API Performance project. The tests cover both the API and benchmark components.

## Structure

- `api/tests/`: Tests for the API application
  - `test_basic.py`: Basic sanity tests
  - `test_endpoints.py`: Tests for API endpoints
  - `test_technique_modules.py`: Tests for performance optimization technique modules
  - `conftest.py`: Fixtures and configuration for API tests

- `benchmarks/tests/`: Tests for benchmarking utilities
  - `test_benchmark_utils.py`: Tests for benchmark utility functions
  - `test_techniques.py`: Tests for technique-specific benchmark modules
  - `conftest.py`: Fixtures and configuration for benchmark tests

## Running Tests

### Installation

First, install the required dependencies:

```bash
pip install -r requirements-test.txt

# Additional dependencies needed for testing
pip install sqlalchemy redis databases asyncpg psycopg2-binary ujson orjson brotli fastapi
```

### Basic Test Execution

To run all tests:

```bash
pytest
```

To run specific test files:

```bash
pytest api/tests/test_basic.py
pytest benchmarks/tests/test_benchmark_utils.py
```

### Running Tests with Coverage

To run tests with coverage reporting:

```bash
pytest --cov=api --cov=benchmarks --cov-report=term
```

Generate an XML coverage report (useful for CI):

```bash
pytest --cov=api --cov=benchmarks --cov-report=xml
```

## Test Design

The tests are designed to be robust and work in a CI environment without requiring actual services. Key features include:

1. **Conditional Imports**: Tests use conditional imports to handle cases where modules might not exist yet.

2. **Mocking External Services**: Tests mock external dependencies like databases and Redis.

3. **Skippable Tests**: Tests that require specific dependencies will be skipped rather than fail if those dependencies are not available.

4. **Comprehensive Fixtures**: Common test fixtures are provided in `conftest.py` files.

## CI Pipeline Integration

The test suite is integrated with GitHub Actions CI pipeline:

1. **Code Quality**: Linting and formatting checks
2. **Tests**: Automated test execution with coverage reporting
3. **Build**: Docker image building and publishing

The CI pipeline configuration is in `.github/workflows/main.yml`. 