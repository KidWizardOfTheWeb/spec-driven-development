#!/usr/bin/env python3
"""
Test Runner for Dockerfile Database System

Provides convenient commands for running different test suites.
"""

import sys
import subprocess


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
Dockerfile Database Test Runner

Usage: python run_database_tests.py [command]

Commands:
    all         - Run all tests with coverage
    unit        - Run only unit tests
    integration - Run only integration tests
    database    - Run database tests
    api         - Run API tests
    fast        - Run tests without slow tests
    verbose     - Run with verbose output
    coverage    - Run with HTML coverage report
    specific    - Run a specific test file or function
    failed      - Re-run only failed tests
    
Examples:
    python run_database_tests.py all
    python run_database_tests.py api
    python run_database_tests.py specific test_dockerfile_api.py::TestCreateDockerfile
        """)
        return 1
    
    command = sys.argv[1]
    
    # Base pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    
    if command == "all":
        return run_command(
            pytest_cmd + [
                "-v",
                "--cov=dockerfile_database",
                "--cov=dockerfile_api",
                "--cov-report=term-missing"
            ],
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
    
    elif command == "database":
        return run_command(
            pytest_cmd + ["-v", "test_dockerfile_database.py"],
            "Database tests only"
        )
    
    elif command == "api":
        return run_command(
            pytest_cmd + ["-v", "test_dockerfile_api.py"],
            "API tests only"
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
        retcode = run_command(
            pytest_cmd + [
                "-v",
                "--cov=dockerfile_database",
                "--cov=dockerfile_api",
                "--cov-report=html",
                "--cov-report=term-missing"
            ],
            "Tests with HTML coverage report"
        )
        if retcode == 0:
            print("\n✓ Coverage report generated at: htmlcov/index.html")
        return retcode
    
    elif command == "specific":
        if len(sys.argv) < 3:
            print("Error: Please specify test file or function")
            print("Example: python run_database_tests.py specific test_dockerfile_api.py::test_function")
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
