"""
Cycle service for Firestore operations.

This service handles CRUD operations for cycles (sprints) in Firestore.
Collection: /cycles/{cycleId}
"""

from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import List, Optional
from datetime import datetime

from app.models.schemas import CycleCreate, CycleUpdate


class CycleService:
    COLLECTION = "cycles"

    @staticmethod
    def create_cycle(db: firestore.Client, cycle_data: CycleCreate) -> dict:
        """Create a new cycle in Firestore."""
        now = firestore.SERVER_TIMESTAMP

        cycle_dict = cycle_data.model_dump()
        cycle_dict["created_at"] = now
        cycle_dict["updated_at"] = now

        # Create document with auto-generated ID
        doc_ref = db.collection(CycleService.COLLECTION).document()
        doc_ref.set(cycle_dict)

        # Return created cycle with ID
        cycle_dict["id"] = doc_ref.id
        cycle_dict["created_at"] = datetime.utcnow()
        cycle_dict["updated_at"] = datetime.utcnow()

        return cycle_dict

    @staticmethod
    def get_all_cycles(db: firestore.Client, project_id: Optional[str] = None) -> List[dict]:
        """Get all cycles, optionally filtered by project, ordered by start_date (desc)."""
        cycles_ref = db.collection(CycleService.COLLECTION)

        if project_id is not None:
            query = cycles_ref.where(filter=FieldFilter("project_id", "==", project_id))
            docs = query.stream()
        else:
            docs = cycles_ref.stream()

        cycles = []
        for doc in docs:
            cycle = doc.to_dict()
            cycle["id"] = doc.id
            cycles.append(cycle)

        # Sort by start_date descending (client-side)
        cycles.sort(key=lambda x: x.get("start_date", datetime.min), reverse=True)

        return cycles

    @staticmethod
    def get_cycle_by_id(db: firestore.Client, cycle_id: str) -> Optional[dict]:
        """Get a single cycle by ID."""
        doc_ref = db.collection(CycleService.COLLECTION).document(cycle_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        cycle = doc.to_dict()
        cycle["id"] = doc.id
        return cycle

    @staticmethod
    def update_cycle(db: firestore.Client, cycle_id: str, update_data: CycleUpdate) -> Optional[dict]:
        """Update a cycle."""
        doc_ref = db.collection(CycleService.COLLECTION).document(cycle_id)

        # Check if cycle exists
        if not doc_ref.get().exists:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = firestore.SERVER_TIMESTAMP

        # Update document
        doc_ref.update(update_dict)

        # Return updated cycle
        updated_doc = doc_ref.get()
        cycle = updated_doc.to_dict()
        cycle["id"] = updated_doc.id
        return cycle

    @staticmethod
    def delete_cycle(db: firestore.Client, cycle_id: str) -> bool:
        """
        Delete a cycle.

        Note: This sets cycle_id to null in all tickets belonging to this cycle.
        """
        doc_ref = db.collection(CycleService.COLLECTION).document(cycle_id)

        # Check if cycle exists
        if not doc_ref.get().exists:
            return False

        # Update all tickets in this cycle (set cycle_id to null)
        tickets_ref = db.collection("tickets")
        query = tickets_ref.where(filter=FieldFilter("cycle_id", "==", cycle_id))
        tickets = list(query.stream())

        # Update tickets in batches
        batch_size = 500
        for i in range(0, len(tickets), batch_size):
            batch = db.batch()
            for ticket in tickets[i:i + batch_size]:
                batch.update(ticket.reference, {"cycle_id": None, "updated_at": firestore.SERVER_TIMESTAMP})
            if tickets[i:i + batch_size]:
                batch.commit()

        # Delete cycle
        doc_ref.delete()

        return True


# Singleton instance
cycle_service = CycleService()
