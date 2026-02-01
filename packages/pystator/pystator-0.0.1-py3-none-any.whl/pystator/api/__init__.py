"""
PyStator API Package

REST API for FSM operations using PyStator.

Usage:
    # Run development server
    uvicorn pystator.api.main:app --reload

    # Access documentation
    http://localhost:8000/docs        # Swagger UI
    http://localhost:8000/redoc        # ReDoc
"""

from pystator.api.main import app, create_application

__all__ = ["app", "create_application"]
