# Testing Quick Reference

## Quick Setup

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=dockerfile_generator_v2
```

## Common Commands

| Command | Description |
|---------|-------------|
| `pytest` | Run all tests |
| `pytest -v` | Verbose output |
| `pytest -vv` | Extra verbose |
| `pytest -x` | Stop on first failure |
| `pytest --lf` | Run last failed tests |
| `pytest --ff` | Run failed tests first |
| `pytest -k pattern` | Run tests matching pattern |
| `pytest -m marker` | Run tests with marker |
| `pytest --collect-only` | Show what tests would run |
| `pytest --markers` | Show available markers |

## Using Test Runner

```bash
# All tests with coverage
python run_tests.py all

# Only unit tests
python run_tests.py unit

# Only integration tests  
python run_tests.py integration

# Fast tests (no slow tests)
python run_tests.py fast

# Verbose output
python run_tests.py verbose

# HTML coverage report
python run_tests.py html

# Specific test
python run_tests.py specific test_dockerfile_generator.py::test_name

# Re-run failed
python run_tests.py failed
```

## Test Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"

# Tests requiring vermin
pytest -m requires_vermin
```

## Coverage Commands

```bash
# Basic coverage
pytest --cov=dockerfile_generator_v2

# With missing lines
pytest --cov=dockerfile_generator_v2 --cov-report=term-missing

# HTML report
pytest --cov=dockerfile_generator_v2 --cov-report=html
# Open: htmlcov/index.html

# XML report (for CI)
pytest --cov=dockerfile_generator_v2 --cov-report=xml
```

## Filtering Tests

```bash
# Run specific file
pytest test_dockerfile_generator.py

# Run specific class
pytest test_dockerfile_generator.py::TestPythonVersionDetector

# Run specific test
pytest test_dockerfile_generator.py::TestPythonVersionDetector::test_detect_python310_match_statement

# Run by pattern
pytest -k "version"
pytest -k "flask or django"
pytest -k "not integration"
```

## Useful Options

```bash
# Show print statements
pytest -s

# Stop after N failures
pytest --maxfail=2

# Run in parallel (requires pytest-xdist)
pytest -n auto

# Timeout for tests
pytest --timeout=10

# Show slowest tests
pytest --durations=10

# Generate JUnit XML
pytest --junit-xml=results.xml
```

## Debugging Tests

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger on error
pytest --pdb --pdbcls=IPython.terminal.debugger:Pdb

# Show local variables on failure
pytest -l

# Capture logging
pytest --log-cli-level=DEBUG
```

## Test Structure

```
test_dockerfile_generator.py
├── TestPythonVersionDetector   # Version detection tests
├── TestPythonFileAnalyzer      # File analysis tests
├── TestDockerfileGenerator     # Dockerfile generation tests
├── TestEndToEnd                # Integration tests
└── TestEdgeCases               # Edge case tests
```

## Fixtures Available

- `tmp_path` - Temporary directory for test files
- `sample_python_files` - Pre-created sample Python files
- `sample_requirements_files` - Pre-created requirements.txt files
- `dockerfile_assertions` - Helper assertions for Dockerfile validation

## Example Test

```python
def test_my_feature(tmp_path):
    """Test description."""
    # Arrange
    code = 'print("hello")'
    file_path = tmp_path / "test.py"
    file_path.write_text(code)
    
    # Act
    result = my_function(str(file_path))
    
    # Assert
    assert result == expected_value
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run tests
  run: pytest --cov=dockerfile_generator_v2 --cov-report=xml
```

### GitLab CI
```yaml
test:
  script:
    - pytest --cov=dockerfile_generator_v2
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| ModuleNotFoundError | Run from project root: `cd /path/to/project && pytest` |
| No coverage shown | Specify module: `--cov=dockerfile_generator_v2` |
| Tests not found | Check naming: `test_*.py` or `*_test.py` |
| Import errors | Add to path: `export PYTHONPATH=.` |
| Vermin not found | Install: `pip install vermin` |

## Best Practices

✅ **Do:**
- Write tests for new features
- Keep tests fast and independent
- Use descriptive test names
- One logical assertion per test
- Use fixtures for setup

❌ **Don't:**
- Rely on test execution order
- Share state between tests
- Test implementation details
- Ignore failing tests
- Skip error handling tests

## Resources

- Pytest docs: https://docs.pytest.org/
- Coverage docs: https://coverage.readthedocs.io/
- Testing guide: ./TESTING.md
