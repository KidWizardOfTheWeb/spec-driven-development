# Version Detection Comparison

This document shows how the enhanced Dockerfile generator detects Python versions for different code examples.

## Example 1: Python 3.10+ (Match Statement)

### Code Sample
```python
def process_command(command: str) -> str:
    match command:
        case "start":
            return "Starting application"
        case "stop":
            return "Stopping application"
        case _:
            return "Unknown command"
```

### Detection Result
- **Detected Version**: Python 3.10
- **Reason**: Match statement (`match`/`case`) introduced in Python 3.10
- **Generated Dockerfile**: `FROM python:3.10-slim`

## Example 2: Python 3.8+ (Walrus Operator)

### Code Sample
```python
def process_data(data: list) -> dict:
    results = []
    # Walrus operator :=
    while (item := next((x for x in data if x > 10), None)) is not None:
        results.append(item)
        data.remove(item)
    return {"processed": results}
```

### Detection Result
- **Detected Version**: Python 3.8
- **Reason**: Walrus operator (`:=`) introduced in Python 3.8
- **Generated Dockerfile**: `FROM python:3.8-slim`

## Example 3: Python 3.8+ (F-String Debugging)

### Code Sample
```python
def debug_values(x: int, y: int) -> None:
    # F-string with = for debugging
    print(f"{x=}, {y=}")
    result = x + y
    print(f"{result=}")
```

### Detection Result
- **Detected Version**: Python 3.8
- **Reason**: F-string `=` syntax introduced in Python 3.8
- **Generated Dockerfile**: `FROM python:3.8-slim`

## Example 4: Generic Python Code

### Code Sample
```python
import json
import os

def load_config(filepath: str) -> dict:
    with open(filepath, 'r') as f:
        return json.load(f)

if __name__ == '__main__':
    config = load_config('config.json')
    print(config)
```

### Detection Result
- **Detected Version**: Python 3.7 (default)
- **Reason**: No version-specific features detected
- **Generated Dockerfile**: `FROM python:3.7-slim`

## Vermin vs Fallback Detection

### With Vermin Package

**Advantages**:
- Detects ALL Python version-specific features across all versions
- Analyzes standard library API changes
- More comprehensive and accurate
- Can analyze multiple files together
- Provides exact minimum version required

**Example Output**:
```bash
$ python dockerfile_generator_v2.py app.py --scan-imports
Analyzing Python file: app.py
✓ Using vermin for Python version detection
Detected imports: requests, typing
Application type: script
Python version: 3.9 (detected via vermin)
```

### Fallback (AST Analysis)

**Advantages**:
- No external dependencies required
- Fast and lightweight
- Good for common version-specific features
- Works offline

**Limitations**:
- Only detects specific major features (match, walrus operator, etc.)
- May not catch subtle API changes
- Defaults to 3.7 for generic code

**Example Output**:
```bash
$ python dockerfile_generator_v2.py app.py
Analyzing Python file: app.py
ℹ Vermin not installed - using fallback version detection
  Install with: pip install vermin
Detected imports: requests, typing
Application type: script
Python version: 3.7 (detected via ast-analysis)
```

## Real-World Example: Flask Application

### Code (flask_app.py)
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    # Using walrus operator
    if (data := {"status": "running"}) is not None:
        return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Detection with Fallback
```bash
$ python dockerfile_generator_v2.py flask_app.py

Analyzing Python file: flask_app.py
ℹ Vermin not installed - using fallback version detection
Detected imports: flask
Application type: flask
Python version: 3.8 (detected via ast-analysis)

Generated Dockerfile uses: FROM python:3.8-slim
Exposes: PORT 5000
```

### Generated Dockerfile
```dockerfile
# Use official Python runtime as base image
# Python version 3.8 detected via ast-analysis
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "flask_app.py"]
```

## Testing the Detection

You can test the version detection on your own files:

```bash
# Test with Python 3.10 features
python dockerfile_generator_v2.py python310_features.py

# Test with Python 3.8 features
python dockerfile_generator_v2.py python38_features.py

# Test with imports scanning (requires vermin)
python dockerfile_generator_v2.py main.py --scan-imports
```

## Recommendation

For production use or accuracy-critical projects:
1. Install vermin: `pip install vermin`
2. Use `--scan-imports` flag for multi-file projects
3. Always review the generated Dockerfile
4. Test the Docker build before deployment

For quick prototyping or simple scripts:
1. The fallback detector works well for common cases
2. Fast and requires no dependencies
3. Good for CI/CD pipelines where you want minimal dependencies
