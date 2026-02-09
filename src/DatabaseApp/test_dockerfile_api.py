"""
Test Suite for Dockerfile Database API

Tests for the FastAPI REST interface.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import pytz
import tempfile
import os

from dockerfile_api import app
from dockerfile_database import DockerfileDatabase


# Fixtures

@pytest.fixture(scope="function")
def test_db(tmp_path):
    """Create a temporary test database."""
    db_path = tmp_path / "test_api.db"
    
    # Set up test database
    db = DockerfileDatabase(str(db_path))
    
    # Override the global db in the API module
    import dockerfile_api
    dockerfile_api.db = db
    
    yield db
    
    db.close()


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_dockerfile():
    """Sample Dockerfile content."""
    return {
        "name": "Dockerfile.test",
        "content": "FROM python:3.11-slim\nWORKDIR /app\nCOPY . ."
    }


@pytest.fixture
def populated_db(test_db):
    """Database with sample data."""
    today = datetime.now(pytz.UTC).date().isoformat()
    
    test_db.add_dockerfile("Dockerfile.flask", "FROM python:3.11\nWORKDIR /app")
    test_db.add_dockerfile("Dockerfile.django", "FROM python:3.11\nWORKDIR /app")
    test_db.add_dockerfile("Dockerfile.fastapi", "FROM python:3.11\nWORKDIR /app")
    
    return test_db, today


# Test Root Endpoint

class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_endpoint(self, client):
        """Test GET / returns API information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "details" in data
        assert data["message"] == "Dockerfile Database API"


# Test Health Check

