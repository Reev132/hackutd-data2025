from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.orm import Project
from app.models.schemas import ProjectCreate, ProjectUpdate


class ProjectService:
    @staticmethod
    def create_project(db: Session, project_data: ProjectCreate) -> Project:
        """Create a new project"""
        db_project = Project(**project_data.model_dump())
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        return db_project

    @staticmethod
    def get_all_projects(db: Session) -> List[Project]:
        """Get all projects ordered by creation date"""
        return db.query(Project).order_by(Project.created_at.desc()).all()

    @staticmethod
    def get_project_by_id(db: Session, project_id: int) -> Optional[Project]:
        """Get a single project by ID"""
        return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def get_project_by_identifier(db: Session, identifier: str) -> Optional[Project]:
        """Get a single project by identifier (e.g., 'HACK')"""
        return db.query(Project).filter(Project.identifier == identifier).first()

    @staticmethod
    def update_project(db: Session, project_id: int, update_data: ProjectUpdate) -> Optional[Project]:
        """Update a project"""
        db_project = db.query(Project).filter(Project.id == project_id).first()
        if not db_project:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(db_project, key, value)

        db.commit()
        db.refresh(db_project)
        return db_project

    @staticmethod
    def delete_project(db: Session, project_id: int) -> bool:
        """Delete a project (cascades to tickets, labels, cycles, modules)"""
        db_project = db.query(Project).filter(Project.id == project_id).first()
        if not db_project:
            return False

        db.delete(db_project)
        db.commit()
        return True


# Singleton instance
project_service = ProjectService()
