# Dockerfile Generator for Python Applications (Enhanced)

A Python tool that automatically generates Dockerfiles by analyzing Python files and detecting their dependencies, **minimum Python version requirements**, framework type, and configuration needs.

## 🆕 New Features (v2.0)

- **🔍 Automatic Python Version Detection**: Uses the `vermin` package to detect minimum required Python version
- **📊 Multi-file Analysis**: Option to scan imported local modules for version requirements
- **🔄 Intelligent Fallback**: AST-based version detection when vermin is not available
- **📝 Enhanced CLI**: Improved command-line interface with more options

## Features

- 🔍 **Automatic Dependency Detection**: Analyzes Python files to extract import statements
- 🐍 **Minimum Python Version Detection**: Uses vermin or AST analysis to determine required Python version
- 📦 **Framework Recognition**: Detects Flask, Django, FastAPI, and Streamlit applications
- 📋 **requirements.txt Support**: Uses existing requirements.txt if available
- 🚀 **Smart CMD Generation**: Creates appropriate run commands based on app type
- 🔧 **System Dependencies**: Automatically includes system packages when needed

## Installation

### Basic Installation

```bash
# Download the script
wget https://raw.githubusercontent.com/your-repo/dockerfile_generator_v2.py
# or
curl -O https://raw.githubusercontent.com/your-repo/dockerfile_generator_v2.py
```

### Recommended: Install with vermin

For best results, install the `vermin` package for accurate Python version detection:

```bash
pip install vermin
```

Without vermin, the tool will use AST-based fallback detection, which can detect:
- Python 3.10+ features (match statements)
- Python 3.8+ features (walrus operator `:=`, f-string `=` debugging)
- Python 3.7 as default minimum

## Usage

### Basic Usage

```bash
# Generate Dockerfile with auto-detected Python version
python dockerfile_generator_v2.py app.py

# Specify output file
python dockerfile_generator_v2.py app.py -o custom_Dockerfile

# Scan imported local modules for version requirements
python dockerfile_generator_v2.py app.py --scan-imports
```

### Command-Line Options

```
usage: dockerfile_generator_v2.py [-h] [-o OUTPUT] [-s] python_file

Arguments:
  python_file           Path to the Python file to analyze

Options:
  -h, --help           Show help message and exit
  -o, --output OUTPUT  Output Dockerfile path (default: Dockerfile)
  -s, --scan-imports   Scan local imported modules for version requirements
```

### Examples

#### Example 1: Python 3.10+ Application

```python
# app.py - uses match statement (Python 3.10+)
def process_command(cmd):
    match cmd:
        case "start":
            return "Starting..."
        case "stop":
            return "Stopping..."
        case _:
            return "Unknown"
```

```bash
python dockerfile_generator_v2.py app.py
```

**Output**: Generates Dockerfile with `FROM python:3.10-slim`

#### Example 2: Python 3.8+ Application

```python
# data.py - uses walrus operator (Python 3.8+)
if (n := len(data)) > 10:
    print(f"{n=}")  # f-string = also requires 3.8+
```

```bash
python dockerfile_generator_v2.py data.py
```

**Output**: Generates Dockerfile with `FROM python:3.8-slim`

#### Example 3: Flask Application with Dependencies

```bash
python dockerfile_generator_v2.py flask_app.py
```

**Output**: Detects Flask framework, exposes port 5000, uses requirements.txt

## How Version Detection Works

### With Vermin (Recommended)

When vermin is installed, the tool:
1. Analyzes your Python file's syntax and features
2. Checks language constructs against Python version compatibility
3. Optionally scans imported local modules (with `--scan-imports`)
4. Returns the minimum Python version required

### Fallback Detection (Without Vermin)

If vermin is not available, the tool uses AST analysis to detect:

| Feature | Minimum Version |
|---------|----------------|
| Match statement (`match`/`case`) | Python 3.10 |
| Walrus operator (`:=`) | Python 3.8 |
| F-string debugging (`f"{x=}"`) | Python 3.8 |
| Positional-only parameters | Python 3.8 |
| Default | Python 3.7 |

## Generated Dockerfile Structure

The generated Dockerfile includes:

```dockerfile
# Use official Python runtime as base image
# Python version X.Y detected via vermin/ast-analysis
FROM python:X.Y-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (for web apps)
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
```

## Supported Application Types

| Framework | Port | Detection | CMD Format |
|-----------|------|-----------|------------|
| Flask | 5000 | `import flask` | `python app.py` |
| Django | 8000 | `import django` | `python manage.py runserver` |
| FastAPI | 8000 | `import fastapi` | `uvicorn app:app` |
| Streamlit | 8501 | `import streamlit` | `streamlit run app.py` |
| Script | N/A | Default | `python script.py` |

