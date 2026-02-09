"""
Test Suite for Dockerfile Database System

Comprehensive tests for both the database manager and FastAPI interface.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
import pytz

from dockerfile_database import DockerfileDatabase


class TestDockerfileDatabase:
    """Test suite for DockerfileDatabase class."""
    
    def test_database_initialization(self, tmp_path):
        """Test database initialization and table creation."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        # Verify database file was created
        assert db_path.exists()
        
        # Verify tables exist
        db.cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='dockerfiles'
        """)
        result = db.cursor.fetchone()
        assert result is not None
        
        db.close()
    
    def test_add_dockerfile_basic(self, tmp_path):
        """Test adding a basic Dockerfile."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        name = "Dockerfile.test"
        content = "FROM python:3.11\nWORKDIR /app"
        
        result = db.add_dockerfile(name, content)
        
        # Verify return values
        assert result['name'] == name
        assert 'created_date' in result
        assert 'created_time' in result
        assert 'created_timestamp' in result
        assert result['timezone'] == str(db.TIMEZONE)
        
        db.close()
    
    def test_add_dockerfile_from_file(self, tmp_path):
        """Test adding a Dockerfile from a file."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        # Create a sample Dockerfile
        dockerfile = tmp_path / "Dockerfile.sample"
        content = "FROM python:3.11\nWORKDIR /app\nCOPY . ."
        dockerfile.write_text(content)
        
        result = db.add_dockerfile_from_file(str(dockerfile))
        
        assert result['name'] == "Dockerfile.sample"
        
        # Verify it's in the database
        retrieved = db.get_dockerfile_by_date_and_name(
            result['created_date'],
            result['name']
        )
        assert retrieved is not None
        assert retrieved['content'] == content
        
        db.close()
    
    def test_add_dockerfile_file_not_found(self, tmp_path):
        """Test adding a Dockerfile from non-existent file."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        with pytest.raises(FileNotFoundError):
            db.add_dockerfile_from_file("nonexistent.dockerfile")
        
        db.close()

    # For our purposes, this test does not work well.
    # It is because we can technically have dupe uploads of items and be ok with it.
    # Since we don't store users who uploaded the data (in this version), we care about when the files were uploaded.
    # The contents of the upload can be the same, we just want all records straight.
    # Test removed temporarily, no way to check duplicates due to microseconds being different.

    # def test_duplicate_dockerfile_prevention(self, tmp_path):
    #     """Test that duplicate Dockerfiles are prevented."""
    #     db_path = tmp_path / "test.db"
    #     db = DockerfileDatabase(str(db_path))
    #
    #     name = "Dockerfile.test"
    #     content = "FROM python:3.11"
    #
    #     # Add first time - should succeed
    #     db.add_dockerfile(name, content)
    #
    #     # Try to add again immediately - should fail
    #     # (same name, same timestamp down to microseconds is unlikely but possible)
    #     # We'll test by manually inserting duplicate
    #     with pytest.raises(sqlite3.IntegrityError):
    #         db.cursor.execute('''
    #             INSERT INTO dockerfiles
    #             (name, content, created_date, created_time, created_timestamp, timezone)
    #             VALUES (?, ?, ?, ?, ?, ?)
    #         ''', (name, content, "2026-02-08", "12:00:00", "2026-02-08T12:00:00", "UTC"))
    #         db.conn.commit()
    #
    #     db.close()
    
    def test_get_dockerfiles_by_date(self, tmp_path):
        """Test retrieving Dockerfiles by date."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        # Add multiple Dockerfiles
        today = datetime.now(db.TIMEZONE).date().isoformat()
        
        db.add_dockerfile("Dockerfile.flask", "FROM python:3.11")
        db.add_dockerfile("Dockerfile.django", "FROM python:3.11")
        
        # Retrieve by date
        dockerfiles = db.get_dockerfiles_by_date(today)
        
        assert len(dockerfiles) >= 2
        names = [df['name'] for df in dockerfiles]
        assert "Dockerfile.flask" in names
        assert "Dockerfile.django" in names
        
        db.close()
    
    def test_get_dockerfiles_by_date_empty(self, tmp_path):
        """Test retrieving Dockerfiles for a date with no entries."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        # Query for a date with no Dockerfiles
        dockerfiles = db.get_dockerfiles_by_date("2020-01-01")
        
        assert dockerfiles == []
        
        db.close()
    
    def test_get_dockerfile_by_date_and_name(self, tmp_path):
        """Test retrieving a specific Dockerfile by date and name."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        name = "Dockerfile.specific"
        content = "FROM python:3.11\nWORKDIR /app"
        
        result = db.add_dockerfile(name, content)
        date = result['created_date']
        
        # Retrieve it
        dockerfile = db.get_dockerfile_by_date_and_name(date, name)
        
        assert dockerfile is not None
        assert dockerfile['name'] == name
        assert dockerfile['content'] == content
        assert dockerfile['created_date'] == date
        
        db.close()
    
    def test_get_dockerfile_by_date_and_name_not_found(self, tmp_path):
        """Test retrieving non-existent Dockerfile."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        dockerfile = db.get_dockerfile_by_date_and_name(
            "2020-01-01",
            "Dockerfile.nonexistent"
        )
        
        assert dockerfile is None
        
        db.close()
    
    def test_get_all_dockerfiles(self, tmp_path):
        """Test retrieving all Dockerfiles."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        # Add multiple Dockerfiles
        db.add_dockerfile("Dockerfile.1", "FROM python:3.11")
        db.add_dockerfile("Dockerfile.2", "FROM python:3.10")
        db.add_dockerfile("Dockerfile.3", "FROM python:3.9")
        
        all_dockerfiles = db.get_all_dockerfiles()
        
        assert len(all_dockerfiles) >= 3
        
        db.close()
    
    def test_get_unique_dates(self, tmp_path):
        """Test retrieving unique dates."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        # Add Dockerfiles
        db.add_dockerfile("Dockerfile.test", "FROM python:3.11")
        
        dates = db.get_unique_dates()
        
        assert len(dates) > 0
        assert isinstance(dates[0], str)
        
        db.close()
    
    def test_get_dockerfile_names_by_date(self, tmp_path):
        """Test retrieving Dockerfile names for a specific date."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        today = datetime.now(db.TIMEZONE).date().isoformat()
        
        db.add_dockerfile("Dockerfile.flask", "FROM python:3.11")
        db.add_dockerfile("Dockerfile.django", "FROM python:3.11")
        
        names = db.get_dockerfile_names_by_date(today)
        
        assert "Dockerfile.flask" in names
        assert "Dockerfile.django" in names
        
        db.close()
    
    def test_delete_dockerfile(self, tmp_path):
        """Test deleting a Dockerfile."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        result = db.add_dockerfile("Dockerfile.delete", "FROM python:3.11")
        dockerfile_id = result['id']
        
        # Delete it
        deleted = db.delete_dockerfile(dockerfile_id)
        
        assert deleted is True
        
        # Verify it's gone
        dockerfile = db.get_dockerfile_by_date_and_name(
            result['created_date'],
            result['name']
        )
        assert dockerfile is None
        
        db.close()
    
    def test_delete_dockerfile_not_found(self, tmp_path):
        """Test deleting non-existent Dockerfile."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        deleted = db.delete_dockerfile(99999)
        
        assert deleted is False
        
        db.close()
    
    def test_get_statistics(self, tmp_path):
        """Test database statistics."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        # Add some Dockerfiles
        db.add_dockerfile("Dockerfile.1", "FROM python:3.11")
        db.add_dockerfile("Dockerfile.2", "FROM python:3.10")
        
        stats = db.get_statistics()
        
        assert 'total_dockerfiles' in stats
        assert 'unique_dates' in stats
        assert 'unique_names' in stats
        assert stats['total_dockerfiles'] >= 2
        
        db.close()
    
    def test_context_manager(self, tmp_path):
        """Test using database as context manager."""
        db_path = tmp_path / "test.db"
        
        with DockerfileDatabase(str(db_path)) as db:
            db.add_dockerfile("Dockerfile.context", "FROM python:3.11")
            result = db.get_all_dockerfiles()
            assert len(result) > 0
        
        # Database should be closed after context
        # (no easy way to test this without accessing private attributes)
    
    def test_timezone_configuration(self, tmp_path):
        """Test that timezone is properly stored."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        result = db.add_dockerfile("Dockerfile.tz", "FROM python:3.11")
        
        # Verify timezone is stored
        assert result['timezone'] == str(db.TIMEZONE)
        
        db.close()
    
    def test_content_preservation(self, tmp_path):
        """Test that Dockerfile content is preserved exactly."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        # Content with special characters and formatting
        content = """FROM python:3.11-slim

# This is a comment
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
"""
        
        result = db.add_dockerfile("Dockerfile.format", content)
        
        # Retrieve and verify
        retrieved = db.get_dockerfile_by_date_and_name(
            result['created_date'],
            result['name']
        )
        
        assert retrieved['content'] == content
        
        db.close()
    
    def test_multiple_dockerfiles_same_date(self, tmp_path):
        """Test storing multiple Dockerfiles on the same date."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        today = datetime.now(db.TIMEZONE).date().isoformat()
        
        # Add multiple Dockerfiles
        for i in range(5):
            db.add_dockerfile(f"Dockerfile.{i}", f"FROM python:3.{i}")
        
        dockerfiles = db.get_dockerfiles_by_date(today)
        
        assert len(dockerfiles) >= 5
        
        db.close()
    
    def test_timestamp_ordering(self, tmp_path):
        """Test that Dockerfiles are ordered by timestamp."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        today = datetime.now(db.TIMEZONE).date().isoformat()
        
        # Add multiple Dockerfiles
        db.add_dockerfile("Dockerfile.first", "FROM python:3.11")
        db.add_dockerfile("Dockerfile.second", "FROM python:3.10")
        db.add_dockerfile("Dockerfile.third", "FROM python:3.9")
        
        dockerfiles = db.get_dockerfiles_by_date(today)
        
        # Verify they're ordered by time
        for i in range(len(dockerfiles) - 1):
            assert dockerfiles[i]['created_time'] <= dockerfiles[i + 1]['created_time']
        
        db.close()


