"""
Test suite for Dockerfile Generator
Tests all major components including version detection, import parsing, and Dockerfile generation.
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# Import the modules to test
from dockerfile_generator_v2 import (
    PythonVersionDetector,
    PythonFileAnalyzer,
    DockerfileGenerator,
    generate_dockerfile
)


class TestPythonVersionDetector:
    """Test suite for Python version detection."""
    
    def test_detect_python310_match_statement(self, tmp_path):
        """Test detection of Python 3.10 match statement."""
        code = '''
def process(cmd):
    match cmd:
        case "start":
            return "starting"
        case _:
            return "unknown"
'''
        file_path = tmp_path / "test_match.py"
        file_path.write_text(code)
        
        detector = PythonVersionDetector(str(file_path))
        version, method = detector.detect_version()
        
        assert version == "3.10"
        assert method in ["vermin", "ast-analysis"]
    
    def test_detect_python38_walrus_operator(self, tmp_path):
        """Test detection of Python 3.8 walrus operator."""
        code = '''
def process(data):
    if (n := len(data)) > 10:
        return n
    return 0
'''
        file_path = tmp_path / "test_walrus.py"
        file_path.write_text(code)
        
        detector = PythonVersionDetector(str(file_path))
        version, method = detector.detect_version()
        
        assert version == "3.8"
        assert method in ["vermin", "ast-analysis"]
    
    def test_detect_python38_fstring_equals(self, tmp_path):
        """Test detection of Python 3.8 f-string = debugging."""
        code = '''
def debug(x, y):
    print(f"{x=}, {y=}")
    return x + y
'''
        file_path = tmp_path / "test_fstring.py"
        file_path.write_text(code)
        
        detector = PythonVersionDetector(str(file_path))
        version, method = detector.detect_version()

        # Note: used to test for
        assert version == "3.8"
        assert method in ["vermin", "ast-analysis"]
    
    def test_detect_default_version(self, tmp_path):
        """Test default version for generic code."""
        code = '''
import json

def load_config(path):
    with open(path) as f:
        return json.load(f)
'''
        file_path = tmp_path / "test_generic.py"
        file_path.write_text(code)
        
        detector = PythonVersionDetector(str(file_path))
        version, method = detector.detect_version()
        
        # Should be a valid version
        # NOTE: Oddly, claude thought that anything in the test code was from a later version.
        # All attributes were added in 2.6 and beyond.
        # assert version in ["3.7", "3.8", "3.9", "3.10", "3.11"]
        assert version in ["2.5", "2.6", "2.7", "3.0"]
        assert method in ["vermin", "ast-analysis", "default", "vermin-default"]
    
    def test_vermin_availability_check(self):
        """Test that vermin availability is correctly detected."""
        detector = PythonVersionDetector(__file__)
        
        # Should be a boolean
        assert isinstance(detector.vermin_available, bool)


class TestPythonFileAnalyzer:
    """Test suite for Python file analysis."""
    
    def test_extract_imports_basic(self, tmp_path):
        """Test basic import extraction."""
        code = '''
import flask
from django.http import HttpResponse
import numpy as np
'''
        file_path = tmp_path / "test_imports.py"
        file_path.write_text(code)
        
        analyzer = PythonFileAnalyzer(str(file_path))
        metadata = analyzer.analyze()
        
        assert "flask" in metadata['imports']
        assert "django" in metadata['imports']
        assert "numpy" in metadata['imports']
    
    def test_filter_stdlib_modules(self, tmp_path):
        """Test that standard library modules are filtered out."""
        code = '''
import os
import sys
import json
import requests
'''
        file_path = tmp_path / "test_stdlib.py"
        file_path.write_text(code)
        
        analyzer = PythonFileAnalyzer(str(file_path))
        metadata = analyzer.analyze()
        
        # stdlib modules should be filtered out
        assert "os" not in metadata['imports']
        assert "sys" not in metadata['imports']
        assert "json" not in metadata['imports']
        
        # third-party should be included
        assert "requests" in metadata['imports']
    
    def test_detect_flask_app(self, tmp_path):
        """Test Flask application detection."""
        code = '''
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello"

if __name__ == '__main__':
    app.run()
'''
        file_path = tmp_path / "test_flask.py"
        file_path.write_text(code)
        
        analyzer = PythonFileAnalyzer(str(file_path))
        metadata = analyzer.analyze()
        
        assert metadata['app_type'] == "flask"
        assert metadata['is_executable'] == True
    
    def test_detect_fastapi_app(self, tmp_path):
        """Test FastAPI application detection."""
        code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
'''
        file_path = tmp_path / "test_fastapi.py"
        file_path.write_text(code)
        
        analyzer = PythonFileAnalyzer(str(file_path))
        metadata = analyzer.analyze()
        
        assert metadata['app_type'] == "fastapi"
    
    def test_detect_django_app(self, tmp_path):
        """Test Django application detection."""
        code = '''
from django.http import HttpResponse

def index(request):
    return HttpResponse("Hello")
'''
        file_path = tmp_path / "test_django.py"
        file_path.write_text(code)
        
        analyzer = PythonFileAnalyzer(str(file_path))
        metadata = analyzer.analyze()
        
        assert metadata['app_type'] == "django"
    
    def test_detect_streamlit_app(self, tmp_path):
        """Test Streamlit application detection."""
        code = '''
import streamlit as st

st.title("My App")
st.write("Hello World")
'''
        file_path = tmp_path / "test_streamlit.py"
        file_path.write_text(code)
        
        analyzer = PythonFileAnalyzer(str(file_path))
        metadata = analyzer.analyze()
        
        assert metadata['app_type'] == "streamlit"
    
    def test_detect_script_type(self, tmp_path):
        """Test regular script detection."""
        code = '''
import requests

def fetch_data():
    return requests.get("https://api.example.com/data")

if __name__ == '__main__':
    data = fetch_data()
    print(data)
'''
        file_path = tmp_path / "test_script.py"
        file_path.write_text(code)
        
        analyzer = PythonFileAnalyzer(str(file_path))
        metadata = analyzer.analyze()
        
        assert metadata['app_type'] == "script"
    
    def test_is_executable_with_main_guard(self, tmp_path):
        """Test detection of executable scripts with main guard."""
        code = '''
def main():
    print("Hello")

if __name__ == '__main__':
    main()
'''
        file_path = tmp_path / "test_executable.py"
        file_path.write_text(code)
        
        analyzer = PythonFileAnalyzer(str(file_path))
        metadata = analyzer.analyze()
        
        assert metadata['is_executable'] == True
    
    def test_is_executable_without_main_guard(self, tmp_path):
        """Test detection of non-executable scripts."""
        code = '''
def helper_function():
    return "I'm a helper"
'''
        file_path = tmp_path / "test_non_executable.py"
        file_path.write_text(code)
        
        analyzer = PythonFileAnalyzer(str(file_path))
        metadata = analyzer.analyze()
        
        assert metadata['is_executable'] == False
    
    def test_requirements_txt_detection(self, tmp_path):
        """Test detection of requirements.txt file."""
        code = '''
import flask
'''
        file_path = tmp_path / "test_app.py"
        file_path.write_text(code)
        
        # Create requirements.txt
        req_path = tmp_path / "requirements.txt"
        req_path.write_text("flask==3.0.0\nrequests==2.31.0\n")
        
        analyzer = PythonFileAnalyzer(str(file_path))
        metadata = analyzer.analyze()
        
        assert len(metadata['requirements']) == 2
        assert "flask==3.0.0" in metadata['requirements']
        assert "requests==2.31.0" in metadata['requirements']
    
    def test_file_not_found(self):
        """Test handling of non-existent files."""
        analyzer = PythonFileAnalyzer("/nonexistent/file.py")
        
        with pytest.raises(FileNotFoundError):
            analyzer.analyze()


class TestDockerfileGenerator:
    """Test suite for Dockerfile generation."""
    
    def test_generate_basic_dockerfile(self):
        """Test basic Dockerfile generation."""
        metadata = {
            'imports': set(),
            'requirements': [],
            'python_version': '3.11',
            'version_detection_method': 'default',
            'app_type': 'script',
            'is_executable': True,
            'filename': 'app.py'
        }
        
        generator = DockerfileGenerator(metadata)
        dockerfile = generator.generate()
        
        assert "FROM python:3.11-slim" in dockerfile
        assert "WORKDIR /app" in dockerfile
        assert "ENV PYTHONDONTWRITEBYTECODE=1" in dockerfile
        assert "ENV PYTHONUNBUFFERED=1" in dockerfile
        assert 'CMD ["python", "app.py"]' in dockerfile
    
    def test_generate_flask_dockerfile(self):
        """Test Flask-specific Dockerfile generation."""
        metadata = {
            'imports': {'flask'},
            'requirements': ['flask==3.0.0'],
            'python_version': '3.10',
            'version_detection_method': 'vermin',
            'app_type': 'flask',
            'is_executable': True,
            'filename': 'app.py'
        }
        
        generator = DockerfileGenerator(metadata)
        dockerfile = generator.generate()
        
        assert "FROM python:3.10-slim" in dockerfile
        assert "EXPOSE 5000" in dockerfile
        assert 'CMD ["python", "app.py"]' in dockerfile
        assert "COPY requirements.txt ." in dockerfile
    
    def test_generate_fastapi_dockerfile(self):
        """Test FastAPI-specific Dockerfile generation."""
        metadata = {
            'imports': {'fastapi'},
            'requirements': ['fastapi==0.109.0', 'uvicorn==0.27.0'],
            'python_version': '3.11',
            'version_detection_method': 'ast-analysis',
            'app_type': 'fastapi',
            'is_executable': False,
            'filename': 'main.py'
        }
        
        generator = DockerfileGenerator(metadata)
        dockerfile = generator.generate()
        
        assert "FROM python:3.11-slim" in dockerfile
        assert "EXPOSE 8000" in dockerfile
        assert 'CMD ["uvicorn", "main:app"' in dockerfile
    
    def test_generate_django_dockerfile(self):
        """Test Django-specific Dockerfile generation."""
        metadata = {
            'imports': {'django'},
            'requirements': ['django==5.0.0'],
            'python_version': '3.11',
            'version_detection_method': 'default',
            'app_type': 'django',
            'is_executable': False,
            'filename': 'views.py'
        }
        
        generator = DockerfileGenerator(metadata)
        dockerfile = generator.generate()
        
        assert "EXPOSE 8000" in dockerfile
        assert 'CMD ["python", "manage.py", "runserver"' in dockerfile
    
    def test_generate_streamlit_dockerfile(self):
        """Test Streamlit-specific Dockerfile generation."""
        metadata = {
            'imports': {'streamlit'},
            'requirements': ['streamlit==1.30.0'],
            'python_version': '3.9',
            'version_detection_method': 'vermin',
            'app_type': 'streamlit',
            'is_executable': False,
            'filename': 'dashboard.py'
        }
        
        generator = DockerfileGenerator(metadata)
        dockerfile = generator.generate()
        
        assert "EXPOSE 8501" in dockerfile
        assert 'CMD ["streamlit", "run", "dashboard.py"' in dockerfile
    
    def test_system_dependencies_for_numpy(self):
        """Test that system dependencies are added for packages that need compilation."""
        metadata = {
            'imports': {'numpy', 'pandas'},
            'requirements': [],
            'python_version': '3.11',
            'version_detection_method': 'default',
            'app_type': 'script',
            'is_executable': True,
            'filename': 'data.py'
        }
        
        generator = DockerfileGenerator(metadata)
        dockerfile = generator.generate()
        
        assert "gcc" in dockerfile
        assert "apt-get update" in dockerfile
    
    def test_no_system_dependencies_for_pure_python(self):
        """Test that system dependencies are not added for pure Python packages."""
        metadata = {
            'imports': {'requests', 'flask'},
            'requirements': [],
            'python_version': '3.11',
            'version_detection_method': 'default',
            'app_type': 'flask',
            'is_executable': True,
            'filename': 'app.py'
        }
        
        generator = DockerfileGenerator(metadata)
        dockerfile = generator.generate()
        
        assert "gcc" not in dockerfile or "apt-get" not in dockerfile
    
    def test_requirements_vs_imports(self):
        """Test that requirements.txt takes precedence over detected imports."""
        metadata = {
            'imports': {'flask', 'requests'},
            'requirements': ['flask==3.0.0', 'requests==2.31.0', 'gunicorn==21.2.0'],
            'python_version': '3.11',
            'version_detection_method': 'default',
            'app_type': 'flask',
            'is_executable': True,
            'filename': 'app.py'
        }
        
        generator = DockerfileGenerator(metadata)
        dockerfile = generator.generate()
        
        # Should use requirements.txt
        assert "COPY requirements.txt ." in dockerfile
        assert "RUN pip install --no-cache-dir -r requirements.txt" in dockerfile
        
        # Should NOT install packages directly
        assert "RUN pip install --no-cache-dir flask requests" not in dockerfile
    
    def test_no_requirements_installs_imports(self):
        """Test that imports are installed when no requirements.txt exists."""
        metadata = {
            'imports': {'flask', 'requests'},
            'requirements': [],
            'python_version': '3.11',
            'version_detection_method': 'default',
            'app_type': 'flask',
            'is_executable': True,
            'filename': 'app.py'
        }
        
        generator = DockerfileGenerator(metadata)
        dockerfile = generator.generate()
        
        # Should install packages directly
        assert "RUN pip install --no-cache-dir" in dockerfile
        assert "flask" in dockerfile or "requests" in dockerfile


class TestEndToEnd:
    """End-to-end integration tests."""
    
    def test_generate_dockerfile_flask_app(self, tmp_path):
        """Test complete workflow for Flask application."""
        code = '''
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "running"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
'''
        file_path = tmp_path / "flask_app.py"
        file_path.write_text(code)
        
        # Create requirements.txt
        req_path = tmp_path / "requirements.txt"
        req_path.write_text("flask==3.0.0\n")
        
        dockerfile_path = tmp_path / "Dockerfile"
        
        # Generate Dockerfile
        content = generate_dockerfile(str(file_path), str(dockerfile_path))
        
        # Verify file was created
        assert dockerfile_path.exists()
        
        # Verify content
        assert "FROM python:" in content
        assert "flask" in content.lower()
        assert "EXPOSE 5000" in content
        assert "CMD" in content
    
    def test_generate_dockerfile_python310_script(self, tmp_path):
        """Test complete workflow for Python 3.10 script."""
        code = '''
def process(cmd):
    match cmd:
        case "start":
            print("Starting")
        case "stop":
            print("Stopping")
        case _:
            print("Unknown")

if __name__ == '__main__':
    process("start")
'''
        file_path = tmp_path / "script.py"
        file_path.write_text(code)
        
        dockerfile_path = tmp_path / "Dockerfile"
        
        # Generate Dockerfile
        content = generate_dockerfile(str(file_path), str(dockerfile_path))
        
        # Verify Python 3.10 is detected
        assert "python:3.10" in content
    
    def test_generate_dockerfile_data_science_app(self, tmp_path):
        """Test complete workflow for data science application."""
        code = '''
import pandas as pd
import numpy as np

def analyze_data():
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    return df.describe()

if __name__ == '__main__':
    print(analyze_data())
'''
        file_path = tmp_path / "analyze.py"
        file_path.write_text(code)
        
        dockerfile_path = tmp_path / "Dockerfile"
        
        # Generate Dockerfile
        content = generate_dockerfile(str(file_path), str(dockerfile_path))
        
        # Verify system dependencies for numpy/pandas
        assert "gcc" in content
        assert "pandas" in content or "numpy" in content


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_file(self, tmp_path):
        """Test handling of empty Python file."""
        file_path = tmp_path / "empty.py"
        file_path.write_text("")
        
        analyzer = PythonFileAnalyzer(str(file_path))
        metadata = analyzer.analyze()
        
        assert metadata['imports'] == set()
        assert metadata['app_type'] == 'script'
    
    def test_syntax_error_file(self, tmp_path):
        """Test handling of file with syntax errors."""
        code = '''
def broken_function(
    # Missing closing parenthesis
    print("This won't parse")
'''
        file_path = tmp_path / "broken.py"
        file_path.write_text(code)
        
        analyzer = PythonFileAnalyzer(str(file_path))
        # Should not crash, should fall back to regex
        metadata = analyzer.analyze()
        
        # Should still return valid metadata
        assert 'imports' in metadata
        assert 'app_type' in metadata
    
    def test_unicode_in_file(self, tmp_path):
        """Test handling of Unicode characters in file."""
        code = '''
# -*- coding: utf-8 -*-
def greet(name):
    return f"こんにちは {name}! 🎉"

if __name__ == '__main__':
    print(greet("世界"))
'''
        file_path = tmp_path / "unicode.py"
        file_path.write_text(code, encoding='utf-8')
        
        analyzer = PythonFileAnalyzer(str(file_path))
        metadata = analyzer.analyze()
        
        assert metadata['is_executable'] == True
    
    def test_requirements_with_comments(self, tmp_path):
        """Test parsing requirements.txt with comments."""
        code = "import flask"
        file_path = tmp_path / "app.py"
        file_path.write_text(code)
        
        req_path = tmp_path / "requirements.txt"
        req_content = """
