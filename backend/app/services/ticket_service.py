"""
Ticket service for Firestore operations.

This service handles CRUD operations for tickets in Firestore.
Collection: /tickets/{ticketId}

Key features:
- Labels stored as label_ids array field
- Parent-child ticket relationships
- Cascade delete to subtasks
"""

from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import List, Optional
from datetime import datetime, timezone

from app.models.schemas import TicketCreate, TicketUpdate


class TicketService:
    COLLECTION = "tickets"

    @staticmethod
    def create_ticket(db: firestore.Client, ticket_data: TicketCreate) -> dict:
        """Create a new ticket with optional labels."""
        now = firestore.SERVER_TIMESTAMP

        # Extract and convert data
        ticket_dict = ticket_data.model_dump(exclude={'label_ids'})
        label_ids = ticket_data.label_ids or []

        # Convert date objects to ISO strings for Firestore compatibility
        if ticket_dict.get("start_date"):
            ticket_dict["start_date"] = ticket_dict["start_date"].isoformat() if hasattr(ticket_dict["start_date"], 'isoformat') else ticket_dict["start_date"]
        if ticket_dict.get("end_date"):
            ticket_dict["end_date"] = ticket_dict["end_date"].isoformat() if hasattr(ticket_dict["end_date"], 'isoformat') else ticket_dict["end_date"]

        # Store labels as array field
        ticket_dict["label_ids"] = label_ids
        ticket_dict["created_at"] = now
        ticket_dict["updated_at"] = now

        # Create document with auto-generated ID
        doc_ref = db.collection(TicketService.COLLECTION).document()
        doc_ref.set(ticket_dict)

        # Return created ticket with ID
        ticket_dict["id"] = doc_ref.id
        ticket_dict["created_at"] = datetime.utcnow()
        ticket_dict["updated_at"] = datetime.utcnow()

        return ticket_dict

    @staticmethod
    def get_all_tickets(db: firestore.Client, project_id: Optional[str] = None) -> List[dict]:
        """Get all tickets, optionally filtered by project, ordered by created_at (desc)."""
        tickets_ref = db.collection(TicketService.COLLECTION)

        if project_id is not None:
            query = tickets_ref.where(filter=FieldFilter("project_id", "==", project_id))
            docs = query.stream()
        else:
            docs = tickets_ref.stream()

        tickets = []
        for doc in docs:
            ticket = doc.to_dict()
            ticket["id"] = doc.id
            tickets.append(ticket)

        # Sort by created_at descending (client-side)
        # Handle Firestore DatetimeWithNanoseconds by converting to timezone-aware datetime
        def get_sort_key(ticket):
            created_at = ticket.get("created_at")
            if created_at is None:
                return datetime.min.replace(tzinfo=timezone.utc)
            # If it's already a datetime-like object, ensure it's timezone-aware
            if hasattr(created_at, 'timestamp'):
                # Firestore DatetimeWithNanoseconds is timezone-aware
                return created_at
            # Otherwise try to convert from string
            if isinstance(created_at, str):
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except:
                    return datetime.min.replace(tzinfo=timezone.utc)
            return datetime.min.replace(tzinfo=timezone.utc)
        
        tickets.sort(key=get_sort_key, reverse=True)

        return tickets

    @staticmethod
    def get_ticket_by_id(db: firestore.Client, ticket_id: str) -> Optional[dict]:
        """Get a single ticket by ID."""
        doc_ref = db.collection(TicketService.COLLECTION).document(ticket_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        ticket = doc.to_dict()
        ticket["id"] = doc.id
        return ticket

    @staticmethod
    def update_ticket(db: firestore.Client, ticket_id: str, update_data: TicketUpdate) -> Optional[dict]:
        """Update a ticket including label relationships."""
        doc_ref = db.collection(TicketService.COLLECTION).document(ticket_id)

        # Check if ticket exists
        if not doc_ref.get().exists:
            return None

        # Extract label_ids separately
        update_dict = update_data.model_dump(exclude_unset=True, exclude={'label_ids'})
        label_ids = update_data.label_ids

        # Convert date objects to ISO strings for Firestore compatibility
        if "start_date" in update_dict and update_dict["start_date"] is not None:
            update_dict["start_date"] = update_dict["start_date"].isoformat() if hasattr(update_dict["start_date"], 'isoformat') else update_dict["start_date"]
        if "end_date" in update_dict and update_dict["end_date"] is not None:
            update_dict["end_date"] = update_dict["end_date"].isoformat() if hasattr(update_dict["end_date"], 'isoformat') else update_dict["end_date"]

        # Update labels if provided
        if label_ids is not None:
            update_dict["label_ids"] = label_ids

        # Add updated timestamp
        update_dict["updated_at"] = firestore.SERVER_TIMESTAMP

        # Update document
        doc_ref.update(update_dict)

        # Return updated ticket
        updated_doc = doc_ref.get()
        ticket = updated_doc.to_dict()
        ticket["id"] = updated_doc.id
        return ticket

    @staticmethod
    def delete_ticket(db: firestore.Client, ticket_id: str) -> bool:
        """
        Delete a ticket and cascade delete all subtasks.

        Subtasks are tickets where parent_ticket_id == ticket_id.
        """
        doc_ref = db.collection(TicketService.COLLECTION).document(ticket_id)

        # Check if ticket exists
        if not doc_ref.get().exists:
            return False

        # Find and delete all subtasks (recursive cascade)
        def delete_ticket_and_subtasks(tid: str):
            """Recursively delete a ticket and all its subtasks."""
            # Find all subtasks
            subtasks_ref = db.collection(TicketService.COLLECTION)
            query = subtasks_ref.where(filter=FieldFilter("parent_ticket_id", "==", tid))
            subtasks = list(query.stream())

            # Recursively delete subtasks first
            for subtask in subtasks:
                delete_ticket_and_subtasks(subtask.id)

            # Delete the ticket itself
            db.collection(TicketService.COLLECTION).document(tid).delete()

        # Execute cascade delete
        delete_ticket_and_subtasks(ticket_id)

        return True


# Singleton instance
ticket_service = TicketService()
