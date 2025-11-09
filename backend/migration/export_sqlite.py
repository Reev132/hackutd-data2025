#!/usr/bin/env python3
"""
SQLite to JSON Export Script

This script exports all data from the SQLite database to a JSON file.
This JSON file will then be imported into Firestore.

Usage:
    python migration/export_sqlite.py

Output:
    migration/migration_backup.json - Contains all exported data
"""

import sqlite3
import json
from datetime import datetime, date
from pathlib import Path


def serialize_value(value):
    """Convert value to JSON-serializable format."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def export_sqlite_to_json(db_path: str, output_path: str):
    """Export all data from SQLite database to JSON."""

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    cursor = conn.cursor()

    data = {
        "exported_at": datetime.utcnow().isoformat(),
        "projects": [],
        "users": [],
        "labels": [],
        "cycles": [],
        "modules": [],
        "tickets": [],
        "ticket_labels": []  # Many-to-many association
    }

    print("Exporting data from SQLite...")

    # Export projects
    cursor.execute("SELECT * FROM projects")
    for row in cursor.fetchall():
        data["projects"].append({k: serialize_value(row[k]) for k in row.keys()})
    print(f"  ✓ Exported {len(data['projects'])} projects")

    # Export users (if table exists)
    try:
        cursor.execute("SELECT * FROM users")
        for row in cursor.fetchall():
            data["users"].append({k: serialize_value(row[k]) for k in row.keys()})
        print(f"  ✓ Exported {len(data['users'])} users")
    except sqlite3.OperationalError:
        print("  ⚠ Users table not found (skipping)")

    # Export labels
    cursor.execute("SELECT * FROM labels")
    for row in cursor.fetchall():
        data["labels"].append({k: serialize_value(row[k]) for k in row.keys()})
    print(f"  ✓ Exported {len(data['labels'])} labels")

    # Export cycles
    cursor.execute("SELECT * FROM cycles")
    for row in cursor.fetchall():
        data["cycles"].append({k: serialize_value(row[k]) for k in row.keys()})
    print(f"  ✓ Exported {len(data['cycles'])} cycles")

    # Export modules
    cursor.execute("SELECT * FROM modules")
    for row in cursor.fetchall():
        data["modules"].append({k: serialize_value(row[k]) for k in row.keys()})
    print(f"  ✓ Exported {len(data['modules'])} modules")

    # Export tickets
    cursor.execute("SELECT * FROM tickets")
    for row in cursor.fetchall():
        data["tickets"].append({k: serialize_value(row[k]) for k in row.keys()})
    print(f"  ✓ Exported {len(data['tickets'])} tickets")

    # Export ticket_labels association table
    cursor.execute("SELECT * FROM ticket_labels")
    for row in cursor.fetchall():
        data["ticket_labels"].append({k: serialize_value(row[k]) for k in row.keys()})
    print(f"  ✓ Exported {len(data['ticket_labels'])} ticket-label associations")

    conn.close()

    # Write to JSON file
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n✓ Export complete! Data saved to {output_path}")
    print(f"  Total records: {sum(len(v) if isinstance(v, list) else 0 for v in data.values())}")


if __name__ == "__main__":
    # Paths
    backend_dir = Path(__file__).parent.parent
    db_path = backend_dir / "catalyst.db"
    output_path = Path(__file__).parent / "migration_backup.json"

    if not db_path.exists():
        print(f"✗ ERROR: Database file not found at {db_path}")
        exit(1)

    export_sqlite_to_json(str(db_path), str(output_path))
