from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    Enum,
    Index,
    func,
)
from .enums import TicketStatus

Base = declarative_base()

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    assignee = Column(String(255), nullable=True)
    status = Column(Enum(TicketStatus), nullable=False, default=TicketStatus.open)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_tickets_status", "status"),
        Index("ix_tickets_assignee", "assignee"),
        Index("ix_tickets_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} title={self.title!r} status={self.status}>"
