"""
Project service for Firestore operations.

This service handles CRUD operations for projects in Firestore.
Collection: /projects/{projectId}
"""

from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import List, Optional
from datetime import datetime

from app.models.schemas import ProjectCreate, ProjectUpdate


class ProjectService:
    COLLECTION = "projects"

    @staticmethod
    def create_project(db: firestore.Client, project_data: ProjectCreate) -> dict:
        """Create a new project in Firestore."""
        now = firestore.SERVER_TIMESTAMP

        # Check name uniqueness
        existing_name = ProjectService.get_project_by_name(db, project_data.name)
        if existing_name:
            raise ValueError(f"Project with name '{project_data.name}' already exists")

        # Check identifier uniqueness
        existing_id = ProjectService.get_project_by_identifier(db, project_data.identifier)
        if existing_id:
            raise ValueError(f"Project with identifier '{project_data.identifier}' already exists")

        project_dict = project_data.model_dump()
        project_dict["created_at"] = now
        project_dict["updated_at"] = now

        # Create document with auto-generated ID
        doc_ref = db.collection(ProjectService.COLLECTION).document()
        doc_ref.set(project_dict)

        # Return created project with ID
        project_dict["id"] = doc_ref.id
        project_dict["created_at"] = datetime.utcnow()
        project_dict["updated_at"] = datetime.utcnow()

        return project_dict

    @staticmethod
    def get_all_projects(db: firestore.Client) -> List[dict]:
        """Get all projects, ordered by creation date (descending)."""
        projects_ref = db.collection(ProjectService.COLLECTION)
        docs = projects_ref.stream()

        projects = []
        for doc in docs:
            project = doc.to_dict()
            project["id"] = doc.id
            projects.append(project)

        # Sort by created_at descending (client-side)
        projects.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)

        return projects

    @staticmethod
    def get_project_by_id(db: firestore.Client, project_id: str) -> Optional[dict]:
        """Get a single project by ID."""
        doc_ref = db.collection(ProjectService.COLLECTION).document(project_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        project = doc.to_dict()
        project["id"] = doc.id
        return project

    @staticmethod
    def get_project_by_identifier(db: firestore.Client, identifier: str) -> Optional[dict]:
        """Get a project by its identifier (e.g., 'HACK')."""
        projects_ref = db.collection(ProjectService.COLLECTION)
        query = projects_ref.where(filter=FieldFilter("identifier", "==", identifier))
        docs = list(query.stream())

        if not docs:
            return None

        project = docs[0].to_dict()
        project["id"] = docs[0].id
        return project

    @staticmethod
    def get_project_by_name(db: firestore.Client, name: str) -> Optional[dict]:
        """Get a project by its name."""
        projects_ref = db.collection(ProjectService.COLLECTION)
        query = projects_ref.where(filter=FieldFilter("name", "==", name))
        docs = list(query.stream())

        if not docs:
            return None

        project = docs[0].to_dict()
        project["id"] = docs[0].id
        return project

    @staticmethod
    def update_project(db: firestore.Client, project_id: str, update_data: ProjectUpdate) -> Optional[dict]:
        """Update a project."""
        doc_ref = db.collection(ProjectService.COLLECTION).document(project_id)

        # Check if project exists
        if not doc_ref.get().exists:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)

        # Check uniqueness constraints if being updated
        if "name" in update_dict:
            existing = ProjectService.get_project_by_name(db, update_dict["name"])
            if existing and existing["id"] != project_id:
                raise ValueError(f"Project with name '{update_dict['name']}' already exists")

        if "identifier" in update_dict:
            existing = ProjectService.get_project_by_identifier(db, update_dict["identifier"])
            if existing and existing["id"] != project_id:
                raise ValueError(f"Project with identifier '{update_dict['identifier']}' already exists")

        # Add updated timestamp
        update_dict["updated_at"] = firestore.SERVER_TIMESTAMP

        # Update document
        doc_ref.update(update_dict)

        # Return updated project
        updated_doc = doc_ref.get()
        project = updated_doc.to_dict()
        project["id"] = updated_doc.id
        return project

    @staticmethod
    def delete_project(db: firestore.Client, project_id: str) -> bool:
        """
        Delete a project and cascade delete all related entities.

        Deletes:
        - The project itself
        - All tickets belonging to this project
        - All labels belonging to this project
        - All cycles belonging to this project
        - All modules belonging to this project
        """
        doc_ref = db.collection(ProjectService.COLLECTION).document(project_id)

        # Check if project exists
        if not doc_ref.get().exists:
            return False

        # Cascade delete related entities using batches
        # Firestore batches can hold max 500 operations, so we need to handle pagination

        def delete_collection_where(collection_name: str, field: str, value: str):
            """Helper to delete all documents in a collection matching a condition."""
            col_ref = db.collection(collection_name)
            query = col_ref.where(filter=FieldFilter(field, "==", value))
            docs = list(query.stream())

            # Delete in batches of 500
            batch_size = 500
            for i in range(0, len(docs), batch_size):
                batch = db.batch()
                for doc in docs[i:i + batch_size]:
                    batch.delete(doc.reference)
                batch.commit()

        # Delete all related entities
        delete_collection_where("tickets", "project_id", project_id)
        delete_collection_where("labels", "project_id", project_id)
        delete_collection_where("cycles", "project_id", project_id)
        delete_collection_where("modules", "project_id", project_id)

        # Finally, delete the project itself
        doc_ref.delete()

        return True


# Singleton instance
project_service = ProjectService()
