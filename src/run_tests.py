#!/usr/bin/env python3
"""
Test runner script for Dockerfile Generator
Provides convenient commands for running tests with different configurations.
"""

import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print its description."""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*70}\n")
    
    result = subprocess.run(cmd)
    return result.returncode


def main():
    """Main test runner."""
    if len(sys.argv) < 2:
        print("""
Dockerfile Generator Test Runner

Usage: python run_tests.py [command]

Commands:
    all         - Run all tests with coverage
    unit        - Run only unit tests
    integration - Run only integration tests
    fast        - Run tests without slow tests
    verbose     - Run with verbose output
    coverage    - Run with coverage report
    html        - Generate HTML coverage report
    watch       - Run tests in watch mode (requires pytest-watch)
    specific    - Run a specific test file or function
    
Examples:
    python run_tests.py all
    python run_tests.py unit
    python run_tests.py verbose
    python run_tests.py specific test_dockerfile_generator.py::TestPythonVersionDetector
        """)
        return 1
    
    command = sys.argv[1]
    
    # Base pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    
    if command == "all":
        return run_command(
            pytest_cmd + ["-v", "--cov=dockerfile_generator_v2", "--cov-report=term-missing"],
            "All tests with coverage"
        )
    
    elif command == "unit":
        return run_command(
            pytest_cmd + ["-v", "-m", "unit"],
            "Unit tests only"
        )
    
    elif command == "integration":
        return run_command(
            pytest_cmd + ["-v", "-m", "integration"],
            "Integration tests only"
        )
    
    elif command == "fast":
        return run_command(
            pytest_cmd + ["-v", "-m", "not slow"],
            "Fast tests (excluding slow tests)"
        )
    
    elif command == "verbose":
        return run_command(
            pytest_cmd + ["-vv", "-s"],
            "Verbose output with print statements"
        )
    
    elif command == "coverage":
        return run_command(
            pytest_cmd + [
                "-v",
                "--cov=dockerfile_generator_v2",
                "--cov-report=term-missing",
                "--cov-report=html"
            ],
            "Tests with detailed coverage report"
        )
    
    elif command == "html":
        retcode = run_command(
            pytest_cmd + [
                "--cov=dockerfile_generator_v2",
                "--cov-report=html"
            ],
            "Generate HTML coverage report"
        )
        if retcode == 0:
            print("\n✓ Coverage report generated at: htmlcov/index.html")
        return retcode
    
    elif command == "watch":
        try:
            return run_command(
                ["ptw", "--", "-v"],
                "Watch mode (re-run tests on file changes)"
            )
        except FileNotFoundError:
            print("Error: pytest-watch not installed")
            print("Install with: pip install pytest-watch")
            return 1
    
    elif command == "specific":
        if len(sys.argv) < 3:
            print("Error: Please specify test file or function")
            print("Example: python run_tests.py specific test_dockerfile_generator.py::test_function")
            return 1
        
        return run_command(
            pytest_cmd + ["-v", sys.argv[2]],
            f"Specific test: {sys.argv[2]}"
        )
    
    elif command == "failed":
        return run_command(
            pytest_cmd + ["-v", "--lf"],
            "Re-run only failed tests"
        )
    
    elif command == "markers":
        return run_command(
            pytest_cmd + ["--markers"],
            "Show available test markers"
        )
    
    else:
        print(f"Unknown command: {command}")
        print("Run without arguments to see available commands")
        return 1


if __name__ == "__main__":
    sys.exit(main())
