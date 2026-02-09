#!/usr/bin/env python3
"""
Dockerfile Generator for Python Applications (Enhanced with Version Detection)

This script analyzes Python files and generates appropriate Dockerfiles
based on detected dependencies, minimum Python version requirements, and project structure.

Features:
- Automatic minimum Python version detection using vermin
- Dependency analysis and framework detection
- Smart Dockerfile generation based on app type
"""

import os
import re
import sys
import ast
import subprocess
from pathlib import Path
from typing import Set, Optional, Dict, List, Tuple


class PythonVersionDetector:
    """Detects minimum required Python version for a file and its imports."""
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.vermin_available = self._check_vermin_available()
        
    def _check_vermin_available(self) -> bool:
        """Check if vermin is installed."""
        try:
            import vermin
            return True
        except ImportError:
            return False
    
    def detect_version(self, scan_imports: bool = False) -> Tuple[Optional[str], str]:
        """
        Detect minimum Python version required.
        
        Args:
            scan_imports: If True, also scan imported local modules
            
        Returns:
            Tuple of (version_string, detection_method)
            e.g., ('3.8', 'vermin') or ('3.11', 'default')
        """
        if self.vermin_available:
            return self._detect_with_vermin(scan_imports)
        else:
            return self._detect_fallback()
    
    def _detect_with_vermin(self, scan_imports: bool) -> Tuple[str, str]:
        """Detect version using vermin package."""
        try:
            import vermin as v
            from vermin.config import Config
            
            # Configure vermin
            config = v.Config()
            config.quiet = True
            config.show_tips = False
            
            # Files to analyze
            files = [str(self.filepath)]

            scan_command = ['vermin', "--format", "parsable", "--feature", "fstring-self-doc"] + files
            
            # Optionally scan local imports
            if scan_imports:
                local_imports = self._find_local_imports()
                files.extend(local_imports)

                # Scan all imported files here instead of only one.
                scan_command = ['vermin', "--format", "parsable", "--feature", "fstring-self-doc"] + files

            # TODO: add read entire project directory option

            try:
                process = subprocess.Popen(scan_command, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, text=True)
                stdout, stderr = process.communicate()
                if process.returncode == 0:
                    # Output when quiet (-q) only prints the final verdict: "Minimum required versions: X.Y, Z.W"

                    # This, along with the parsable flag, splits the versions into a list to read properly.
                    # https://github.com/netromdk/vermin?tab=readme-ov-file#parsable-output
                    # Last line (entry in the list) contains minimum and maximum versions, so only get the end for our purposes.
                    check_output = stdout.splitlines()[-1]

                    # Split the line into it's segments
                    minimum_versions = check_output.split(":")
                    # We want index 3 & 4, as it contains the minimum py2 version and minimum py3 version, respectively.
                    min_py2_version = minimum_versions[3] if minimum_versions[3] != "!2" else None
                    min_py3_version = minimum_versions[4] if minimum_versions[4] != "!3" else None

                    if min_py2_version:
                        return min_py2_version, 'vermin'
                    if min_py3_version:
                        return min_py3_version, 'vermin'
                    else:
                        print("Analysis complete, no specific minimum versions detected or inconclusivity.")
                else:
                    print(f"Vermin analysis failed: {stderr}")

            except FileNotFoundError as e:
                print("Error: vermin is not installed or not in PATH.")

            # Below is antiquated old behavior from claude, get rid of it.
            # while minimum_versions() existed, it did not work in this context, as the API is experimental:
            # https://github.com/netromdk/vermin?tab=readme-ov-file#api-experimental
            # So I have elected to remove it until further testing necessitates it more than the expected cli call.

            # Run vermin analysis
            # ver = v
            #
            # # Get minimum version
            # min_versions = ver.minimum_versions()
            #
            # if min_versions and min_versions[0]:
            #     # vermin returns versions as tuples like (3, 8)
            #     version = f"{min_versions[0][0]}.{min_versions[0][1]}"
            #     return version, 'vermin'
            # else:
            #     return '3.11', 'vermin-default'

        except Exception as e:
            print(f"Warning: Vermin analysis failed: {e}", file=sys.stderr)
            return self._detect_fallback()
    
    def _detect_fallback(self) -> Tuple[str, str]:
        """Fallback version detection using AST analysis."""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            min_version = self._analyze_ast_features(tree)
            return min_version, 'ast-analysis'
            
        except Exception as e:
            print(f"Warning: AST analysis failed: {e}", file=sys.stderr)
            return '3.11', 'default'
    
    def _analyze_ast_features(self, tree: ast.AST) -> str:
        """Analyze AST for Python version-specific features."""
        # Check for Python 3.10+ features
        for node in ast.walk(tree):
            # Match statement (3.10+)
            if isinstance(node, ast.Match):
                return '3.10'
            
            # Positional-only parameters with defaults (3.8+)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.args.posonlyargs:
                    return '3.8'
            
            # Walrus operator := (3.8+)
            if isinstance(node, ast.NamedExpr):
                return '3.8'
        
        # Check for f-string with = (3.8+)
        with open(self.filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if re.search(r'f["\'].*\{[^}]+=\}', content):
                return '3.8'
        
        # Default to 3.7 if no specific features detected
        return '3.7'
    
    def _find_local_imports(self) -> List[str]:
        """Find local Python files imported by the main file."""
        local_imports = []
        base_dir = self.filepath.parent
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.level > 0:  # Relative import
                        continue
                    
                    if node.module:
                        # Check if it's a local module
                        module_path = base_dir / f"{node.module.replace('.', '/')}.py"
                        if module_path.exists():
                            local_imports.append(str(module_path))
                        
                        # Also check for package
                        package_path = base_dir / node.module.replace('.', '/') / '__init__.py'
                        if package_path.exists():
                            local_imports.append(str(package_path))
                            
        except Exception as e:
            print(f"Warning: Could not scan local imports: {e}", file=sys.stderr)
        
        return local_imports


class PythonFileAnalyzer:
    """Analyzes Python files to extract metadata for Dockerfile generation."""
    
    def __init__(self, filepath: str, scan_imports_for_version: bool = False):
        self.filepath = Path(filepath)
        self.imports: Set[str] = set()
        self.python_version: Optional[str] = None
        self.requirements: List[str] = []
        self.scan_imports_for_version = scan_imports_for_version
        
    def analyze(self) -> Dict:
        """Analyze the Python file and return metadata."""
        if not self.filepath.exists():
            raise FileNotFoundError(f"File not found: {self.filepath}")
        
        with open(self.filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse imports
        self.imports = self._extract_imports(content)
        
        # Detect minimum Python version
        version_detector = PythonVersionDetector(str(self.filepath))
        detected_version, detection_method = version_detector.detect_version(
            scan_imports=self.scan_imports_for_version
        )
        self.python_version = detected_version
        
        # Check for requirements.txt
        self._check_requirements_file()
        
        # Detect if it's a Flask/Django/FastAPI app
        app_type = self._detect_app_type()
        
        # Determine if file is executable (has main guard)
        is_executable = self._is_executable(content)
        
        return {
            'imports': self.imports,
            'requirements': self.requirements,
            'python_version': self.python_version,
            'version_detection_method': detection_method,
            'app_type': app_type,
            'is_executable': is_executable,
            'filename': self.filepath.name
        }
    
    def _extract_imports(self, content: str) -> Set[str]:
        """Extract import statements from Python code."""
        imports = set()
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Get top-level package name
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
        except SyntaxError:
            # Fallback to regex if AST parsing fails
            import_pattern = r'^\s*(?:from\s+(\S+)|import\s+(\S+))'
            for match in re.finditer(import_pattern, content, re.MULTILINE):
                module = match.group(1) or match.group(2)
                imports.add(module.split('.')[0])
        
        # Filter out standard library modules
        stdlib_modules = self._get_stdlib_modules()
        return {imp for imp in imports if imp not in stdlib_modules}
    
    def _get_stdlib_modules(self) -> Set[str]:
        """Return a set of common standard library module names."""
        return {
            'os', 'sys', 'json', 'math', 're', 'time', 'datetime', 'random',
            'collections', 'itertools', 'functools', 'pathlib', 'typing',
            'logging', 'unittest', 'argparse', 'subprocess', 'threading',
            'multiprocessing', 'asyncio', 'io', 'pickle', 'csv', 'sqlite3',
            'http', 'urllib', 'email', 'html', 'xml', 'hashlib', 'base64',
            'shutil', 'glob', 'tempfile', 'warnings', 'abc', 'dataclasses',
            'enum', 'decimal', 'fractions', 'statistics', 'secrets', 'uuid',
            'copy', 'pprint', 'textwrap', 'codecs', 'struct', 'array'
        }
    
    def _check_requirements_file(self):
        """Check for requirements.txt in the same directory."""
        req_file = self.filepath.parent / 'requirements.txt'
        if req_file.exists():
            # We can't guarantee utf-8. Find a better way.
            with open(req_file, 'r', encoding='utf-8') as f:
                self.requirements = [
                    line.strip() for line in f 
                    if line.strip() and not line.startswith('#')
                ]
    
    def _detect_app_type(self) -> str:
        """Detect the type of Python application."""
        if 'flask' in self.imports:
            return 'flask'
        elif 'django' in self.imports:
            return 'django'
        elif 'fastapi' in self.imports:
            return 'fastapi'
        elif 'streamlit' in self.imports:
            return 'streamlit'
        else:
            return 'script'
    
    def _is_executable(self, content: str) -> bool:
        """Check if the file has a main execution guard."""
        return bool(re.search(r'if\s+__name__\s*==\s*["\']__main__["\']', content))


class DockerfileGenerator:
    """Generates Dockerfiles based on Python file analysis."""
    
    def __init__(self, metadata: Dict):
        self.metadata = metadata
        
    def generate(self) -> str:
        """Generate the Dockerfile content."""
        dockerfile_lines = []
        
        # Base image
        python_version = self.metadata['python_version']
        detection_method = self.metadata.get('version_detection_method', 'default')
        
        dockerfile_lines.append(f"# Use official Python runtime as base image")
        dockerfile_lines.append(f"# Python version {python_version} detected via {detection_method}")
        dockerfile_lines.append(f"FROM python:{python_version}-slim")
        dockerfile_lines.append("")
        
        # Set working directory
        dockerfile_lines.append("# Set working directory")
        dockerfile_lines.append("WORKDIR /app")
        dockerfile_lines.append("")
        
        # Environment variables
        dockerfile_lines.append("# Prevent Python from writing pyc files and buffering stdout/stderr")
        dockerfile_lines.append("ENV PYTHONDONTWRITEBYTECODE=1")
        dockerfile_lines.append("ENV PYTHONUNBUFFERED=1")
        dockerfile_lines.append("")
        
        # System dependencies (if needed)
        if self._needs_system_deps():
            dockerfile_lines.append("# Install system dependencies")
            dockerfile_lines.append("RUN apt-get update && apt-get install -y \\")
            dockerfile_lines.append("    gcc \\")
            dockerfile_lines.append("    && rm -rf /var/lib/apt/lists/*")
            dockerfile_lines.append("")
        
        # Copy and install requirements
        if self.metadata['requirements']:
            dockerfile_lines.append("# Copy requirements file")
            dockerfile_lines.append("COPY requirements.txt .")
            dockerfile_lines.append("")
            dockerfile_lines.append("# Install Python dependencies")
            dockerfile_lines.append("RUN pip install --no-cache-dir -r requirements.txt")
            dockerfile_lines.append("")
        elif self.metadata['imports']:
            dockerfile_lines.append("# Install Python dependencies")
            packages = ' '.join(sorted(self.metadata['imports']))
            dockerfile_lines.append(f"RUN pip install --no-cache-dir {packages}")
            dockerfile_lines.append("")
        
        # Copy application code
        dockerfile_lines.append("# Copy application code")
        dockerfile_lines.append("COPY . .")
        dockerfile_lines.append("")
        
        # Expose port (for web apps)
        app_type = self.metadata['app_type']
        if app_type in ['flask', 'django', 'fastapi', 'streamlit']:
            port = self._get_default_port(app_type)
            dockerfile_lines.append(f"# Expose port")
            dockerfile_lines.append(f"EXPOSE {port}")
            dockerfile_lines.append("")
        
        # CMD instruction
        dockerfile_lines.append("# Run the application")
        cmd = self._generate_cmd()
        dockerfile_lines.append(f"CMD {cmd}")
        
        return '\n'.join(dockerfile_lines)
    
    def _needs_system_deps(self) -> bool:
        """Check if system dependencies are needed."""
        # Packages that typically require compilation
        compile_packages = {'numpy', 'pandas', 'pillow', 'psycopg2', 'mysqlclient', 'lxml'}
        return bool(self.metadata['imports'] & compile_packages)
    
    def _get_default_port(self, app_type: str) -> int:
        """Get default port for web framework."""
        ports = {
            'flask': 5000,
            'django': 8000,
            'fastapi': 8000,
            'streamlit': 8501
        }
        return ports.get(app_type, 8000)
    
    def _generate_cmd(self) -> str:
        """Generate the CMD instruction based on app type."""
        app_type = self.metadata['app_type']
        filename = self.metadata['filename']
        
        if app_type == 'flask':
            return f'["python", "{filename}"]'
        elif app_type == 'django':
            return '["python", "manage.py", "runserver", "0.0.0.0:8000"]'
        elif app_type == 'fastapi':
            module_name = filename.replace('.py', '')
            return f'["uvicorn", "{module_name}:app", "--host", "0.0.0.0", "--port", "8000"]'
        elif app_type == 'streamlit':
            return f'["streamlit", "run", "{filename}", "--server.port=8501", "--server.address=0.0.0.0"]'
        else:
            # For regular scripts
            if self.metadata['is_executable']:
                return f'["python", "{filename}"]'
            else:
                return f'["python", "-c", "print(\\"Application ready\\")"]'


def generate_dockerfile(
    python_file: str, 
    output_file: str = 'Dockerfile',
    scan_imports: bool = False
) -> str:
    """
    Main function to generate a Dockerfile for a Python file.
    
    Args:
        python_file: Path to the Python file to analyze
        output_file: Path where the Dockerfile should be written
        scan_imports: If True, scan imported local modules for version requirements
        
    Returns:
        The generated Dockerfile content
    """
    print(f"Analyzing Python file: {python_file}")
    
    # Check if vermin is available
    try:
        import vermin
        print("✓ Using vermin for Python version detection")
    except ImportError:
        print("ℹ Vermin not installed - using fallback version detection")
        print("  Install with: pip install vermin")
    
    # Analyze the Python file
    analyzer = PythonFileAnalyzer(python_file, scan_imports_for_version=scan_imports)
    metadata = analyzer.analyze()
    
    print(f"Detected imports: {', '.join(sorted(metadata['imports'])) or 'None'}")
    print(f"Application type: {metadata['app_type']}")
    print(f"Python version: {metadata['python_version']} (detected via {metadata['version_detection_method']})")
    
    # Generate Dockerfile
    generator = DockerfileGenerator(metadata)
    dockerfile_content = generator.generate()
    
    # Write to file
    output_path = Path(python_file).parent / output_file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(dockerfile_content)
    
    print(f"\n✓ Dockerfile generated successfully: {output_path}")
    
    return dockerfile_content


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate Dockerfiles for Python applications with automatic version detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s app.py
  %(prog)s app.py --output custom_Dockerfile
  %(prog)s app.py --scan-imports
  
The tool will automatically detect the minimum Python version required
using vermin if installed, otherwise it will use fallback detection.
        """
    )
    
    parser.add_argument(
        'python_file',
        help='Path to the Python file to analyze'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='Dockerfile',
        help='Output Dockerfile path (default: Dockerfile)'
    )
    
    parser.add_argument(
        '-s', '--scan-imports',
        action='store_true',
        help='Scan local imported modules for version requirements (requires vermin)'
    )
    
    args = parser.parse_args()
    
    try:
        dockerfile_content = generate_dockerfile(
            args.python_file, 
            args.output,
            scan_imports=args.scan_imports
        )
        print("\n" + "="*50)
        print("Generated Dockerfile:")
        print("="*50)
        print(dockerfile_content)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
