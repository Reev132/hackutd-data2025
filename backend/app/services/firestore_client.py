"""
Firestore client dependency injection for FastAPI.

This module provides the dependency function to inject Firestore client
into FastAPI route handlers.
"""

from firebase_admin import firestore
from app.services.firebase_service import get_firestore_client


def get_db() -> firestore.Client:
    """
    Dependency function to inject Firestore client into route handlers.

    This replaces the old SQLAlchemy session dependency.

    Usage in FastAPI routes:
        @router.get("/")
        def list_items(db: firestore.Client = Depends(get_db)):
            ...

    Returns:
        firestore.Client: Firestore client instance

    Raises:
        RuntimeError: If Firebase has not been initialized
    """
    return get_firestore_client()