class TestDockerfileContent:
    """Test various Dockerfile content scenarios."""
    
    def test_empty_dockerfile(self, tmp_path):
        """Test storing an empty Dockerfile."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        result = db.add_dockerfile("Dockerfile.empty", "")
        
        assert result['name'] == "Dockerfile.empty"
        
        retrieved = db.get_dockerfile_by_date_and_name(
            result['created_date'],
            result['name']
        )
        assert retrieved['content'] == ""
        
        db.close()
    
    def test_large_dockerfile(self, tmp_path):
        """Test storing a large Dockerfile."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        # Create a large Dockerfile (simulate multi-stage build)
        content = ""
        for i in range(100):
            content += f"RUN echo 'Step {i}'\n"
        
        result = db.add_dockerfile("Dockerfile.large", content)
        
        retrieved = db.get_dockerfile_by_date_and_name(
            result['created_date'],
            result['name']
        )
        
        assert len(retrieved['content']) == len(content)
        
        db.close()
    
    def test_unicode_in_dockerfile(self, tmp_path):
        """Test storing Dockerfile with Unicode characters."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        content = """FROM python:3.11
# Dockerfile with Unicode: 你好世界 🐳 🐍
RUN echo "Hello 世界"
"""
        
        result = db.add_dockerfile("Dockerfile.unicode", content)
        
        retrieved = db.get_dockerfile_by_date_and_name(
            result['created_date'],
            result['name']
        )
        
        assert retrieved['content'] == content
        
        db.close()
    
    def test_special_characters_in_name(self, tmp_path):
        """Test Dockerfile names with special characters."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        names = [
            "Dockerfile.flask-app",
            "Dockerfile.app_v2",
            "Dockerfile.test.prod"
        ]
        
        for name in names:
            result = db.add_dockerfile(name, "FROM python:3.11")
            assert result['name'] == name
        
        db.close()


