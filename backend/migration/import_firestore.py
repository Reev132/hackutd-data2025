#!/usr/bin/env python3
"""
JSON to Firestore Import Script

This script imports data from the JSON backup file into Firestore.
It converts integer IDs to Firestore document IDs and transforms
the ticket_labels association table into label_ids arrays.

Usage:
    python migration/import_firestore.py

Input:
    migration/migration_backup.json - JSON export from SQLite

Prerequisites:
    - Firebase credentials configured (firebase-credentials.json)
    - firebase-admin package installed
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.firebase_service import initialize_firebase
from firebase_admin import firestore


def import_json_to_firestore(json_path: str):
    """Import data from JSON file into Firestore."""

    # Initialize Firebase
    print("Initializing Firebase...")
    try:
        initialize_firebase()
        db = firestore.client()
        print("✓ Firebase initialized successfully\n")
    except Exception as e:
        print(f"✗ ERROR: Failed to initialize Firebase: {str(e)}")
        print("  Make sure firebase-credentials.json exists in the backend directory")
        exit(1)

    # Load JSON data
    print(f"Loading data from {json_path}...")
    with open(json_path, 'r') as f:
        data = json.load(f)
    print("✓ Data loaded\n")

    # ID mapping (old integer ID -> new Firestore string ID)
    id_map = {
        "projects": {},
        "users": {},
        "labels": {},
        "cycles": {},
        "modules": {},
        "tickets": {}
    }

    # Import in order (respecting foreign key dependencies)

    # 1. Import projects
    print(f"Importing {len(data['projects'])} projects...")
    for project in data['projects']:
        old_id = project.pop('id')
        doc_ref = db.collection('projects').document()
        doc_ref.set(project)
        id_map['projects'][old_id] = doc_ref.id
    print(f"  ✓ Imported {len(data['projects'])} projects\n")

    # 2. Import users
    print(f"Importing {len(data['users'])} users...")
    for user in data['users']:
        old_id = user.pop('id')
        doc_ref = db.collection('users').document()
        doc_ref.set(user)
        id_map['users'][old_id] = doc_ref.id
    print(f"  ✓ Imported {len(data['users'])} users\n")

    # 3. Import labels (update project_id)
    print(f"Importing {len(data['labels'])} labels...")
    for label in data['labels']:
        old_id = label.pop('id')
        old_project_id = label.get('project_id')
        if old_project_id and old_project_id in id_map['projects']:
            label['project_id'] = id_map['projects'][old_project_id]
        doc_ref = db.collection('labels').document()
        doc_ref.set(label)
        id_map['labels'][old_id] = doc_ref.id
    print(f"  ✓ Imported {len(data['labels'])} labels\n")

    # 4. Import cycles (update project_id)
    print(f"Importing {len(data['cycles'])} cycles...")
    for cycle in data['cycles']:
        old_id = cycle.pop('id')
        old_project_id = cycle.get('project_id')
        if old_project_id and old_project_id in id_map['projects']:
            cycle['project_id'] = id_map['projects'][old_project_id]
        doc_ref = db.collection('cycles').document()
        doc_ref.set(cycle)
        id_map['cycles'][old_id] = doc_ref.id
    print(f"  ✓ Imported {len(data['cycles'])} cycles\n")

    # 5. Import modules (update project_id)
    print(f"Importing {len(data['modules'])} modules...")
    for module in data['modules']:
        old_id = module.pop('id')
        old_project_id = module.get('project_id')
        if old_project_id and old_project_id in id_map['projects']:
            module['project_id'] = id_map['projects'][old_project_id]
        doc_ref = db.collection('modules').document()
        doc_ref.set(module)
        id_map['modules'][old_id] = doc_ref.id
    print(f"  ✓ Imported {len(data['modules'])} modules\n")

    # 6. Build label_ids mapping from ticket_labels association table
    print("Processing ticket-label relationships...")
    ticket_label_map = {}  # ticket_id -> [label_ids]
    for assoc in data['ticket_labels']:
        old_ticket_id = assoc['ticket_id']
        old_label_id = assoc['label_id']
        if old_ticket_id not in ticket_label_map:
            ticket_label_map[old_ticket_id] = []
        if old_label_id in id_map['labels']:
            ticket_label_map[old_ticket_id].append(id_map['labels'][old_label_id])
    print(f"  ✓ Processed {len(data['ticket_labels'])} associations\n")

    # 7. Import tickets (update all foreign keys and add label_ids)
    print(f"Importing {len(data['tickets'])} tickets...")
    for ticket in data['tickets']:
        old_id = ticket.pop('id')

        # Update foreign key references
        if ticket.get('project_id') and ticket['project_id'] in id_map['projects']:
            ticket['project_id'] = id_map['projects'][ticket['project_id']]

        if ticket.get('cycle_id') and ticket['cycle_id'] in id_map['cycles']:
            ticket['cycle_id'] = id_map['cycles'][ticket['cycle_id']]

        if ticket.get('module_id') and ticket['module_id'] in id_map['modules']:
            ticket['module_id'] = id_map['modules'][ticket['module_id']]

        if ticket.get('parent_ticket_id') and ticket['parent_ticket_id'] in id_map['tickets']:
            ticket['parent_ticket_id'] = id_map['tickets'][ticket['parent_ticket_id']]

        if ticket.get('assignee_id') and ticket['assignee_id'] in id_map['users']:
            ticket['assignee_id'] = id_map['users'][ticket['assignee_id']]

        # Remove assignee_id if it doesn't exist in the original schema
        if 'assignee_id' in ticket and ticket['assignee_id'] is None:
            del ticket['assignee_id']

        # Add label_ids array
        ticket['label_ids'] = ticket_label_map.get(old_id, [])

        # Create document
        doc_ref = db.collection('tickets').document()
        doc_ref.set(ticket)
        id_map['tickets'][old_id] = doc_ref.id

    print(f"  ✓ Imported {len(data['tickets'])} tickets\n")

    # Save ID mapping for reference
    mapping_path = Path(__file__).parent / "id_mapping.json"
    with open(mapping_path, 'w') as f:
        json.dump(id_map, f, indent=2)
    print(f"✓ ID mapping saved to {mapping_path}")

    print("\n" + "="*60)
    print("✓ MIGRATION COMPLETE!")
    print("="*60)
    print(f"  Projects:  {len(data['projects'])}")
    print(f"  Users:     {len(data['users'])}")
    print(f"  Labels:    {len(data['labels'])}")
    print(f"  Cycles:    {len(data['cycles'])}")
    print(f"  Modules:   {len(data['modules'])}")
    print(f"  Tickets:   {len(data['tickets'])}")
    print("="*60)


if __name__ == "__main__":
    json_path = Path(__file__).parent / "migration_backup.json"

    if not json_path.exists():
        print(f"✗ ERROR: JSON backup file not found at {json_path}")
        print("  Run export_sqlite.py first to create the backup")
        exit(1)

    import_json_to_firestore(str(json_path))
