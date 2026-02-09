# Testing Guide for Dockerfile Generator

This document provides comprehensive information about testing the Dockerfile Generator application.

## Table of Contents

1. [Setup](#setup)
2. [Running Tests](#running-tests)
3. [Test Structure](#test-structure)
4. [Writing Tests](#writing-tests)
5. [Coverage](#coverage)
6. [Continuous Integration](#continuous-integration)

## Setup

### Install Testing Dependencies

```bash
# Install pytest and coverage tools
pip install pytest pytest-cov

# Optional: Install pytest-watch for automatic test re-running
pip install pytest-watch

# Optional: Install vermin for full functionality testing
pip install vermin
```

### Verify Installation

```bash
pytest --version
```

## Running Tests

### Quick Start

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=dockerfile_generator_v2
```

### Using the Test Runner Script

The `run_tests.py` script provides convenient shortcuts:

```bash
# Run all tests with coverage
python run_tests.py all

# Run only unit tests
python run_tests.py unit

# Run only integration tests
python run_tests.py integration

# Run fast tests (exclude slow tests)
python run_tests.py fast

# Run with verbose output
python run_tests.py verbose

# Generate HTML coverage report
python run_tests.py html

# Run specific test
python run_tests.py specific test_dockerfile_generator.py::TestPythonVersionDetector

# Re-run only failed tests
python run_tests.py failed
```

### Test Selection

```bash
# Run tests in a specific file
pytest test_dockerfile_generator.py

# Run a specific test class
pytest test_dockerfile_generator.py::TestPythonVersionDetector

# Run a specific test function
pytest test_dockerfile_generator.py::TestPythonVersionDetector::test_detect_python310_match_statement

# Run tests matching a pattern
pytest -k "version_detection"

# Run tests with specific marker
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

## Test Structure

### Test Organization

```
.
├── test_dockerfile_generator.py    # Main test file
├── conftest.py                      # Shared fixtures and configuration
├── pytest.ini                       # Pytest configuration
└── run_tests.py                     # Test runner script
```

### Test Classes

The test suite is organized into the following classes:

1. **TestPythonVersionDetector**
   - Tests for Python version detection
   - Both vermin and fallback methods
   - Version-specific feature detection

2. **TestPythonFileAnalyzer**
   - Tests for import extraction
   - Framework detection
   - requirements.txt parsing
   - Executable detection

3. **TestDockerfileGenerator**
   - Tests for Dockerfile generation
   - Framework-specific generation
   - System dependency detection
   - Port exposure

4. **TestEndToEnd**
   - Integration tests
   - Complete workflow testing
   - Real-world scenarios

5. **TestEdgeCases**
   - Error handling
   - Malformed input
   - Edge cases

### Test Markers

Tests are marked with the following markers:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (slower, end-to-end)
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.requires_vermin` - Tests requiring vermin package

## Test Coverage

### Current Test Coverage

The test suite aims for >80% code coverage and includes:

- ✅ Python version detection (vermin and fallback)
- ✅ Import parsing and analysis
- ✅ Framework detection (Flask, Django, FastAPI, Streamlit)
- ✅ Dockerfile generation for all app types
- ✅ System dependency detection
- ✅ requirements.txt parsing
- ✅ Edge cases and error handling

### Viewing Coverage

```bash
# Terminal report
pytest --cov=dockerfile_generator_v2 --cov-report=term-missing

# HTML report
pytest --cov=dockerfile_generator_v2 --cov-report=html
# Open htmlcov/index.html in browser

# XML report (for CI tools)
pytest --cov=dockerfile_generator_v2 --cov-report=xml
```

### Coverage Reports

Coverage reports show:
- Lines executed during tests
- Lines not covered
- Coverage percentage per file
- Missing line numbers

## Writing Tests

### Test Structure

```python
import pytest
from dockerfile_generator_v2 import PythonFileAnalyzer

class TestMyFeature:
    """Test suite for my feature."""
    
    def test_basic_functionality(self, tmp_path):
        """Test basic functionality."""
        # Arrange
        code = '''
def hello():
    return "world"
'''
        file_path = tmp_path / "test.py"
        file_path.write_text(code)
        
        # Act
        analyzer = PythonFileAnalyzer(str(file_path))
        result = analyzer.analyze()
        
        # Assert
        assert result is not None
```

### Using Fixtures

```python
def test_with_fixtures(sample_python_files, dockerfile_assertions):
    """Test using shared fixtures."""
    # Use pre-created sample files
    flask_app = sample_python_files['flask_app']
    
    # Use assertion helpers
    dockerfile_assertions.has_base_image(content)
```

### Parametrized Tests

```python
@pytest.mark.parametrize("version,feature", [
    ("3.10", "match cmd:"),
    ("3.8", "if (n := len(x)):"),
])
def test_version_features(tmp_path, version, feature):
    """Test multiple scenarios with same test logic."""
    # Test implementation
    pass
```

### Testing Exceptions

```python
def test_file_not_found():
    """Test error handling."""
    analyzer = PythonFileAnalyzer("/nonexistent/file.py")
    
    with pytest.raises(FileNotFoundError):
        analyzer.analyze()
```

## Test Examples

### Example 1: Testing Version Detection

```python
def test_detect_python310_match(tmp_path):
    """Test Python 3.10 match statement detection."""
    code = '''
def process(cmd):
    match cmd:
        case "start":
            return "starting"
'''
    file_path = tmp_path / "test.py"
    file_path.write_text(code)
    
    detector = PythonVersionDetector(str(file_path))
    version, method = detector.detect_version()
    
    assert version == "3.10"
```

### Example 2: Testing Dockerfile Generation

```python
def test_generate_flask_dockerfile():
    """Test Flask Dockerfile generation."""
    metadata = {
        'imports': {'flask'},
        'requirements': ['flask==3.0.0'],
        'python_version': '3.11',
        'app_type': 'flask',
        'is_executable': True,
        'filename': 'app.py'
    }
    
    generator = DockerfileGenerator(metadata)
    dockerfile = generator.generate()
    
    assert "FROM python:3.11-slim" in dockerfile
    assert "EXPOSE 5000" in dockerfile
```

### Example 3: Integration Test

```python
def test_complete_workflow(tmp_path):
    """Test complete workflow from code to Dockerfile."""
    # Create Python file
    code = '''
from flask import Flask
app = Flask(__name__)

if __name__ == '__main__':
    app.run()
'''
    file_path = tmp_path / "app.py"
    file_path.write_text(code)
    
    # Generate Dockerfile
    dockerfile_path = tmp_path / "Dockerfile"
    content = generate_dockerfile(str(file_path), str(dockerfile_path))
    
    # Verify
    assert dockerfile_path.exists()
    assert "flask" in content
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install pytest pytest-cov vermin
    
    - name: Run tests
      run: |
        pytest --cov=dockerfile_generator_v2 --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### GitLab CI Example

```yaml
test:
  image: python:3.11
  script:
    - pip install pytest pytest-cov vermin
    - pytest --cov=dockerfile_generator_v2 --cov-report=term
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

## Best Practices

### 1. Test Naming

- Use descriptive test names: `test_detect_python310_match_statement`
- Follow pattern: `test_<what>_<condition>_<expected_result>`

### 2. Test Independence

- Each test should be independent
- Use fixtures for setup/teardown
- Don't rely on test execution order

### 3. Test Data

- Use `tmp_path` fixture for file operations
- Create minimal test data
- Use fixtures for reusable test data

### 4. Assertions

- One logical assertion per test (when possible)
- Use descriptive assertion messages
- Use helper assertion methods from fixtures

### 5. Performance

- Mark slow tests with `@pytest.mark.slow`
- Keep unit tests fast (<100ms)
- Use mocking for external dependencies

## Troubleshooting

### Common Issues

**Issue**: Tests fail with "ModuleNotFoundError"
```bash
# Solution: Ensure you're running from the correct directory
cd /path/to/dockerfile_generator
pytest
```

**Issue**: Import errors
```bash
# Solution: Add current directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:."
pytest
```

**Issue**: Coverage not showing
```bash
# Solution: Specify the correct module
pytest --cov=dockerfile_generator_v2 --cov-report=term
```

**Issue**: Tests hang or timeout
```bash
# Solution: Run with shorter timeout
pytest --timeout=10
```

## Advanced Testing

### Testing with Mocks

```python
from unittest.mock import patch, MagicMock

def test_with_mock():
    """Test using mocks."""
    with patch('dockerfile_generator_v2.subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        # Test code
```

### Testing Async Code

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async functions."""
    result = await some_async_function()
    assert result == expected
```

### Property-Based Testing

```python
from hypothesis import given, strategies as st

@given(st.text())
def test_property(input_text):
    """Property-based test."""
    # Test should pass for any input
    pass
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Best Practices](https://docs.pytest.org/en/latest/goodpractices.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://realpython.com/pytest-python-testing/)

## Contributing Tests

When contributing tests:

1. Follow existing test structure
2. Maintain or improve coverage
3. Add tests for new features
4. Include edge cases
5. Update this documentation if needed

## License

Same license as the main project.