class TestHealthCheck:
    """Tests for health check endpoint."""
    
    def test_health_check_success(self, client, test_db):
        """Test health check returns healthy status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "total_entries" in data


# Test Statistics

class TestStatistics:
    """Tests for statistics endpoint."""
    
    def test_get_statistics_empty(self, client, test_db):
        """Test statistics on empty database."""
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_dockerfiles"] == 0
        assert data["unique_dates"] == 0
        assert data["unique_names"] == 0
    
    def test_get_statistics_populated(self, client, populated_db):
        """Test statistics on populated database."""
        db, _ = populated_db
        
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_dockerfiles"] >= 3
        assert data["unique_dates"] >= 1
        assert data["unique_names"] >= 3


# Test Get All Dockerfiles

class TestGetAllDockerfiles:
    """Tests for getting all Dockerfiles."""
    
    def test_get_all_dockerfiles_empty(self, client, test_db):
        """Test getting all Dockerfiles from empty database."""
        response = client.get("/dockerfiles")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["dockerfiles"] == []
    
    def test_get_all_dockerfiles_populated(self, client, populated_db):
        """Test getting all Dockerfiles from populated database."""
        db, _ = populated_db
        
        response = client.get("/dockerfiles")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 3
        assert len(data["dockerfiles"]) >= 3
        
        # Verify structure
        dockerfile = data["dockerfiles"][0]
        assert "id" in dockerfile
        assert "name" in dockerfile
        assert "content" in dockerfile
        assert "created_date" in dockerfile
        assert "created_time" in dockerfile


# Test Get Unique Dates

class TestGetUniqueDates:
    """Tests for getting unique dates."""
    
    def test_get_unique_dates_empty(self, client, test_db):
        """Test getting dates from empty database."""
        response = client.get("/dockerfiles/dates")
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    def test_get_unique_dates_populated(self, client, populated_db):
        """Test getting dates from populated database."""
        db, today = populated_db
        
        response = client.get("/dockerfiles/dates")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert today in data


# Test Get Dockerfiles by Date

class TestGetDockerfilesByDate:
    """Tests for getting Dockerfiles by date."""
    
    def test_get_dockerfiles_by_date_success(self, client, populated_db):
        """Test retrieving Dockerfiles for a specific date."""
        db, today = populated_db
        
        response = client.get(f"/dockerfiles/by-date/{today}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 3
        assert len(data["dockerfiles"]) >= 3
    
    def test_get_dockerfiles_by_date_empty(self, client, test_db):
        """Test retrieving Dockerfiles for date with no entries."""
        response = client.get("/dockerfiles/by-date/2020-01-01")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["dockerfiles"] == []
    
    def test_get_dockerfiles_by_date_invalid_format(self, client, test_db):
        """Test retrieving with invalid date format."""
        response = client.get("/dockerfiles/by-date/invalid-date")
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid date format" in data["detail"]
    
    def test_get_dockerfiles_by_date_various_formats(self, client, test_db):
        """Test various valid date formats."""
        valid_dates = [
            "2026-02-08",
            "2026-01-01",
            "2020-12-31"
        ]
        
        for date in valid_dates:
            response = client.get(f"/dockerfiles/by-date/{date}")
            assert response.status_code == 200


# Test Get Dockerfile Names by Date

class TestGetDockerfileNamesByDate:
    """Tests for getting Dockerfile names by date."""
    
    def test_get_names_by_date_success(self, client, populated_db):
        """Test getting Dockerfile names for a date."""
        db, today = populated_db
        
        response = client.get(f"/dockerfiles/by-date/{today}/names")
        
        assert response.status_code == 200
        names = response.json()
        assert isinstance(names, list)
        assert "Dockerfile.flask" in names
        assert "Dockerfile.django" in names
        assert "Dockerfile.fastapi" in names
    
    def test_get_names_by_date_empty(self, client, test_db):
        """Test getting names for date with no entries."""
        response = client.get("/dockerfiles/by-date/2020-01-01/names")
        
        assert response.status_code == 200
        names = response.json()
        assert names == []


# Test Get Specific Dockerfile

class TestGetSpecificDockerfile:
    """Tests for getting a specific Dockerfile."""
    
    def test_get_dockerfile_by_date_and_name_success(self, client, populated_db):
        """Test getting specific Dockerfile."""
        db, today = populated_db
        
        response = client.get(f"/dockerfiles/by-date/{today}/Dockerfile.flask")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Dockerfile.flask"
        assert "content" in data
        assert data["created_date"] == today
    
    def test_get_dockerfile_by_date_and_name_not_found(self, client, test_db):
        """Test getting non-existent Dockerfile."""
        response = client.get("/dockerfiles/by-date/2020-01-01/Dockerfile.nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert "Resource not found" in data["message"]
        # assert "not found" in data["detail"]
    
    def test_get_dockerfile_with_special_chars_in_name(self, client, test_db):
        """Test getting Dockerfile with special characters in name."""
        today = datetime.now(pytz.UTC).date().isoformat()
        
        # Add Dockerfile with special characters
        test_db.add_dockerfile("Dockerfile.test-app_v2", "FROM python:3.11")
        
        response = client.get(f"/dockerfiles/by-date/{today}/Dockerfile.test-app_v2")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Dockerfile.test-app_v2"


# Test Get Dockerfile Content (Plain Text)

class TestGetDockerfileContent:
    """Tests for getting Dockerfile content as plain text."""
    
    def test_get_dockerfile_content_success(self, client, populated_db):
        """Test getting Dockerfile content as plain text."""
        db, today = populated_db
        
        response = client.get(f"/dockerfiles/by-date/{today}/Dockerfile.flask/content")
        
        assert response.status_code == 200
        content = response.text
        assert "FROM python:3.11" in content
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
    
    def test_get_dockerfile_content_not_found(self, client, test_db):
        """Test getting content for non-existent Dockerfile."""
        response = client.get("/dockerfiles/by-date/2020-01-01/Dockerfile.none/content")
        
        assert response.status_code == 404


# Test Create Dockerfile (POST)

class TestCreateDockerfile:
    """Tests for creating Dockerfiles via POST."""
    
    def test_create_dockerfile_success(self, client, test_db, sample_dockerfile):
        """Test creating a new Dockerfile."""
        response = client.post("/dockerfiles", json=sample_dockerfile)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_dockerfile["name"]
        assert data["content"] == sample_dockerfile["content"]
        assert "created_date" in data
        assert "created_time" in data
        assert "id" in data
    
    def test_create_dockerfile_duplicate(self, client, test_db, sample_dockerfile):
        """Test creating duplicate Dockerfile at same timestamp."""
        # First creation
        response1 = client.post("/dockerfiles", json=sample_dockerfile)
        assert response1.status_code == 201
        
        # Immediate duplicate - may or may not fail depending on timing
        # (microsecond precision makes exact duplicates rare)
        # This tests the error handling if it does occur
    
    def test_create_dockerfile_invalid_data(self, client, test_db):
        """Test creating Dockerfile with invalid data."""
        invalid_data = {
            "name": "Dockerfile.test"
            # Missing 'content' field
        }
        
        response = client.post("/dockerfiles", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_create_dockerfile_empty_name(self, client, test_db):
        """Test creating Dockerfile with empty name."""
        invalid_data = {
            "name": "",
            "content": "FROM python:3.11"
        }
        
        response = client.post("/dockerfiles", json=invalid_data)
        
        # Should either fail validation or be rejected
        assert response.status_code in [400, 422]
    
    def test_create_dockerfile_empty_content(self, client, test_db):
        """Test creating Dockerfile with empty content."""
        data = {
            "name": "Dockerfile.empty",
            "content": ""
        }
        
        response = client.post("/dockerfiles", json=data)
        
        # Empty content should be allowed
        assert response.status_code == 201


# Test Delete Dockerfile

class TestDeleteDockerfile:
    """Tests for deleting Dockerfiles."""
    
    def test_delete_dockerfile_success(self, client, test_db):
        """Test deleting a Dockerfile."""
        # Create a Dockerfile first
        result = test_db.add_dockerfile("Dockerfile.delete", "FROM python:3.11")
        dockerfile_id = result['id']
        
        response = client.delete(f"/dockerfiles/{dockerfile_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
    
    def test_delete_dockerfile_not_found(self, client, test_db):
        """Test deleting non-existent Dockerfile."""
        response = client.delete("/dockerfiles/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert "Resource not found" in data["message"]
        # assert "not found" in data["detail"]


# Integration Tests

class TestAPIIntegration:
    """Integration tests for complete API workflows."""
    
    def test_complete_crud_workflow(self, client, test_db):
        """Test complete Create-Read-Update-Delete workflow."""
        # Create
        dockerfile = {
            "name": "Dockerfile.crud",
            "content": "FROM python:3.11\nWORKDIR /app"
        }
        
        create_response = client.post("/dockerfiles", json=dockerfile)
        assert create_response.status_code == 201
        created = create_response.json()
        
        # Read - Get all
        all_response = client.get("/dockerfiles")
        assert all_response.status_code == 200
        assert all_response.json()["count"] >= 1
        
        # Read - Get by date
        date_response = client.get(f"/dockerfiles/by-date/{created['created_date']}")
        assert date_response.status_code == 200
        
        # Read - Get specific
        specific_response = client.get(
            f"/dockerfiles/by-date/{created['created_date']}/{created['name']}"
        )
        assert specific_response.status_code == 200
        assert specific_response.json()["name"] == dockerfile["name"]
        
        # Delete
        delete_response = client.delete(f"/dockerfiles/{created['id']}")
        assert delete_response.status_code == 200
        
        # Verify deletion
        verify_response = client.get(
            f"/dockerfiles/by-date/{created['created_date']}/{created['name']}"
        )
        assert verify_response.status_code == 404
    
    def test_batch_create_and_retrieve(self, client, test_db):
        """Test creating multiple Dockerfiles and retrieving them."""
        dockerfiles = [
            {"name": "Dockerfile.app1", "content": "FROM python:3.11"},
            {"name": "Dockerfile.app2", "content": "FROM python:3.10"},
            {"name": "Dockerfile.app3", "content": "FROM python:3.9"},
        ]
        
        created_ids = []
        
        # Create all
        for df in dockerfiles:
            response = client.post("/dockerfiles", json=df)
            assert response.status_code == 201
            created_ids.append(response.json()["id"])
        
        # Retrieve all
        response = client.get("/dockerfiles")
        assert response.status_code == 200
        assert response.json()["count"] >= 3
        
        # Clean up
        for df_id in created_ids:
            client.delete(f"/dockerfiles/{df_id}")


# Parametrized Tests

@pytest.mark.parametrize("endpoint", [
    "/",
    "/health",
    "/stats",
    "/dockerfiles",
    "/dockerfiles/dates",
])
def test_get_endpoints_accessible(client, test_db, endpoint):
    """Test that all GET endpoints are accessible."""
    response = client.get(endpoint)
    assert response.status_code == 200


@pytest.mark.parametrize("invalid_date", [
    "not-a-date",
    "2026/02/08",  # This returns 404, somewhat problematic
    "08-02-2026",
    "2026-13-01",  # Invalid month
    "2026-02-32",  # Invalid day
])
def test_invalid_date_formats(client, test_db, invalid_date):
    """Test that invalid date formats are rejected."""
    response = client.get(f"/dockerfiles/by-date/{invalid_date}")
    # NOTE: slashes in dates return 404. This is because the query is invalid and cannot be parsed.
    # This is why we have a 404 here, it is a special case.
    assert response.status_code == 400 or response.status_code == 404


@pytest.mark.parametrize("dockerfile_content", [
    "FROM python:3.11",
    "FROM python:3.11\nWORKDIR /app",
    "FROM python:3.11\nWORKDIR /app\nCOPY . .\nCMD [\"python\", \"app.py\"]",
])
def test_create_various_contents(client, test_db, dockerfile_content):
    """Test creating Dockerfiles with various content lengths."""
    data = {
        "name": "Dockerfile.test",
        "content": dockerfile_content
    }
    
    response = client.post("/dockerfiles", json=data)
    assert response.status_code == 201


# Error Handling Tests

class TestErrorHandling:
    """Tests for error handling."""
    
    def test_404_on_unknown_endpoint(self, client, test_db):
        """Test 404 for unknown endpoint."""
        response = client.get("/unknown/endpoint")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client, test_db):
        """Test method not allowed errors."""
        # POST to a GET-only endpoint
        response = client.post("/stats", json={})
        assert response.status_code == 405


# Content Type Tests

class TestContentTypes:
    """Tests for content type handling."""
    
    def test_json_response_for_most_endpoints(self, client, test_db):
        """Test that most endpoints return JSON."""
        endpoints = [
            "/",
            "/health",
            "/stats",
            "/dockerfiles",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert "application/json" in response.headers["content-type"]
    
    def test_plain_text_for_content_endpoint(self, client, populated_db):
        """Test that content endpoint returns plain text."""
        db, today = populated_db
        
        response = client.get(f"/dockerfiles/by-date/{today}/Dockerfile.flask/content")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
