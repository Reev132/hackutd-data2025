from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.orm import Module
from app.models.schemas import ModuleCreate, ModuleUpdate


class ModuleService:
    @staticmethod
    def create_module(db: Session, module_data: ModuleCreate) -> Module:
        """Create a new module"""
        db_module = Module(**module_data.model_dump())
        db.add(db_module)
        db.commit()
        db.refresh(db_module)
        return db_module

    @staticmethod
    def get_all_modules(db: Session, project_id: Optional[int] = None) -> List[Module]:
        """Get all modules, optionally filtered by project"""
        query = db.query(Module)
        if project_id is not None:
            query = query.filter(Module.project_id == project_id)
        return query.order_by(Module.name).all()

    @staticmethod
    def get_module_by_id(db: Session, module_id: int) -> Optional[Module]:
        """Get a single module by ID"""
        return db.query(Module).filter(Module.id == module_id).first()

    @staticmethod
    def update_module(db: Session, module_id: int, update_data: ModuleUpdate) -> Optional[Module]:
        """Update a module"""
        db_module = db.query(Module).filter(Module.id == module_id).first()
        if not db_module:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(db_module, key, value)

        db.commit()
        db.refresh(db_module)
        return db_module

    @staticmethod
    def delete_module(db: Session, module_id: int) -> bool:
        """Delete a module (tickets will have module_id set to NULL)"""
        db_module = db.query(Module).filter(Module.id == module_id).first()
        if not db_module:
            return False

        db.delete(db_module)
        db.commit()
        return True


# Singleton instance
module_service = ModuleService()
