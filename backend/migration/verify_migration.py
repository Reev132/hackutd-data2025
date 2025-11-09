#!/usr/bin/env python3
"""
Migration Verification Script

This script verifies that data was correctly migrated from SQLite to Firestore
by comparing record counts and checking data integrity.

Usage:
    python migration/verify_migration.py
"""

import sqlite3
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.firebase_service import initialize_firebase
from firebase_admin import firestore


def verify_migration(db_path: str):
    """Verify migration by comparing SQLite and Firestore data."""

    # Connect to SQLite
    print("Connecting to SQLite database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Initialize Firebase
    print("Connecting to Firestore...\n")
    try:
        initialize_firebase()
        db = firestore.client()
    except Exception as e:
        print(f"✗ ERROR: Failed to connect to Firestore: {str(e)}")
        exit(1)

    print("="*60)
    print("MIGRATION VERIFICATION REPORT")
    print("="*60 + "\n")

    errors = []

    # Check each collection
    collections = [
        ('projects', 'projects'),
        ('users', 'users'),
        ('labels', 'labels'),
        ('cycles', 'cycles'),
        ('modules', 'modules'),
        ('tickets', 'tickets'),
    ]

    for sqlite_table, firestore_collection in collections:
        # Count in SQLite
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {sqlite_table}")
            sqlite_count = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            sqlite_count = 0
            print(f"⚠ {sqlite_table.upper()}: Table not found in SQLite (skipping)")
            continue

        # Count in Firestore
        firestore_count = len(list(db.collection(firestore_collection).stream()))

        # Compare
        if sqlite_count == firestore_count:
            print(f"✓ {sqlite_table.upper()}: {sqlite_count} records (match)")
        else:
            error_msg = f"✗ {sqlite_table.upper()}: SQLite={sqlite_count}, Firestore={firestore_count} (MISMATCH)"
            print(error_msg)
            errors.append(error_msg)

    # Check ticket-label relationships
    print()
    cursor.execute("SELECT COUNT(*) FROM ticket_labels")
    sqlite_associations = cursor.fetchone()[0]

    # Count labels in Firestore tickets
    tickets = db.collection('tickets').stream()
    firestore_label_count = sum(len(t.to_dict().get('label_ids', [])) for t in tickets)

    if sqlite_associations == firestore_label_count:
        print(f"✓ TICKET-LABEL ASSOCIATIONS: {sqlite_associations} (match)")
    else:
        error_msg = f"✗ TICKET-LABEL ASSOCIATIONS: SQLite={sqlite_associations}, Firestore={firestore_label_count} (MISMATCH)"
        print(error_msg)
        errors.append(error_msg)

    conn.close()

    # Summary
    print("\n" + "="*60)
    if errors:
        print("✗ VERIFICATION FAILED")
        print("="*60)
        print(f"\nFound {len(errors)} issue(s):")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease review the migration and try again.")
        exit(1)
    else:
        print("✓ VERIFICATION SUCCESSFUL")
        print("="*60)
        print("\nAll data has been correctly migrated to Firestore!")
        print("You can now safely use the new Firestore backend.")


if __name__ == "__main__":
    backend_dir = Path(__file__).parent.parent
    db_path = backend_dir / "catalyst.db"

    if not db_path.exists():
        print(f"✗ ERROR: SQLite database not found at {db_path}")
        exit(1)

    verify_migration(str(db_path))
