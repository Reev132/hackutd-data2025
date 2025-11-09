"""
User service for Firestore operations.

This service handles CRUD operations for users in Firestore.
Collection: /users/{userId}
"""

from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import List, Optional
from datetime import datetime

from app.models.schemas import UserCreate, UserUpdate


class UserService:
    COLLECTION = "users"

    @staticmethod
    def create_user(db: firestore.Client, user_data: UserCreate) -> dict:
        """Create a new user in Firestore."""
        now = firestore.SERVER_TIMESTAMP

        # Check email uniqueness if email provided
        if user_data.email:
            existing = UserService.get_user_by_email(db, user_data.email)
            if existing:
                raise ValueError(f"User with email {user_data.email} already exists")

        user_dict = user_data.model_dump()
        user_dict["created_at"] = now
        user_dict["updated_at"] = now

        # Create document with auto-generated ID
        doc_ref = db.collection(UserService.COLLECTION).document()
        doc_ref.set(user_dict)

        # Return created user with ID
        user_dict["id"] = doc_ref.id
        user_dict["created_at"] = datetime.utcnow()
        user_dict["updated_at"] = datetime.utcnow()

        return user_dict

    @staticmethod
    def get_all_users(db: firestore.Client) -> List[dict]:
        """Get all users, ordered by name."""
        users_ref = db.collection(UserService.COLLECTION)
        docs = users_ref.stream()

        users = []
        for doc in docs:
            user = doc.to_dict()
            user["id"] = doc.id
            users.append(user)

        # Sort by name client-side (Firestore requires index for orderBy)
        users.sort(key=lambda x: x.get("name", "").lower())

        return users

    @staticmethod
    def get_user_by_id(db: firestore.Client, user_id: str) -> Optional[dict]:
        """Get a single user by ID."""
        doc_ref = db.collection(UserService.COLLECTION).document(user_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        user = doc.to_dict()
        user["id"] = doc.id
        return user

    @staticmethod
    def get_user_by_email(db: firestore.Client, email: str) -> Optional[dict]:
        """Get a user by email address."""
        users_ref = db.collection(UserService.COLLECTION)
        query = users_ref.where(filter=FieldFilter("email", "==", email))
        docs = list(query.stream())

        if not docs:
            return None

        user = docs[0].to_dict()
        user["id"] = docs[0].id
        return user

    @staticmethod
    def update_user(db: firestore.Client, user_id: str, update_data: UserUpdate) -> Optional[dict]:
        """Update a user."""
        doc_ref = db.collection(UserService.COLLECTION).document(user_id)

        # Check if user exists
        if not doc_ref.get().exists:
            return None

        # Check email uniqueness if being updated
        update_dict = update_data.model_dump(exclude_unset=True)
        if "email" in update_dict and update_dict["email"]:
            existing = UserService.get_user_by_email(db, update_dict["email"])
            if existing and existing["id"] != user_id:
                raise ValueError(f"User with email {update_dict['email']} already exists")

        # Add updated timestamp
        update_dict["updated_at"] = firestore.SERVER_TIMESTAMP

        # Update document
        doc_ref.update(update_dict)

        # Return updated user
        updated_doc = doc_ref.get()
        user = updated_doc.to_dict()
        user["id"] = updated_doc.id
        return user

    @staticmethod
    def delete_user(db: firestore.Client, user_id: str) -> bool:
        """
        Delete a user.

        Note: This sets assignee_id to null in all tickets assigned to this user.
        """
        doc_ref = db.collection(UserService.COLLECTION).document(user_id)

        # Check if user exists
        if not doc_ref.get().exists:
            return False

        # Update all tickets assigned to this user (set assignee_id to null)
        tickets_ref = db.collection("tickets")
        query = tickets_ref.where(filter=FieldFilter("assignee_id", "==", user_id))
        tickets = query.stream()

        batch = db.batch()
        for ticket in tickets:
            batch.update(ticket.reference, {"assignee_id": None, "updated_at": firestore.SERVER_TIMESTAMP})

        # Delete user
        batch.delete(doc_ref)

        # Commit batch
        batch.commit()

        return True


# Singleton instance
user_service = UserService()


