from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.orm import Label
from app.models.schemas import LabelCreate, LabelUpdate


class LabelService:
    @staticmethod
    def create_label(db: Session, label_data: LabelCreate) -> Label:
        """Create a new label"""
        db_label = Label(**label_data.model_dump())
        db.add(db_label)
        db.commit()
        db.refresh(db_label)
        return db_label

    @staticmethod
    def get_all_labels(db: Session, project_id: Optional[int] = None) -> List[Label]:
        """Get all labels, optionally filtered by project"""
        query = db.query(Label)
        if project_id is not None:
            query = query.filter(Label.project_id == project_id)
        return query.order_by(Label.name).all()

    @staticmethod
    def get_label_by_id(db: Session, label_id: int) -> Optional[Label]:
        """Get a single label by ID"""
        return db.query(Label).filter(Label.id == label_id).first()

    @staticmethod
    def update_label(db: Session, label_id: int, update_data: LabelUpdate) -> Optional[Label]:
        """Update a label"""
        db_label = db.query(Label).filter(Label.id == label_id).first()
        if not db_label:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(db_label, key, value)

        db.commit()
        db.refresh(db_label)
        return db_label

    @staticmethod
    def delete_label(db: Session, label_id: int) -> bool:
        """Delete a label"""
        db_label = db.query(Label).filter(Label.id == label_id).first()
        if not db_label:
            return False

        db.delete(db_label)
        db.commit()
        return True


# Singleton instance
label_service = LabelService()
