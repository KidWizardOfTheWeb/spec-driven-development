"""
Pytest configuration and shared fixtures for Dockerfile Database tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytz

from dockerfile_database import DockerfileDatabase


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    """Create a session-scoped temporary directory for test data."""
    return tmp_path_factory.mktemp("db_test_data")


@pytest.fixture(scope="function")
def temp_db(tmp_path):
    """Provide a clean temporary database for each test."""
    db_path = tmp_path / "test.db"
    db = DockerfileDatabase(str(db_path))
    yield db
    db.close()


@pytest.fixture(scope="function")
def temp_db_path(tmp_path):
    """Provide a temporary database path without initializing."""
    return tmp_path / "test.db"


@pytest.fixture
def sample_dockerfiles():
    """Provide a set of sample Dockerfile contents."""
    return {
        'flask': """FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]""",
        
        'django': """FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]""",
        
        'fastapi': """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]""",
        
        'minimal': "FROM python:3.11",
        
        'complex': """# Multi-stage build
FROM python:3.11 AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "app.py"]"""
    }


@pytest.fixture
def sample_dockerfile_files(tmp_path, sample_dockerfiles):
    """Create sample Dockerfile files on disk."""
    files = {}
    
    for name, content in sample_dockerfiles.items():
        filepath = tmp_path / f"Dockerfile.{name}"
        filepath.write_text(content)
        files[name] = filepath
    
    return files


@pytest.fixture
def populated_test_db(temp_db, sample_dockerfiles):
    """Provide a database populated with sample Dockerfiles."""
    for name, content in sample_dockerfiles.items():
        temp_db.add_dockerfile(f"Dockerfile.{name}", content)
    
    return temp_db


@pytest.fixture
def get_today():
    """Get today's date in ISO format."""
    return datetime.now(pytz.UTC).date().isoformat()


@pytest.fixture
def dockerfile_validator():
    """Provide helper functions for validating Dockerfile data."""
    class DockerfileValidator:
        @staticmethod
        def validate_structure(data):
            """Validate Dockerfile data structure."""
            required_fields = [
                'id', 'name', 'content', 'created_date',
                'created_time', 'created_timestamp', 'timezone'
            ]
            return all(field in data for field in required_fields)
        
        @staticmethod
        def validate_date_format(date_str):
            """Validate date is in ISO format (YYYY-MM-DD)."""
            try:
                datetime.fromisoformat(date_str)
                return True
            except ValueError:
                return False
        
        @staticmethod
        def validate_content(expected, actual):
            """Validate Dockerfile content matches."""
            return expected.strip() == actual.strip()
    
    return DockerfileValidator()


@pytest.fixture
def api_test_helpers():
    """Provide helper functions for API testing."""
    class APITestHelpers:
        @staticmethod
        def assert_successful_response(response, expected_status=200):
            """Assert response is successful."""
            assert response.status_code == expected_status
            return response.json()
        
        @staticmethod
        def assert_error_response(response, expected_status=400):
            """Assert response is an error."""
            assert response.status_code == expected_status
            data = response.json()
            assert 'detail' in data
            return data
        
        @staticmethod
        def create_dockerfile_data(name, content):
            """Create valid Dockerfile request data."""
            return {
                "name": name,
                "content": content
            }
    
    return APITestHelpers()


@pytest.fixture(autouse=True)
def reset_test_state():
    """Reset any test state between tests."""
    # This runs before each test
    yield
    # Cleanup after each test (if needed)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )
    config.addinivalue_line(
        "markers", "database: mark test as a database test"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Mark API tests
        if "test_dockerfile_api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        
        # Mark database tests
        if "test_dockerfile_database" in item.nodeid:
            item.add_marker(pytest.mark.database)
        
        # Mark integration tests
        if "Integration" in item.nodeid or "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)


# Helper functions for tests

def create_test_dockerfile(path: Path, content: str) -> Path:
    """Helper to create a test Dockerfile."""
    path.write_text(content)
    return path


def verify_dockerfile_in_db(db: DockerfileDatabase, name: str, date: str) -> bool:
    """Helper to verify a Dockerfile exists in database."""
    result = db.get_dockerfile_by_date_and_name(date, name)
    return result is not None
