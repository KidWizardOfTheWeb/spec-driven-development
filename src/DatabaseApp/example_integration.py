#!/usr/bin/env python3
"""
Example: Complete Integration

This example demonstrates how to:
1. Generate a Dockerfile using dockerfile_generator_v2
2. Store it in the database
3. Retrieve it via API
"""

import sys
from pathlib import Path

# Import our modules
from dockerfile_generator_v2 import generate_dockerfile
from dockerfile_database import DockerfileDatabase


def example_complete_workflow():
    """Complete workflow from generation to storage to retrieval."""
    
    print("="*70)
    print("Dockerfile Generator + Database Integration Example")
    print("="*70)
    
    # Step 1: Generate a Dockerfile
    print("\n[Step 1] Generating Dockerfile from Python file...")
    
    # Create a sample Python file
    sample_app = Path("sample_app.py")
    sample_app.write_text("""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({'status': 'running'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
""")
    
    # Generate Dockerfile
    dockerfile_path = "Dockerfile.sample_app"
    dockerfile_content = generate_dockerfile(
        str(sample_app),
        dockerfile_path
    )
    
    print(f"✓ Generated: {dockerfile_path}")
    
    # Step 2: Store in database
    print("\n[Step 2] Storing Dockerfile in database...")
    
    with DockerfileDatabase() as db:
        # Add to database
        result = db.add_dockerfile_from_file(dockerfile_path)
        
        # Verify storage
        stored_date = result['created_date']
        stored_name = result['name']
        
        print(f"\n✓ Stored in database")
        print(f"  Date: {stored_date}")
        print(f"  Name: {stored_name}")
        
        # Step 3: Retrieve from database
        print("\n[Step 3] Retrieving from database...")
        
        # Retrieve by date
        dockerfiles_today = db.get_dockerfiles_by_date(stored_date)
        print(f"\n✓ Found {len(dockerfiles_today)} Dockerfile(s) for {stored_date}")
        
        # Retrieve specific Dockerfile
        retrieved = db.get_dockerfile_by_date_and_name(stored_date, stored_name)
        
        if retrieved:
            print(f"\n✓ Retrieved: {retrieved['name']}")
            print(f"\nContent preview:")
            print("-" * 50)
            print(retrieved['content'][:200] + "...")
            print("-" * 50)
        
        # Step 4: Show statistics
        print("\n[Step 4] Database Statistics...")
        stats = db.get_statistics()
        print(f"\n  Total Dockerfiles: {stats['total_dockerfiles']}")
        print(f"  Unique Dates: {stats['unique_dates']}")
        print(f"  Unique Names: {stats['unique_names']}")
    
    print("\n" + "="*70)
    print("✓ Complete workflow finished successfully!")
    print("="*70)
    
    # Cleanup
    sample_app.unlink()
    Path(dockerfile_path).unlink()


def example_batch_storage():
    """Example of storing multiple Dockerfiles at once."""
    
    print("\n" + "="*70)
    print("Batch Storage Example")
    print("="*70)
    
    # Sample Dockerfiles
    dockerfiles = {
        "Dockerfile.flask": """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]""",
        
        "Dockerfile.django": """FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]""",
        
        "Dockerfile.fastapi": """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]"""
    }
    
    with DockerfileDatabase() as db:
        print(f"\nStoring {len(dockerfiles)} Dockerfiles...")
        
        for name, content in dockerfiles.items():
            try:
                db.add_dockerfile(name, content)
            except Exception as e:
                print(f"  ⚠ Warning: Could not store {name}: {e}")
        
        # Show what was stored
        print("\n" + "="*70)
        dates = db.get_unique_dates()
        
        for date in dates[:3]:  # Show latest 3 dates
            dockerfiles = db.get_dockerfiles_by_date(date)
            print(f"\n{date} ({len(dockerfiles)} Dockerfile(s)):")
            for df in dockerfiles:
                print(f"  • {df['name']} - {df['created_time']}")


def example_search_and_filter():
    """Example of searching and filtering Dockerfiles."""
    
    print("\n" + "="*70)
    print("Search and Filter Example")
    print("="*70)
    
    with DockerfileDatabase() as db:
        # Get all unique dates
        dates = db.get_unique_dates()
        
        if not dates:
            print("\nNo Dockerfiles in database yet!")
            return
        
        # Show latest date
        latest_date = dates[0]
        print(f"\nLatest date with Dockerfiles: {latest_date}")
        
        # Get all names for that date
        names = db.get_dockerfile_names_by_date(latest_date)
        print(f"\nDockerfiles on {latest_date}:")
        for name in names:
            print(f"  • {name}")
        
        # Filter by name pattern
        print("\nFiltering for Flask Dockerfiles:")
        for date in dates:
            names = db.get_dockerfile_names_by_date(date)
            flask_files = [n for n in names if 'flask' in n.lower()]
            
            if flask_files:
                print(f"\n  {date}:")
                for name in flask_files:
                    print(f"    • {name}")


def example_api_client():
    """Example of using the API with requests library."""
    
    print("\n" + "="*70)
    print("API Client Example")
    print("="*70)
    
    try:
        import requests
    except ImportError:
        print("\n⚠ requests library not installed")
        print("Install with: pip install requests")
        return
    
    API_URL = "http://localhost:8000"
    
    print(f"\nConnecting to API at {API_URL}...")
    
    try:
        # Health check
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✓ API is healthy")
        
        # Get statistics
        response = requests.get(f"{API_URL}/stats")
        stats = response.json()
        print(f"\nDatabase Statistics:")
        print(f"  Total: {stats['total_dockerfiles']}")
        print(f"  Dates: {stats['unique_dates']}")
        print(f"  Names: {stats['unique_names']}")
        
        # Create a new Dockerfile via API
        new_dockerfile = {
            "name": "Dockerfile.api_test",
            "content": "FROM python:3.11\nWORKDIR /app\nCOPY . ."
        }
        
        print("\nCreating Dockerfile via API...")
        response = requests.post(f"{API_URL}/dockerfiles", json=new_dockerfile)
        
        if response.status_code == 201:
            result = response.json()
            print(f"✓ Created: {result['name']}")
            print(f"  ID: {result['id']}")
            print(f"  Date: {result['created_date']}")
        
    except requests.exceptions.ConnectionError:
        print("\n⚠ Cannot connect to API")
        print("Start the API server with: python dockerfile_api.py")
    except Exception as e:
        print(f"\n⚠ Error: {e}")


def main():
    """Run all examples."""
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
        
        if example == "workflow":
            example_complete_workflow()
        elif example == "batch":
            example_batch_storage()
        elif example == "search":
            example_search_and_filter()
        elif example == "api":
            example_api_client()
        else:
            print(f"Unknown example: {example}")
            print("Available: workflow, batch, search, api")
    else:
        # Run all examples
        example_complete_workflow()
        example_batch_storage()
        example_search_and_filter()
        example_api_client()


if __name__ == '__main__':
    main()
