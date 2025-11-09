from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from .enums import TicketStatus, Priority, CycleStatus


# ============================================================================
# PROJECT SCHEMAS
# ============================================================================

class ProjectBase(BaseModel):
    name: str = Field(..., max_length=255)
    identifier: str = Field(..., max_length=10)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    identifier: Optional[str] = Field(None, max_length=10)
    description: Optional[str] = None


class ProjectOut(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectListOut(BaseModel):
    projects: List[ProjectOut]
    total: int


# ============================================================================
# LABEL SCHEMAS
# ============================================================================

class LabelBase(BaseModel):
    name: str = Field(..., max_length=100)
    color: Optional[str] = Field(None, max_length=7)
    project_id: str


class LabelCreate(LabelBase):
    pass


class LabelUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=7)


class LabelOut(BaseModel):
    id: str
    name: str
    color: Optional[str]
    project_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class LabelListOut(BaseModel):
    labels: List[LabelOut]
    total: int


# ============================================================================
# CYCLE SCHEMAS
# ============================================================================

class CycleBase(BaseModel):
    name: str = Field(..., max_length=255)
    project_id: str
    start_date: date
    end_date: date
    status: CycleStatus = CycleStatus.planned


class CycleCreate(CycleBase):
    pass


class CycleUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[CycleStatus] = None


class CycleOut(CycleBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CycleListOut(BaseModel):
    cycles: List[CycleOut]
    total: int


# ============================================================================
# MODULE SCHEMAS
# ============================================================================

class ModuleBase(BaseModel):
    name: str = Field(..., max_length=255)
    project_id: str
    description: Optional[str] = None
    lead_id: Optional[str] = Field(None, max_length=255)


class ModuleCreate(ModuleBase):
    pass


class ModuleUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    lead_id: Optional[str] = Field(None, max_length=255)


class ModuleOut(ModuleBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModuleListOut(BaseModel):
    modules: List[ModuleOut]
    total: int


# ============================================================================
# TICKET SCHEMAS (Updated with relationships)
# ============================================================================

# Minimal schemas for nested relationships to avoid circular imports
class LabelMinimal(BaseModel):
    id: str
    name: str
    color: Optional[str]

    class Config:
        from_attributes = True


class ProjectMinimal(BaseModel):
    id: str
    name: str
    identifier: str

    class Config:
        from_attributes = True


class CycleMinimal(BaseModel):
    id: str
    name: str
    start_date: date
    end_date: date

    class Config:
        from_attributes = True


class ModuleMinimal(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


class TicketMinimal(BaseModel):
    id: str
    title: str
    status: TicketStatus

    class Config:
        from_attributes = True


class UserMinimal(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    color: Optional[str] = None

    class Config:
        from_attributes = True


class TicketBase(BaseModel):
    title: str = Field(..., max_length=255)
    summary: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    assignee: Optional[str] = Field(None, max_length=255)  # Keep for backward compatibility
    assignee_id: Optional[str] = None
    status: TicketStatus = TicketStatus.open
    priority: Priority = Priority.none
    estimated_hours: Optional[float] = None
    project_id: Optional[str] = None
    cycle_id: Optional[str] = None
    module_id: Optional[str] = None
    parent_ticket_id: Optional[str] = None


class TicketCreate(TicketBase):
    label_ids: Optional[List[str]] = Field(default_factory=list)


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    summary: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    assignee: Optional[str] = Field(None, max_length=255)  # Keep for backward compatibility
    assignee_id: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[Priority] = None
    estimated_hours: Optional[float] = None
    project_id: Optional[str] = None
    cycle_id: Optional[str] = None
    module_id: Optional[str] = None
    parent_ticket_id: Optional[str] = None
    label_ids: Optional[List[str]] = None


class TicketOut(TicketBase):
    id: str
    created_at: datetime
    updated_at: datetime

    # Nested relationships
    project: Optional[ProjectMinimal] = None
    cycle: Optional[CycleMinimal] = None
    module: Optional[ModuleMinimal] = None
    parent: Optional[TicketMinimal] = None
    labels: List[LabelMinimal] = Field(default_factory=list)
    subtasks: List[TicketMinimal] = Field(default_factory=list)
    assignee_user: Optional[UserMinimal] = None

    class Config:
        from_attributes = True


class TicketListOut(BaseModel):
    tickets: List[TicketOut]
    total: int


# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    name: str = Field(..., max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, max_length=7)


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, max_length=7)


class UserOut(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListOut(BaseModel):
    users: List[UserOut]
    total: int
