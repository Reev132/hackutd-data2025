from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.orm import Cycle
from app.models.schemas import CycleCreate, CycleUpdate


class CycleService:
    @staticmethod
    def create_cycle(db: Session, cycle_data: CycleCreate) -> Cycle:
        """Create a new cycle"""
        db_cycle = Cycle(**cycle_data.model_dump())
        db.add(db_cycle)
        db.commit()
        db.refresh(db_cycle)
        return db_cycle

    @staticmethod
    def get_all_cycles(db: Session, project_id: Optional[int] = None) -> List[Cycle]:
        """Get all cycles, optionally filtered by project"""
        query = db.query(Cycle)
        if project_id is not None:
            query = query.filter(Cycle.project_id == project_id)
        return query.order_by(Cycle.start_date.desc()).all()

    @staticmethod
    def get_cycle_by_id(db: Session, cycle_id: int) -> Optional[Cycle]:
        """Get a single cycle by ID"""
        return db.query(Cycle).filter(Cycle.id == cycle_id).first()

    @staticmethod
    def update_cycle(db: Session, cycle_id: int, update_data: CycleUpdate) -> Optional[Cycle]:
        """Update a cycle"""
        db_cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
        if not db_cycle:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(db_cycle, key, value)

        db.commit()
        db.refresh(db_cycle)
        return db_cycle

    @staticmethod
    def delete_cycle(db: Session, cycle_id: int) -> bool:
        """Delete a cycle (tickets will have cycle_id set to NULL)"""
        db_cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
        if not db_cycle:
            return False

        db.delete(db_cycle)
        db.commit()
        return True


# Singleton instance
cycle_service = CycleService()
