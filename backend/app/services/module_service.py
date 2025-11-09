"""
Module service for Firestore operations.

This service handles CRUD operations for modules (feature groups) in Firestore.
Collection: /modules/{moduleId}
"""

from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import List, Optional
from datetime import datetime

from app.models.schemas import ModuleCreate, ModuleUpdate


class ModuleService:
    COLLECTION = "modules"

    @staticmethod
    def create_module(db: firestore.Client, module_data: ModuleCreate) -> dict:
        """Create a new module in Firestore."""
        now = firestore.SERVER_TIMESTAMP

        module_dict = module_data.model_dump()
        module_dict["created_at"] = now
        module_dict["updated_at"] = now

        # Create document with auto-generated ID
        doc_ref = db.collection(ModuleService.COLLECTION).document()
        doc_ref.set(module_dict)

        # Return created module with ID
        module_dict["id"] = doc_ref.id
        module_dict["created_at"] = datetime.utcnow()
        module_dict["updated_at"] = datetime.utcnow()

        return module_dict

    @staticmethod
    def get_all_modules(db: firestore.Client, project_id: Optional[str] = None) -> List[dict]:
        """Get all modules, optionally filtered by project, ordered by name."""
        modules_ref = db.collection(ModuleService.COLLECTION)

        if project_id is not None:
            query = modules_ref.where(filter=FieldFilter("project_id", "==", project_id))
            docs = query.stream()
        else:
            docs = modules_ref.stream()

        modules = []
        for doc in docs:
            module = doc.to_dict()
            module["id"] = doc.id
            modules.append(module)

        # Sort by name (client-side)
        modules.sort(key=lambda x: x.get("name", "").lower())

        return modules

    @staticmethod
    def get_module_by_id(db: firestore.Client, module_id: str) -> Optional[dict]:
        """Get a single module by ID."""
        doc_ref = db.collection(ModuleService.COLLECTION).document(module_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        module = doc.to_dict()
        module["id"] = doc.id
        return module

    @staticmethod
    def update_module(db: firestore.Client, module_id: str, update_data: ModuleUpdate) -> Optional[dict]:
        """Update a module."""
        doc_ref = db.collection(ModuleService.COLLECTION).document(module_id)

        # Check if module exists
        if not doc_ref.get().exists:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = firestore.SERVER_TIMESTAMP

        # Update document
        doc_ref.update(update_dict)

        # Return updated module
        updated_doc = doc_ref.get()
        module = updated_doc.to_dict()
        module["id"] = updated_doc.id
        return module

    @staticmethod
    def delete_module(db: firestore.Client, module_id: str) -> bool:
        """
        Delete a module.

        Note: This sets module_id to null in all tickets belonging to this module.
        """
        doc_ref = db.collection(ModuleService.COLLECTION).document(module_id)

        # Check if module exists
        if not doc_ref.get().exists:
            return False

        # Update all tickets in this module (set module_id to null)
        tickets_ref = db.collection("tickets")
        query = tickets_ref.where(filter=FieldFilter("module_id", "==", module_id))
        tickets = list(query.stream())

        # Update tickets in batches
        batch_size = 500
        for i in range(0, len(tickets), batch_size):
            batch = db.batch()
            for ticket in tickets[i:i + batch_size]:
                batch.update(ticket.reference, {"module_id": None, "updated_at": firestore.SERVER_TIMESTAMP})
            if tickets[i:i + batch_size]:
                batch.commit()

        # Delete module
        doc_ref.delete()

        return True


# Singleton instance
module_service = ModuleService()
