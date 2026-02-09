#!/usr/bin/env python3
"""
Quick Start Script for Dockerfile Database System

This script helps you get started with the database system quickly.
"""

import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(text)
    print("="*70 + "\n")


def check_dependencies():
    """Check if required dependencies are installed."""
    print_header("Checking Dependencies")
    
    required = {
        'fastapi': 'FastAPI web framework',
        'uvicorn': 'ASGI server',
        'pytz': 'Timezone handling',
        'pydantic': 'Data validation'
    }
    
    missing = []
    
    for package, description in required.items():
        try:
            __import__(package)
            print(f"✓ {package:15} - {description}")
        except ImportError:
            print(f"✗ {package:15} - {description} (MISSING)")
            missing.append(package)
    
    if missing:
        print("\n⚠ Missing dependencies detected!")
        print("Install with: pip install -r requirements-database.txt")
        return False
    
    print("\n✓ All dependencies installed!")
    return True


def create_sample_dockerfile():
    """Create a sample Dockerfile for testing."""
    sample_content = """# Sample Flask Dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
"""
    
    sample_path = Path("Dockerfile.sample")
    sample_path.write_text(sample_content)
    return sample_path


def demo_database():
    """Run a quick database demo."""
    print_header("Database Demo")
    
    from dockerfile_database import DockerfileDatabase
    
    # Create sample Dockerfile
    sample_path = create_sample_dockerfile()
    print(f"✓ Created sample Dockerfile: {sample_path}")
    
    # Initialize database
    db = DockerfileDatabase("demo.db")
    print("✓ Initialized database: demo.db")
    
    # Add Dockerfile
    print("\n📝 Adding Dockerfile to database...")
    result = db.add_dockerfile_from_file(str(sample_path))
    
    # Retrieve it back
    print("\n🔍 Retrieving Dockerfile...")
    retrieved = db.get_dockerfile_by_date_and_name(
        result['created_date'],
        result['name']
    )
    
    if retrieved:
        print(f"✓ Successfully retrieved: {retrieved['name']}")
        print(f"\nFirst 3 lines:")
        lines = retrieved['content'].split('\n')[:3]
        for line in lines:
            print(f"  {line}")
    
    # Statistics
    stats = db.get_statistics()
    print(f"\n📊 Database Statistics:")
    print(f"  Total Dockerfiles: {stats['total_dockerfiles']}")
    
    db.close()
    
    # Cleanup
    sample_path.unlink()
    print("\n✓ Demo completed!")
    print(f"  Database saved to: demo.db")


def demo_api():
    """Run API server demo."""
    print_header("API Server Demo")
    
    print("Starting API server...")
    print("Once started, you can:")
    print("  • View docs at: http://localhost:8000/docs")
    print("  • View health at: http://localhost:8000/health")
    print("  • View stats at: http://localhost:8000/stats")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        subprocess.run([
            sys.executable, "dockerfile_api.py"
        ])
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")


def show_usage():
    """Show usage examples."""
    print_header("Usage Examples")
    
    print("1. Interactive Database Manager:")
    print("   python dockerfile_database.py")
    
    print("\n2. API Server:")
    print("   python dockerfile_api.py")
    
    print("\n3. Python API:")
    print("""
   from dockerfile_database import DockerfileDatabase
   
   with DockerfileDatabase() as db:
       db.add_dockerfile_from_file('Dockerfile')
       dockerfiles = db.get_all_dockerfiles()
   """)
    
    print("\n4. REST API (with curl):")
    print("""
   # Get all Dockerfiles
   curl http://localhost:8000/dockerfiles
   
   # Get by date
   curl http://localhost:8000/dockerfiles/by-date/2026-02-08
   
   # Create new Dockerfile
   curl -X POST http://localhost:8000/dockerfiles \\
     -H "Content-Type: application/json" \\
     -d '{"name": "Dockerfile.test", "content": "FROM python:3.11"}'
   """)


def main():
    """Main quick start function."""
    print_header("Dockerfile Database Quick Start")
    
    if len(sys.argv) < 2:
        print("Usage: python quickstart.py [command]")
        print("\nCommands:")
        print("  check     - Check if dependencies are installed")
        print("  demo-db   - Run database demo")
        print("  demo-api  - Start API server demo")
        print("  usage     - Show usage examples")
        print("  all       - Run all checks and demos")
        return
    
    command = sys.argv[1]
    
    if command == "check":
        check_dependencies()
    
    elif command == "demo-db":
        if check_dependencies():
            demo_database()
    
    elif command == "demo-api":
        if check_dependencies():
            demo_api()
    
    elif command == "usage":
        show_usage()
    
    elif command == "all":
        if check_dependencies():
            demo_database()
            print("\n" + "="*70)
            response = input("\nStart API server demo? (y/n): ")
            if response.lower() == 'y':
                demo_api()
            show_usage()
    
    else:
        print(f"Unknown command: {command}")
        print("Run without arguments to see available commands")


if __name__ == '__main__':
    main()