## Python Version Detection Examples

### Example Output

```bash
$ python dockerfile_generator_v2.py modern_app.py

Analyzing Python file: modern_app.py
✓ Using vermin for Python version detection
Detected imports: requests, pandas
Application type: script
Python version: 3.9 (detected via vermin)

✓ Dockerfile generated successfully: Dockerfile
```

### Comparison: Vermin vs Fallback

**With Vermin (More Accurate)**:
- Detects exact minimum version across all Python versions
- Analyzes standard library usage
- Checks feature compatibility comprehensively
- Scans dependencies if requested

**Fallback (Good for Common Cases)**:
- Detects major version-specific features
- Works without external dependencies
- Fast and lightweight
- Sufficient for most modern Python code (3.7+)

## Building and Running

After generating the Dockerfile:

```bash
# Build the Docker image
docker build -t my-python-app .

# Run the container
docker run -p 5000:5000 my-python-app

# For scripts (no port mapping needed)
docker run my-python-app
```

## Advanced Usage

### As a Python Module

```python
from dockerfile_generator_v2 import generate_dockerfile

# Basic usage
dockerfile = generate_dockerfile('app.py')

# With import scanning
dockerfile = generate_dockerfile('app.py', scan_imports=True)

# Custom output location
dockerfile = generate_dockerfile('app.py', output_file='custom.Dockerfile')
```

### Customizing Detection

```python
from dockerfile_generator_v2 import PythonFileAnalyzer, DockerfileGenerator

# Analyze with import scanning
analyzer = PythonFileAnalyzer('app.py', scan_imports_for_version=True)
metadata = analyzer.analyze()

print(f"Detected version: {metadata['python_version']}")
print(f"Detection method: {metadata['version_detection_method']}")

# Customize metadata before generation
metadata['python_version'] = '3.11'  # Override if needed

# Generate Dockerfile
generator = DockerfileGenerator(metadata)
dockerfile = generator.generate()
```

## Requirements Detection

The tool checks for dependencies in this order:

1. **requirements.txt** (if exists in same directory)
2. **Detected imports** (parsed from source code)
3. **Standard library modules** (filtered out automatically)

## System Dependencies

The tool automatically includes system dependencies for packages that need compilation:

- `numpy`, `pandas` → Requires `gcc`
- `pillow` → Requires `gcc`
- `psycopg2`, `mysqlclient` → Requires `gcc`
- `lxml` → Requires `gcc`

## Tips for Best Results

1. **Install vermin**: For the most accurate version detection
   ```bash
   pip install vermin
   ```

2. **Maintain requirements.txt**: Keep an up-to-date requirements.txt file
   ```bash
   pip freeze > requirements.txt
   ```

3. **Use --scan-imports**: For projects with local modules
   ```bash
   python dockerfile_generator_v2.py main.py --scan-imports
   ```

4. **Review generated Dockerfile**: Always review before use in production

5. **Add .dockerignore**: Exclude unnecessary files
   ```
   __pycache__/
   *.pyc
   .git/
   .env
   venv/
   ```

## Troubleshooting

### Q: Vermin is installed but not being detected

**A**: Make sure vermin is in the same Python environment:
```bash
python -c "import vermin; print(vermin.__version__)"
```

### Q: Wrong Python version detected

**A**: The fallback detector has limitations. Install vermin for accurate detection, or manually edit the generated Dockerfile.

### Q: How to force a specific Python version?

**A**: Either:
- Edit the generated Dockerfile manually
- Modify the code to accept a `--python-version` flag (see customization example)

### Q: App doesn't work in Docker container

**A**: Common issues:
- Missing files (check COPY commands)
- Wrong working directory
- Missing environment variables
- Port not exposed correctly

## Changelog

### Version 2.0 (Current)
- ✨ Added automatic Python version detection using vermin
- ✨ Added AST-based fallback version detection
- ✨ Added `--scan-imports` flag for multi-file analysis
- ✨ Improved CLI with argparse
- 📝 Enhanced documentation
- 🎯 Better detection of Python 3.8, 3.10+ features

### Version 1.0
- Initial release
- Basic dependency detection
- Framework recognition
- requirements.txt support

## Contributing

Suggestions for improvement:
- Add support for more frameworks (Tornado, Sanic, etc.)
- Multi-stage build generation
- Docker Compose file generation
- Poetry/Pipenv support
- Custom base image selection

## License

This tool is provided as-is for educational and development purposes.

## Acknowledgments

- **vermin**: Python version detection - https://github.com/netromdk/vermin
- Python AST module for syntax analysis
- Docker best practices documentation
