#!/usr/bin/env python3
"""
Dockerfile Database API

FastAPI application providing REST API access to the Dockerfile database.
"""
import sqlite3

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
import uvicorn

from dockerfile_database import DockerfileDatabase


# Pydantic models for request/response validation
class DockerfileCreate(BaseModel):
    """Model for creating a new Dockerfile entry."""
    name: str = Field(..., description="Name of the Dockerfile", example="Dockerfile.flask")
    content: str = Field(..., description="Full content of the Dockerfile")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Dockerfile.flask",
                "content": "FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nCMD [\"python\", \"app.py\"]"
            }
        }


class DockerfileResponse(BaseModel):
    """Model for Dockerfile response."""
    id: int
    name: str
    content: str
    created_date: str
    created_time: str
    created_timestamp: str
    timezone: str
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Dockerfile.flask",
                "content": "FROM python:3.11-slim\n...",
                "created_date": "2026-02-08",
                "created_time": "14:30:00",
                "created_timestamp": "2026-02-08T14:30:00+00:00",
                "timezone": "UTC"
            }
        }


class DockerfileListResponse(BaseModel):
    """Model for list of Dockerfiles response."""
    count: int
    dockerfiles: List[DockerfileResponse]


class DatabaseStats(BaseModel):
    """Model for database statistics."""
    total_dockerfiles: int
    unique_dates: int
    unique_names: int


class MessageResponse(BaseModel):
    """Model for simple message responses."""
    message: str
    details: Optional[dict] = None


# Initialize FastAPI app
app = FastAPI(
    title="Dockerfile Database API",
    description="REST API for storing and retrieving Dockerfiles with timestamp tracking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# Database instance (singleton pattern)
db = DockerfileDatabase()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    print("✓ Dockerfile Database API started")
    print(f"✓ Database file: {db.db_path}")
    stats = db.get_statistics()
    print(f"✓ Current entries: {stats['total_dockerfiles']}")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    db.close()
    print("✓ Database connection closed")


# API Endpoints

@app.get("/", response_model=MessageResponse)
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Dockerfile Database API",
        "details": {
            "version": "1.0.0",
            "endpoints": {
                "docs": "/docs",
                "health": "/health",
                "stats": "/stats",
                "dockerfiles": "/dockerfiles"
            }
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        stats = db.get_statistics()
        return {
            "status": "healthy",
            "database": "connected",
            "total_entries": stats['total_dockerfiles']
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database health check failed: {str(e)}"
        )


@app.get("/stats", response_model=DatabaseStats)
async def get_statistics():
    """
    Get database statistics.
    
    Returns:
        Statistics including total Dockerfiles, unique dates, and unique names
    """
    try:
        stats = db.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


@app.get("/dockerfiles", response_model=DockerfileListResponse)
async def get_all_dockerfiles():
    """
    Retrieve all Dockerfiles from the database.
    
    Returns:
        List of all Dockerfile entries with metadata
    """
    try:
        dockerfiles = db.get_all_dockerfiles()
        return {
            "count": len(dockerfiles),
            "dockerfiles": dockerfiles
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Dockerfiles: {str(e)}"
        )


@app.get("/dockerfiles/dates", response_model=List[str])
async def get_unique_dates():
    """
    Get all unique dates that have Dockerfiles stored.
    
    Returns:
        List of dates in ISO format (YYYY-MM-DD)
    """
    try:
        dates = db.get_unique_dates()
        return dates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dates: {str(e)}"
        )


@app.get("/dockerfiles/by-date/{date}", response_model=DockerfileListResponse)
# str = Query(
#         ...,
#         description="Date in ISO format (YYYY-MM-DD)",
#         example="2026-02-08"
#     )
async def get_dockerfiles_by_date(
    date: str
):
    """
    Retrieve all Dockerfiles stored on a specific date.
    
    Args:
        date: Date in ISO format (YYYY-MM-DD)
        
    Returns:
        List of Dockerfiles stored on the specified date
    """
    # Validate date format
    try:
        datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    try:
        dockerfiles = db.get_dockerfiles_by_date(date)
        return {
            "count": len(dockerfiles),
            "dockerfiles": dockerfiles
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Dockerfiles: {str(e)}"
        )


@app.get("/dockerfiles/by-date/{date}/names", response_model=List[str])
# = Query(
#         ...,
#         description="Date in ISO format (YYYY-MM-DD)",
#         example="2026-02-08"
#     )
async def get_dockerfile_names_by_date(
    date: str
):
    """
    Get all Dockerfile names for a specific date.
    
    Args:
        date: Date in ISO format (YYYY-MM-DD)
        
    Returns:
        List of Dockerfile names stored on the specified date
    """
    # Validate date format
    try:
        datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    try:
        names = db.get_dockerfile_names_by_date(date)
        return names
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Dockerfile names: {str(e)}"
        )


