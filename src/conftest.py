"""
Pytest configuration and shared fixtures for Dockerfile Generator tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    """Create a temporary directory for test data that persists for the session."""
    return tmp_path_factory.mktemp("test_data")


@pytest.fixture
def clean_temp_dir(tmp_path):
    """Provide a clean temporary directory for each test."""
    yield tmp_path
    # Cleanup is automatic with tmp_path


@pytest.fixture
def sample_python_files(tmp_path):
    """Create a set of sample Python files for testing."""
    files = {}
    
    # Flask app
    files['flask_app'] = tmp_path / "flask_app.py"
    files['flask_app'].write_text('''
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "Hello"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
''')
    
    # FastAPI app
    files['fastapi_app'] = tmp_path / "fastapi_app.py"
    files['fastapi_app'].write_text('''
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
''')
    
    # Django view
    files['django_view'] = tmp_path / "django_view.py"
    files['django_view'].write_text('''
from django.http import HttpResponse

def index(request):
    return HttpResponse("Hello, world.")
''')
    
    # Streamlit app
    files['streamlit_app'] = tmp_path / "streamlit_app.py"
    files['streamlit_app'].write_text('''
import streamlit as st

st.title("My Dashboard")
st.write("Hello, Streamlit!")
''')
    
    # Python 3.10 script
    files['python310'] = tmp_path / "python310.py"
    files['python310'].write_text('''
def process(cmd):
    match cmd:
        case "start":
            return "Starting"
        case "stop":
            return "Stopping"
        case _:
            return "Unknown"

if __name__ == '__main__':
    process("start")
''')
    
    # Python 3.8 script
    files['python38'] = tmp_path / "python38.py"
    files['python38'].write_text('''
def process(data):
    if (n := len(data)) > 0:
        print(f"{n=}")
        return n
    return 0

if __name__ == '__main__':
    process([1, 2, 3])
''')
    
    # Data science script
    files['data_science'] = tmp_path / "data_science.py"
    files['data_science'].write_text('''
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def analyze():
    data = np.random.randn(100)
    df = pd.DataFrame(data, columns=['values'])
    return df.describe()

if __name__ == '__main__':
    print(analyze())
''')
    
    # Simple script
    files['simple_script'] = tmp_path / "simple_script.py"
    files['simple_script'].write_text('''
import requests

def fetch_data(url):
    response = requests.get(url)
    return response.json()

if __name__ == '__main__':
    data = fetch_data("https://api.example.com/data")
    print(data)
''')
    
    return files


@pytest.fixture
def sample_requirements_files(tmp_path):
    """Create sample requirements.txt files."""
    files = {}
    
    # Basic requirements
    files['basic'] = tmp_path / "requirements_basic.txt"
    files['basic'].write_text('''
flask==3.0.0
requests==2.31.0
''')
    
    # Requirements with comments
    files['with_comments'] = tmp_path / "requirements_comments.txt"
    files['with_comments'].write_text('''
# Web framework
flask==3.0.0

# HTTP client
requests==2.31.0

# ASGI server
uvicorn==0.27.0
''')
    
    # Data science requirements
    files['data_science'] = tmp_path / "requirements_ds.txt"
    files['data_science'].write_text('''
pandas==2.2.0
numpy==1.26.0
matplotlib==3.8.0
scikit-learn==1.4.0
''')
    
    # Requirements with versions and extras
    files['complex'] = tmp_path / "requirements_complex.txt"
    files['complex'].write_text('''
flask[async]==3.0.0
requests>=2.31.0,<3.0.0
pandas~=2.2.0
numpy
''')
    
    return files


@pytest.fixture
def dockerfile_assertions():
    """Provide common assertion helpers for Dockerfile content."""
    class DockerfileAssertions:
        @staticmethod
        def has_base_image(content, version=None):
            """Assert Dockerfile has a base image."""
            assert "FROM python:" in content
            if version:
                assert f"FROM python:{version}" in content
        
        @staticmethod
        def has_workdir(content, workdir="/app"):
            """Assert Dockerfile sets WORKDIR."""
            assert f"WORKDIR {workdir}" in content
        
        @staticmethod
        def has_env_vars(content):
            """Assert Dockerfile has Python environment variables."""
            assert "ENV PYTHONDONTWRITEBYTECODE=1" in content
            assert "ENV PYTHONUNBUFFERED=1" in content
        
        @staticmethod
        def has_port_exposed(content, port):
            """Assert Dockerfile exposes a specific port."""
            assert f"EXPOSE {port}" in content
        
        @staticmethod
        def has_cmd(content):
            """Assert Dockerfile has a CMD instruction."""
            assert "CMD" in content
        
        @staticmethod
        def uses_requirements_file(content):
            """Assert Dockerfile uses requirements.txt."""
            assert "COPY requirements.txt ." in content
            assert "pip install --no-cache-dir -r requirements.txt" in content
        
        @staticmethod
        def has_system_deps(content):
            """Assert Dockerfile installs system dependencies."""
            assert "apt-get update" in content
            assert "gcc" in content
        
        @staticmethod
        def is_valid_dockerfile(content):
            """Run basic validation on Dockerfile content."""
            assert content.strip(), "Dockerfile is empty"
            assert "FROM" in content, "Missing FROM instruction"
            assert "CMD" in content or "ENTRYPOINT" in content, "Missing CMD/ENTRYPOINT"
            return True
    
    return DockerfileAssertions()


@pytest.fixture(autouse=True)
def reset_imports():
    """Reset import cache between tests to avoid contamination."""
    import sys
    initial_modules = set(sys.modules.keys())
    yield
    # Clean up any modules imported during the test
    current_modules = set(sys.modules.keys())
    for module in current_modules - initial_modules:
        if module.startswith('test_') or module.startswith('dockerfile_'):
            sys.modules.pop(module, None)


def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_vermin: mark test as requiring vermin package"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Mark integration tests
        if "test_end_to_end" in item.nodeid or "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        # Mark unit tests
        elif "Test" in item.nodeid and "EndToEnd" not in item.nodeid:
            item.add_marker(pytest.mark.unit)


# Utility functions for tests
def create_python_file(path: Path, content: str) -> Path:
    """Helper to create a Python file with content."""
    path.write_text(content)
    return path


def create_requirements_file(path: Path, packages: list) -> Path:
    """Helper to create a requirements.txt file."""
    content = '\n'.join(packages)
    path.write_text(content)
    return path