# Web framework
flask==3.0.0

# HTTP library
requests==2.31.0

# This is a comment
# Another comment
gunicorn==21.2.0
"""
        req_path.write_text(req_content)
        
        analyzer = PythonFileAnalyzer(str(file_path))
        metadata = analyzer.analyze()
        
        # Comments should be filtered out
        assert len(metadata['requirements']) == 3
        assert all(not req.startswith('#') for req in metadata['requirements'])


# Pytest fixtures
@pytest.fixture
def sample_flask_app(tmp_path):
    """Fixture providing a sample Flask application."""
    code = '''
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Hello"

if __name__ == '__main__':
    app.run()
'''
    file_path = tmp_path / "app.py"
    file_path.write_text(code)
    return file_path


@pytest.fixture
def sample_requirements(tmp_path):
    """Fixture providing a sample requirements.txt."""
    req_path = tmp_path / "requirements.txt"
    req_path.write_text("flask==3.0.0\nrequests==2.31.0\n")
    return req_path


# Parametrized tests
@pytest.mark.parametrize("app_type,import_stmt,expected_port", [
    ("flask", "import flask", 5000),
    ("django", "import django", 8000),
    ("fastapi", "import fastapi", 8000),
    ("streamlit", "import streamlit", 8501),
])
def test_framework_port_detection(tmp_path, app_type, import_stmt, expected_port):
    """Parametrized test for framework port detection."""
    code = f"{import_stmt}\n\ndef main():\n    pass"
    file_path = tmp_path / "app.py"
    file_path.write_text(code)
    
    analyzer = PythonFileAnalyzer(str(file_path))
    metadata = analyzer.analyze()
    
    generator = DockerfileGenerator(metadata)
    dockerfile = generator.generate()
    
    assert f"EXPOSE {expected_port}" in dockerfile

# NOTE:
# Had to fix code f-string, did not account for indents properly.
# Had to fix test 1, claude did NOT indent it properly.
# Test 3 is ambiguous, as vermin cannot disseminate between self-documenting fstrings from general fstrings
@pytest.mark.parametrize("python_feature,expected_version", [
    ("match cmd:\n\t\tcase _:\n\t\t\tpass", "3.10"),
    ("if (n := len(data)):\n\t\tpass", "3.8"),
    ('print(f"{x=}")\n\tpass', "3.8"),
])
def test_version_detection_features(tmp_path, python_feature, expected_version):
    """Parametrized test for Python version detection."""
    code = f'''
def test_function():
\t{python_feature}
'''
    file_path = tmp_path / "test.py"
    file_path.write_text(code)
    
    detector = PythonVersionDetector(str(file_path))
    version, _ = detector.detect_version()
    
    assert version == expected_version


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
