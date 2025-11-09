"""
Firebase Admin SDK initialization and configuration.

This module initializes the Firebase Admin SDK and provides access to Firestore.
The service account credentials should be stored in firebase-credentials.json
at the backend root directory.
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional

# Global Firebase app instance
_firebase_app: Optional[firebase_admin.App] = None


def initialize_firebase() -> firebase_admin.App:
    """
    Initialize Firebase Admin SDK with service account credentials.

    This should be called once at application startup.

    Returns:
        firebase_admin.App: The initialized Firebase app instance

    Raises:
        FileNotFoundError: If credentials file is not found
        ValueError: If Firebase is already initialized with different credentials
    """
    global _firebase_app

    if _firebase_app is not None:
        return _firebase_app

    # Path to service account key file
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    cred_path = os.path.join(backend_dir, "firebase-credentials.json")

    if not os.path.exists(cred_path):
        raise FileNotFoundError(
            f"Firebase credentials not found at {cred_path}. "
            "Please download your service account key from Firebase Console "
            "and save it as firebase-credentials.json in the backend directory."
        )

    # Initialize Firebase Admin SDK
    cred = credentials.Certificate(cred_path)
    _firebase_app = firebase_admin.initialize_app(cred)

    print(f"✓ Firebase Admin SDK initialized successfully")
    print(f"  Project ID: {cred.project_id}")

    return _firebase_app


def get_firestore_client() -> firestore.Client:
    """
    Get Firestore client instance.

    Returns:
        firestore.Client: Firestore client for database operations

    Raises:
        RuntimeError: If Firebase has not been initialized
    """
    if _firebase_app is None:
        raise RuntimeError(
            "Firebase has not been initialized. "
            "Call initialize_firebase() at application startup."
        )

    return firestore.client()


def cleanup_firebase():
    """
    Cleanup Firebase resources.

    This should be called at application shutdown.
    """
    global _firebase_app

    if _firebase_app is not None:
        firebase_admin.delete_app(_firebase_app)
        _firebase_app = None
        print("✓ Firebase resources cleaned up")
