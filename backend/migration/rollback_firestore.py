#!/usr/bin/env python3
"""
Firestore Rollback Script

This script provides a rollback mechanism by exporting Firestore data
back to a JSON file that can be used to reconstruct the SQLite database.

Usage:
    python migration/rollback_firestore.py

Output:
    migration/firestore_backup.json - Firestore data export
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.firebase_service import initialize_firebase
from firebase_admin import firestore


def firestore_to_json(output_path: str):
    """Export all Firestore data to JSON."""

    # Initialize Firebase
    print("Connecting to Firestore...")
    try:
        initialize_firebase()
        db = firestore.client()
        print("✓ Connected successfully\n")
    except Exception as e:
        print(f"✗ ERROR: Failed to connect to Firestore: {str(e)}")
        exit(1)

    data = {
        "exported_at": datetime.utcnow().isoformat(),
        "source": "firestore",
        "projects": [],
        "users": [],
        "labels": [],
        "cycles": [],
        "modules": [],
        "tickets": []
    }

    print("Exporting data from Firestore...")

    # Export each collection
    collections = ['projects', 'users', 'labels', 'cycles', 'modules', 'tickets']

    for collection_name in collections:
        docs = db.collection(collection_name).stream()
        count = 0
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['id'] = doc.id  # Include document ID
            data[collection_name].append(doc_data)
            count += 1
        print(f"  ✓ Exported {count} {collection_name}")

    # Write to JSON
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n✓ Export complete! Data saved to {output_path}")
    print(f"  Total documents: {sum(len(v) for k, v in data.items() if isinstance(v, list))}")
    print("\nYou can use this backup to:")
    print("  1. Restore data to Firestore if needed")
    print("  2. Reconstruct SQLite database (requires additional conversion)")


if __name__ == "__main__":
    output_path = Path(__file__).parent / "firestore_backup.json"
    firestore_to_json(str(output_path))