@app.get("/dockerfiles/by-date/{date}/{name}", response_model=DockerfileResponse)
# = Query(
#         ...,
#         description="Date in ISO format (YYYY-MM-DD)",
#         example="2026-02-08"
#     ),
# = Query(
#         ...,
#         description="Name of the Dockerfile",
#         example="Dockerfile.flask"
#     )
async def get_dockerfile_by_date_and_name(
    date: str,
    name: str
):
    """
    Retrieve a specific Dockerfile by date and name.
    
    Args:
        date: Date in ISO format (YYYY-MM-DD)
        name: Name of the Dockerfile
        
    Returns:
        Dockerfile entry with full content and metadata
    """
    # Validate date format
    try:
        datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    try:
        dockerfile = db.get_dockerfile_by_date_and_name(date, name)
        
        if not dockerfile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dockerfile '{name}' not found for date {date}"
            )
        
        return dockerfile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Dockerfile: {str(e)}"
        )


@app.get("/dockerfiles/by-date/{date}/{name}/content", response_class=PlainTextResponse)
# = Query(
#         ...,
#         description="Date in ISO format (YYYY-MM-DD)",
#         example="2026-02-08"
#     )
# = Query(
#         ...,
#         description="Name of the Dockerfile",
#         example="Dockerfile.flask"
#     )
async def get_dockerfile_content(
    date: str,
    name: str
):
    """
    Retrieve only the content of a specific Dockerfile (as plain text).
    
    Args:
        date: Date in ISO format (YYYY-MM-DD)
        name: Name of the Dockerfile
        
    Returns:
        Plain text content of the Dockerfile
    """
    # Validate date format
    try:
        datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    try:
        dockerfile = db.get_dockerfile_by_date_and_name(date, name)
        
        if not dockerfile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dockerfile '{name}' not found for date {date}"
            )
        
        return dockerfile['content']
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Dockerfile content: {str(e)}"
        )


@app.post("/dockerfiles", response_model=DockerfileResponse, status_code=status.HTTP_201_CREATED)
async def create_dockerfile(dockerfile: DockerfileCreate):
    """
    Add a new Dockerfile to the database.
    
    This endpoint provides the basis for external database integration.
    When connecting an external database in the future, this POST endpoint
    can be modified to store data in the external system.
    
    Args:
        dockerfile: Dockerfile data including name and content
        
    Returns:
        Created Dockerfile entry with metadata
    """
    try:
        result = db.add_dockerfile(
            name=dockerfile.name,
            content=dockerfile.content
        )
        
        # Retrieve the full entry
        full_entry = db.get_dockerfile_by_date_and_name(
            result['created_date'],
            result['name']
        )
        
        return full_entry
    
    except Exception as e:
        # Check if it's a duplicate entry error
        if "UNIQUE constraint failed" in str(e) or "Duplicate" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Dockerfile '{dockerfile.name}' already exists at this timestamp"
            )
        elif isinstance(e, sqlite3.DataError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Dockerfile with no name is not allowed to exist in the database."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create Dockerfile: {str(e)}"
            )


@app.delete("/dockerfiles/{dockerfile_id}", response_model=MessageResponse)
async def delete_dockerfile(dockerfile_id: int):
    """
    Delete a Dockerfile by its ID.
    
    Args:
        dockerfile_id: The ID of the Dockerfile to delete
        
    Returns:
        Confirmation message
    """
    try:
        deleted = db.delete_dockerfile(dockerfile_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dockerfile with ID {dockerfile_id} not found"
            )
        
        return {
            "message": f"Dockerfile with ID {dockerfile_id} deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete Dockerfile: {str(e)}"
        )


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"message": "Resource not found", "path": str(request.url)}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "detail": str(exc)}
    )


def run_api(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Run the FastAPI application.
    
    Args:
        host: Host address to bind to
        port: Port to listen on
        reload: Enable auto-reload for development
    """
    uvicorn.run(
        "dockerfile_api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == '__main__':
    run_api(reload=True)
