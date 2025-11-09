from sqlalchemy.orm import declarative_base, relationship
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
    ForeignKey,
    Table,
    Float,
)
from .enums import TicketStatus, Priority, CycleStatus

Base = declarative_base()

# Association table for many-to-many relationship between tickets and labels
ticket_labels = Table(
    "ticket_labels",
    Base.metadata,
    Column("ticket_id", Integer, ForeignKey("tickets.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", Integer, ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, unique=True)
    avatar_url = Column(String(500), nullable=True)
    color = Column(String(7), nullable=True)  # Hex color for avatar
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    assigned_tickets = relationship("Ticket", back_populates="assignee_user", foreign_keys="[Ticket.assignee_id]")

    __table_args__ = (
        Index("ix_users_email", "email"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} name={self.name!r}>"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    identifier = Column(String(10), nullable=False, unique=True)  # Short code like "HACK"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tickets = relationship("Ticket", back_populates="project", cascade="all, delete-orphan")
    labels = relationship("Label", back_populates="project", cascade="all, delete-orphan")
    cycles = relationship("Cycle", back_populates="project", cascade="all, delete-orphan")
    modules = relationship("Module", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name!r}>"


class Label(Base):
    __tablename__ = "labels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    color = Column(String(7), nullable=True)  # Hex color code like #FF5733
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="labels")
    tickets = relationship("Ticket", secondary=ticket_labels, back_populates="labels")

    __table_args__ = (
        Index("ix_labels_project_id", "project_id"),
    )

    def __repr__(self) -> str:
        return f"<Label id={self.id} name={self.name!r}>"


class Cycle(Base):
    __tablename__ = "cycles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum(CycleStatus), nullable=False, default=CycleStatus.planned)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="cycles")
    tickets = relationship("Ticket", back_populates="cycle")

    __table_args__ = (
        Index("ix_cycles_project_id", "project_id"),
        Index("ix_cycles_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Cycle id={self.id} name={self.name!r}>"


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=True)
    lead_id = Column(String(255), nullable=True)  # User identifier
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="modules")
    tickets = relationship("Ticket", back_populates="module")

    __table_args__ = (
        Index("ix_modules_project_id", "project_id"),
    )

    def __repr__(self) -> str:
        return f"<Module id={self.id} name={self.name!r}>"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)

    # Dates
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # Assignment and status
    assignee = Column(String(255), nullable=True)  # Keep for backward compatibility
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum(TicketStatus), nullable=False, default=TicketStatus.open)
    priority = Column(Enum(Priority), nullable=False, default=Priority.none)

    # Estimation
    estimated_hours = Column(Float, nullable=True)

    # Foreign keys
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)  # nullable for migration
    cycle_id = Column(Integer, ForeignKey("cycles.id", ondelete="SET NULL"), nullable=True)
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="SET NULL"), nullable=True)
    parent_ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    project = relationship("Project", back_populates="tickets")
    cycle = relationship("Cycle", back_populates="tickets")
    module = relationship("Module", back_populates="tickets")
    parent = relationship("Ticket", remote_side=[id], foreign_keys=[parent_ticket_id], backref="subtasks")
    labels = relationship("Label", secondary=ticket_labels, back_populates="tickets")
    assignee_user = relationship("User", back_populates="assigned_tickets", foreign_keys=[assignee_id])

    __table_args__ = (
        Index("ix_tickets_status", "status"),
        Index("ix_tickets_assignee", "assignee"),
        Index("ix_tickets_created_at", "created_at"),
        Index("ix_tickets_project_id", "project_id"),
        Index("ix_tickets_priority", "priority"),
    )

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} title={self.title!r} status={self.status}>"
