# Testing Guide for Dockerfile Database System

Complete testing documentation for both the database manager and REST API.

## Table of Contents

1. [Setup](#setup)
2. [Running Tests](#running-tests)
3. [Test Structure](#test-structure)
4. [Test Coverage](#test-coverage)
5. [Writing Tests](#writing-tests)
6. [CI/CD Integration](#cicd-integration)

## Setup

### Install Testing Dependencies

```bash
# Install core testing dependencies
pip install pytest pytest-cov

# Install API testing dependencies
pip install httpx pytest-asyncio

# Install all requirements
pip install -r requirements-database.txt
```

### Verify Installation

```bash
pytest --version
python -m pytest --version
```

## Running Tests

### Quick Start

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=dockerfile_database --cov=dockerfile_api
```

### Using the Test Runner

```bash
# All tests with coverage
python run_database_tests.py all

# Database tests only
python run_database_tests.py database

# API tests only
python run_database_tests.py api

# Unit tests only
python run_database_tests.py unit

# Integration tests only
python run_database_tests.py integration

# Fast tests (no slow tests)
python run_database_tests.py fast

# Verbose output
python run_database_tests.py verbose

# HTML coverage report
python run_database_tests.py coverage

# Specific test
python run_database_tests.py specific test_dockerfile_api.py::TestCreateDockerfile

# Re-run failed tests
python run_database_tests.py failed
```

### Test Selection

```bash
# Run specific test file
pytest test_dockerfile_database.py

# Run specific test class
pytest test_dockerfile_api.py::TestCreateDockerfile

# Run specific test function
pytest test_dockerfile_database.py::TestDockerfileDatabase::test_add_dockerfile_basic

# Run tests matching pattern
pytest -k "create"
pytest -k "database or api"

# Run tests with marker
pytest -m unit
pytest -m api
pytest -m "not slow"
```

## Test Structure

### Test Files

```
.
├── test_dockerfile_database.py    # Database manager tests
├── test_dockerfile_api.py          # FastAPI endpoint tests
├── conftest_database.py            # Shared fixtures
├── pytest_database.ini             # Pytest configuration
└── run_database_tests.py           # Test runner script
```

### Test Classes

#### test_dockerfile_database.py

1. **TestDockerfileDatabase** (20+ tests)
   - Database initialization
   - Adding Dockerfiles
   - Retrieving by date
   - Retrieving by date and name
   - Statistics
   - Deletion
   - Context manager usage

2. **TestDockerfileContent** (4 tests)
   - Empty Dockerfiles
   - Large Dockerfiles
   - Unicode content
   - Special characters in names

3. **TestDatabaseIndexes** (1 test)
   - Index creation verification

4. **TestDatabaseIntegration** (2 tests)
   - Complete workflows
   - Batch operations

#### test_dockerfile_api.py

1. **TestRootEndpoint** (1 test)
   - API information

2. **TestHealthCheck** (1 test)
   - Health check endpoint

3. **TestStatistics** (2 tests)
   - Empty database stats
   - Populated database stats

4. **TestGetAllDockerfiles** (2 tests)
   - Empty database
   - Populated database

5. **TestGetUniqueDates** (2 tests)
   - Empty database
   - Populated database

6. **TestGetDockerfilesByDate** (4 tests)
   - Valid date retrieval
   - Empty date
   - Invalid date format
   - Various date formats

7. **TestGetDockerfileNamesByDate** (2 tests)
   - Names retrieval
   - Empty date

8. **TestGetSpecificDockerfile** (3 tests)
   - Successful retrieval
   - Not found
   - Special characters in name

9. **TestGetDockerfileContent** (2 tests)
   - Plain text content
   - Not found

10. **TestCreateDockerfile** (5 tests)
    - Successful creation
    - Duplicate handling
    - Invalid data
    - Empty name
    - Empty content

11. **TestDeleteDockerfile** (2 tests)
    - Successful deletion
    - Not found

12. **TestAPIIntegration** (2 tests)
    - Complete CRUD workflow
    - Batch operations

13. **TestErrorHandling** (2 tests)
    - 404 errors
    - Method not allowed

14. **TestContentTypes** (2 tests)
    - JSON responses
    - Plain text responses

### Test Markers

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Slower, end-to-end tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.database` - Database operation tests
- `@pytest.mark.slow` - Slow-running tests

## Test Coverage

### Current Coverage

The test suite aims for >85% code coverage:

**Database Manager (dockerfile_database.py)**
- ✅ Initialization and table creation
- ✅ Adding Dockerfiles (from string and file)
- ✅ Retrieving by date
- ✅ Retrieving by date and name
- ✅ Getting all Dockerfiles
- ✅ Getting unique dates
- ✅ Getting statistics
- ✅ Deleting Dockerfiles
- ✅ Context manager usage
- ✅ Error handling

**FastAPI Interface (dockerfile_api.py)**
- ✅ All GET endpoints
- ✅ POST endpoint (create)
- ✅ DELETE endpoint
- ✅ Error responses (400, 404, 409, 500)
- ✅ Request validation
- ✅ Response formatting
- ✅ Content type handling

### Viewing Coverage

```bash
# Terminal report
pytest --cov=dockerfile_database --cov=dockerfile_api --cov-report=term-missing

# HTML report
pytest --cov=dockerfile_database --cov=dockerfile_api --cov-report=html
# Open htmlcov/index.html

# XML report (for CI)
pytest --cov=dockerfile_database --cov=dockerfile_api --cov-report=xml
```

## Writing Tests

### Test Structure (AAA Pattern)

```python
def test_feature(temp_db):
    """Test description."""
    # Arrange
    name = "Dockerfile.test"
    content = "FROM python:3.11"
    
    # Act
    result = temp_db.add_dockerfile(name, content)
    
    # Assert
    assert result['name'] == name
```

### Using Fixtures

```python
def test_with_fixtures(temp_db, sample_dockerfiles):
    """Test using shared fixtures."""
    # temp_db provides a clean database
    # sample_dockerfiles provides sample content
    
    temp_db.add_dockerfile("Dockerfile.flask", sample_dockerfiles['flask'])
    
    dockerfiles = temp_db.get_all_dockerfiles()
    assert len(dockerfiles) > 0
```

### API Testing

```python
def test_api_endpoint(client, test_db):
    """Test API endpoint."""
    # client is TestClient from FastAPI
    # test_db is a temporary database
    
    response = client.get("/dockerfiles")
    
    assert response.status_code == 200
    data = response.json()
    assert "dockerfiles" in data
```

### Parametrized Tests

```python
@pytest.mark.parametrize("name,content", [
    ("Dockerfile.1", "FROM python:3.11"),
    ("Dockerfile.2", "FROM python:3.10"),
])
def test_multiple_dockerfiles(temp_db, name, content):
    """Test with multiple parameter sets."""
    result = temp_db.add_dockerfile(name, content)
    assert result['name'] == name
```

## Available Fixtures

### Database Fixtures

- `temp_db` - Clean temporary database
- `temp_db_path` - Database path without initialization
- `populated_test_db` - Database with sample data
- `sample_dockerfiles` - Dictionary of sample Dockerfile contents
- `sample_dockerfile_files` - Sample Dockerfile files on disk

### API Fixtures

- `client` - FastAPI TestClient
- `test_db` - Temporary database for API tests
- `sample_dockerfile` - Sample Dockerfile request data
- `populated_db` - Populated database with today's date

### Helper Fixtures

- `get_today` - Get today's date in ISO format
- `dockerfile_validator` - Helper class for validating data
- `api_test_helpers` - Helper class for API testing

## Example Tests

### Example 1: Database Test

```python
def test_add_and_retrieve(temp_db):
    """Test adding and retrieving a Dockerfile."""
    # Add
    result = temp_db.add_dockerfile(
        "Dockerfile.test",
        "FROM python:3.11\nWORKDIR /app"
    )
    
    # Retrieve
    dockerfile = temp_db.get_dockerfile_by_date_and_name(
        result['created_date'],
        result['name']
    )
    
    assert dockerfile is not None
    assert dockerfile['name'] == "Dockerfile.test"
```

### Example 2: API Test

```python
def test_create_via_api(client, test_db):
    """Test creating Dockerfile via API."""
    data = {
        "name": "Dockerfile.api",
        "content": "FROM python:3.11"
    }
    
    response = client.post("/dockerfiles", json=data)
    
    assert response.status_code == 201
    result = response.json()
    assert result['name'] == data['name']
```

### Example 3: Integration Test

```python
def test_full_workflow(client, test_db):
    """Test complete workflow."""
    # Create
    create_response = client.post(
        "/dockerfiles",
        json={"name": "Dockerfile.test", "content": "FROM python:3.11"}
    )
    created = create_response.json()
    
    # Read
    get_response = client.get(
        f"/dockerfiles/by-date/{created['created_date']}/{created['name']}"
    )
    assert get_response.status_code == 200
    
    # Delete
    delete_response = client.delete(f"/dockerfiles/{created['id']}")
    assert delete_response.status_code == 200
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Database Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-database.txt
        pip install pytest pytest-cov httpx
    
    - name: Run tests
      run: |
        pytest --cov=dockerfile_database --cov=dockerfile_api --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### GitLab CI

```yaml
test:
  image: python:3.11
  script:
    - pip install -r requirements-database.txt
    - pip install pytest pytest-cov httpx
    - pytest --cov=dockerfile_database --cov=dockerfile_api
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

## Performance Benchmarks

### Test Execution Times

- Unit tests (database): ~5 seconds
- Unit tests (API): ~8 seconds
- Integration tests: ~3 seconds
- Full suite: ~15-20 seconds

### Optimization Tips

1. Use `pytest-xdist` for parallel execution
2. Mark slow tests with `@pytest.mark.slow`
3. Use fixtures appropriately (function vs session scope)
4. Clean up resources after tests

## Troubleshooting

### Common Issues

**Issue**: Tests fail with "Database is locked"
```
Solution: Ensure all database connections are closed
Use context managers or call db.close()
```

**Issue**: API tests fail with connection errors
```
Solution: Ensure test_db fixture is properly initialized
Check that the database instance is correctly overridden
```

**Issue**: Coverage not showing
```
Solution: Specify modules correctly
pytest --cov=dockerfile_database --cov=dockerfile_api
```

**Issue**: Tests pass locally but fail in CI
```
Solution: Check Python version compatibility
Ensure all dependencies are installed
Check for timezone issues (use UTC in tests)
```

## Best Practices

### 1. Test Independence

Each test should be independent:
```python
# Good
def test_feature(temp_db):
    db = temp_db  # Fresh database each time
    # test code

# Bad
db = DockerfileDatabase("shared.db")  # Shared state!
```

### 2. Descriptive Names

```python
# Good
def test_add_dockerfile_returns_created_metadata(temp_db):
    ...

# Bad
def test_1(temp_db):
    ...
```

### 3. Use Fixtures

```python
# Good
def test_feature(temp_db, sample_dockerfiles):
    ...

# Bad
def test_feature():
    db = DockerfileDatabase("test.db")  # Manual setup
    # test code
    db.close()  # Manual cleanup
```

### 4. Test Edge Cases

```python
def test_empty_dockerfile(temp_db):
    result = temp_db.add_dockerfile("Dockerfile.empty", "")
    assert result is not None

def test_large_dockerfile(temp_db):
    content = "RUN echo 'test'\n" * 1000
    result = temp_db.add_dockerfile("Dockerfile.large", content)
    assert result is not None
```

## Test Metrics

- **Total Tests**: 60+ tests
- **Coverage Target**: >85%
- **Execution Time**: ~15-20 seconds
- **Success Rate**: 100%

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Coverage.py](https://coverage.readthedocs.io/)

## Contributing

When adding tests:

1. Follow existing test structure
2. Use appropriate fixtures
3. Add parametrized tests for variations
4. Maintain or improve coverage
5. Update documentation