class TestDatabaseIndexes:
    """Test database indexes and performance."""
    
    def test_indexes_exist(self, tmp_path):
        """Test that indexes are created."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        # Check for indexes
        db.cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND tbl_name='dockerfiles'
        """)
        
        indexes = [row[0] for row in db.cursor.fetchall()]
        
        assert 'idx_created_date' in indexes
        assert 'idx_name' in indexes
        assert 'idx_name_date' in indexes
        
        db.close()


# Fixtures for testing
@pytest.fixture
def temp_database(tmp_path):
    """Provide a temporary database for testing."""
    db_path = tmp_path / "test.db"
    db = DockerfileDatabase(str(db_path))
    yield db
    db.close()


@pytest.fixture
def populated_database(tmp_path):
    """Provide a database with sample data."""
    db_path = tmp_path / "test.db"
    db = DockerfileDatabase(str(db_path))
    
    # Add sample data
    db.add_dockerfile("Dockerfile.flask", "FROM python:3.11\nWORKDIR /app")
    db.add_dockerfile("Dockerfile.django", "FROM python:3.11\nWORKDIR /app")
    db.add_dockerfile("Dockerfile.fastapi", "FROM python:3.11\nWORKDIR /app")
    
    yield db
    db.close()


@pytest.fixture
def sample_dockerfile_content():
    """Provide sample Dockerfile content."""
    return """FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
"""


