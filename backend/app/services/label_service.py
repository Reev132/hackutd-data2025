"""
Label service for Firestore operations.

This service handles CRUD operations for labels in Firestore.
Collection: /labels/{labelId}
"""

from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import List, Optional
from datetime import datetime

from app.models.schemas import LabelCreate, LabelUpdate


class LabelService:
    COLLECTION = "labels"

    @staticmethod
    def create_label(db: firestore.Client, label_data: LabelCreate) -> dict:
        """Create a new label in Firestore."""
        now = firestore.SERVER_TIMESTAMP

        label_dict = label_data.model_dump()
        label_dict["created_at"] = now

        # Create document with auto-generated ID
        doc_ref = db.collection(LabelService.COLLECTION).document()
        doc_ref.set(label_dict)

        # Return created label with ID
        label_dict["id"] = doc_ref.id
        label_dict["created_at"] = datetime.utcnow()

        return label_dict

    @staticmethod
    def get_all_labels(db: firestore.Client, project_id: Optional[str] = None) -> List[dict]:
        """Get all labels, optionally filtered by project, ordered by name."""
        labels_ref = db.collection(LabelService.COLLECTION)

        if project_id is not None:
            query = labels_ref.where(filter=FieldFilter("project_id", "==", project_id))
            docs = query.stream()
        else:
            docs = labels_ref.stream()

        labels = []
        for doc in docs:
            label = doc.to_dict()
            label["id"] = doc.id
            labels.append(label)

        # Sort by name client-side
        labels.sort(key=lambda x: x.get("name", "").lower())

        return labels

    @staticmethod
    def get_label_by_id(db: firestore.Client, label_id: str) -> Optional[dict]:
        """Get a single label by ID."""
        doc_ref = db.collection(LabelService.COLLECTION).document(label_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        label = doc.to_dict()
        label["id"] = doc.id
        return label

    @staticmethod
    def update_label(db: firestore.Client, label_id: str, update_data: LabelUpdate) -> Optional[dict]:
        """Update a label."""
        doc_ref = db.collection(LabelService.COLLECTION).document(label_id)

        # Check if label exists
        if not doc_ref.get().exists:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)

        # Update document
        doc_ref.update(update_dict)

        # Return updated label
        updated_doc = doc_ref.get()
        label = updated_doc.to_dict()
        label["id"] = updated_doc.id
        return label

    @staticmethod
    def delete_label(db: firestore.Client, label_id: str) -> bool:
        """
        Delete a label.

        Note: This removes the label from all tickets' label_ids arrays.
        """
        doc_ref = db.collection(LabelService.COLLECTION).document(label_id)

        # Check if label exists
        if not doc_ref.get().exists:
            return False

        # Find all tickets with this label and remove it from their label_ids
        tickets_ref = db.collection("tickets")
        query = tickets_ref.where(filter=FieldFilter("label_ids", "array_contains", label_id))
        tickets = list(query.stream())

        # Update tickets in batches
        batch_size = 500
        for i in range(0, len(tickets), batch_size):
            batch = db.batch()
            for ticket in tickets[i:i + batch_size]:
                ticket_data = ticket.to_dict()
                label_ids = ticket_data.get("label_ids", [])
                if label_id in label_ids:
                    label_ids.remove(label_id)
                    batch.update(ticket.reference, {
                        "label_ids": label_ids,
                        "updated_at": firestore.SERVER_TIMESTAMP
                    })
            if tickets[i:i + batch_size]:  # Only commit if there are updates
                batch.commit()

        # Delete label
        doc_ref.delete()

        return True


# Singleton instance
label_service = LabelService()
