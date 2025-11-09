# Firestore Migration Guide

This guide will help you migrate your data from SQLite to Firebase Firestore.

## Overview

The migration involves:
1. Setting up Firebase credentials
2. Installing new dependencies
3. Exporting data from SQLite
4. Importing data into Firestore
5. Verifying the migration
6. Deploying Firestore indexes

## Prerequisites

- Python 3.8+
- A Firebase project (create one at https://console.firebase.google.com)
- Firestore enabled in your Firebase project

## Step 1: Get Firebase Credentials

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project (or create a new one)
3. Click the gear icon ⚙️ → **Project settings**
4. Go to the **Service accounts** tab
5. Click **Generate new private key**
6. Save the downloaded JSON file as `firebase-credentials.json` in the `backend/` directory

**IMPORTANT**: Never commit this file to git. It's already in `.gitignore`.

## Step 2: Enable Firestore

1. In Firebase Console, go to **Firestore Database**
2. Click **Create database**
3. Choose **Start in production mode** (you can adjust rules later)
4. Select your preferred region
5. Click **Enable**

## Step 3: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install `firebase-admin` and remove SQLAlchemy.

## Step 4: Backup Your Current Database

```bash
# Create a backup copy of your SQLite database
cp catalyst.db catalyst.db.backup
```

## Step 5: Export Data from SQLite

```bash
python migration/export_sqlite.py
```

This creates `migration/migration_backup.json` with all your data.

**Expected output:**
```
Exporting data from SQLite...
  ✓ Exported 1 projects
  ✓ Exported 0 users
  ✓ Exported 3 labels
  ✓ Exported 1 cycles
  ✓ Exported 2 modules
  ✓ Exported 5 tickets
  ✓ Exported 6 ticket-label associations

✓ Export complete!
```

## Step 6: Stop the Backend Server

If your backend is running, stop it now:

```bash
# Kill the uvicorn process or press Ctrl+C
```

## Step 7: Import Data to Firestore

```bash
python migration/import_firestore.py
```

This imports all data to Firestore and creates `migration/id_mapping.json` showing the ID conversions.

**Expected output:**
```
Initializing Firebase...
✓ Firebase initialized successfully

Loading data from migration_backup.json...
✓ Data loaded

Importing 1 projects...
  ✓ Imported 1 projects

...

✓ MIGRATION COMPLETE!
```

## Step 8: Verify the Migration

```bash
python migration/verify_migration.py
```

This compares record counts between SQLite and Firestore.

**Expected output:**
```
✓ PROJECTS: 1 records (match)
✓ USERS: 0 records (match)
✓ LABELS: 3 records (match)
✓ CYCLES: 1 records (match)
✓ MODULES: 2 records (match)
✓ TICKETS: 5 records (match)
✓ TICKET-LABEL ASSOCIATIONS: 6 (match)

✓ VERIFICATION SUCCESSFUL
```

## Step 9: Deploy Firestore Indexes

Firestore requires indexes for complex queries. Deploy them using Firebase CLI:

### Install Firebase CLI (if not already installed)

```bash
npm install -g firebase-tools
```

### Login to Firebase

```bash
firebase login
```

### Initialize Firebase (one-time setup)

```bash
cd backend
firebase init firestore
```

Select your project and use `firestore.indexes.json` when prompted.

### Deploy Indexes

```bash
firebase deploy --only firestore:indexes
```

**Note**: Indexes can take a few minutes to build in production. Check status in Firebase Console.

## Step 10: Start the Backend

```bash
python -m uvicorn app.main:app --reload --port 8000
```

You should see:
```
✓ Firebase Admin SDK initialized successfully
  Project ID: your-project-id
✓ Application started successfully
```

## Step 11: Test the Backend

Test that all endpoints work:

```bash
# List projects
curl http://localhost:8000/projects

# List tickets
curl http://localhost:8000/tickets
```

## Troubleshooting

### Error: "Firebase credentials not found"

- Ensure `firebase-credentials.json` exists in `backend/` directory
- Check that the file is valid JSON
- Verify file permissions (should be readable)

### Error: "Failed to initialize Firebase"

- Check your internet connection
- Verify the service account key is valid
- Ensure Firestore is enabled in Firebase Console

### Verification fails with mismatched counts

- Check for errors during import
- Review `migration/id_mapping.json` for any NULL values
- Re-run the import script

### Frontend showing errors

- Clear browser cache
- Check browser console for errors
- Verify backend is running on port 8000
- Check CORS configuration in `main.py`

## Rollback (If Needed)

If you need to rollback to SQLite:

1. Stop the backend server
2. Restore the backup: `cp catalyst.db.backup catalyst.db`
3. Revert code changes (checkout previous commit)
4. Restart the server

You can also export Firestore data for backup:

```bash
python migration/rollback_firestore.py
```

This creates `migration/firestore_backup.json`.

## File Structure

```
backend/
├── firebase-credentials.json          # Firebase service account key (don't commit!)
├── firestore.indexes.json            # Firestore composite indexes
├── migration/
│   ├── README.md                     # This file
│   ├── export_sqlite.py              # Export SQLite → JSON
│   ├── import_firestore.py           # Import JSON → Firestore
│   ├── verify_migration.py           # Verify data integrity
│   ├── rollback_firestore.py         # Export Firestore → JSON
│   ├── migration_backup.json         # SQLite data export (generated)
│   ├── firestore_backup.json         # Firestore data export (generated)
│   └── id_mapping.json               # ID conversion map (generated)
└── catalyst.db.backup                # SQLite backup (manual)
```

## What Changed

### Data Structure

- **IDs**: Integer IDs → Firestore string IDs (auto-generated)
- **Labels**: `ticket_labels` table → `label_ids` array in tickets
- **Timestamps**: SQLite timestamps → Firestore SERVER_TIMESTAMP
- **Collections**: All collections are now top-level with `project_id` fields

### Code Changes

- Removed: `app/models/orm.py` (SQLAlchemy models)
- Removed: `app/services/db_service.py` (SQLite setup)
- Added: `app/services/firebase_service.py` (Firebase initialization)
- Added: `app/services/firestore_client.py` (Dependency injection)
- Updated: All 6 service files to use Firestore SDK
- Updated: `app/routes/catalyst.py` (Firestore dependencies)
- Updated: `app/main.py` (Firebase initialization)

### Dependencies

- Removed: `SQLAlchemy==2.0.32`
- Added: `firebase-admin==6.5.0`

## Next Steps

After successful migration:

1. Test all features thoroughly
2. Update frontend if IDs changed (unlikely with this migration)
3. Monitor Firestore usage in Firebase Console
4. Set up Firestore security rules for production
5. Consider deleting `catalyst.db` after confirming everything works

## Questions?

If you encounter issues:
1. Check the error messages carefully
2. Review Firebase Console for any quota/permission issues
3. Ensure all prerequisites are met
4. Try the rollback procedure if needed

Happy migrating! 🚀