# Parametrized tests
@pytest.mark.parametrize("dockerfile_name,expected_framework", [
    ("Dockerfile.flask", "flask"),
    ("Dockerfile.django", "django"),
    ("Dockerfile.fastapi", "fastapi"),
    ("Dockerfile.streamlit", "streamlit"),
    ("Dockerfile", "generic"),
])
def test_dockerfile_naming_convention(temp_database, dockerfile_name, expected_framework):
    """Test that naming conventions are preserved."""
    result = temp_database.add_dockerfile(dockerfile_name, "FROM python:3.11")
    assert result['name'] == dockerfile_name


@pytest.mark.parametrize("content", [
    "FROM python:3.11",
    "FROM python:3.11\nWORKDIR /app",
    "FROM python:3.11\nWORKDIR /app\nCOPY . .",
])
def test_various_dockerfile_contents(temp_database, content):
    """Test storing various Dockerfile contents."""
    result = temp_database.add_dockerfile("Dockerfile.test", content)
    
    retrieved = temp_database.get_dockerfile_by_date_and_name(
        result['created_date'],
        result['name']
    )
    
    assert retrieved['content'] == content


# Integration tests
class TestDatabaseIntegration:
    """Integration tests for complete workflows."""
    
    def test_complete_workflow(self, tmp_path, sample_dockerfile_content):
        """Test complete workflow: add, retrieve, delete."""
        db_path = tmp_path / "test.db"
        
        with DockerfileDatabase(str(db_path)) as db:
            # Add
            result = db.add_dockerfile("Dockerfile.workflow", sample_dockerfile_content)
            dockerfile_id = result['id']
            
            # Retrieve by date
            dockerfiles = db.get_dockerfiles_by_date(result['created_date'])
            assert len(dockerfiles) > 0
            
            # Retrieve by date and name
            dockerfile = db.get_dockerfile_by_date_and_name(
                result['created_date'],
                result['name']
            )
            assert dockerfile is not None
            
            # Statistics
            stats = db.get_statistics()
            assert stats['total_dockerfiles'] > 0
            
            # Delete
            deleted = db.delete_dockerfile(dockerfile_id)
            assert deleted is True
    
    def test_batch_operations(self, tmp_path):
        """Test batch insertion and retrieval."""
        db_path = tmp_path / "test.db"
        db = DockerfileDatabase(str(db_path))
        
        # Batch insert
        count = 10
        for i in range(count):
            db.add_dockerfile(f"Dockerfile.{i}", f"FROM python:3.{i % 3 + 9}")
        
        # Verify all were added
        all_dockerfiles = db.get_all_dockerfiles()
        assert len(all_dockerfiles) >= count
        
        db.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
