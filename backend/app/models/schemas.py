from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from .enums import TicketStatus

# Shared fields that both create and update can reuse
class TicketBase(BaseModel):
    title: str = Field(..., max_length=255)
    summary: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    assignee: Optional[str] = Field(None, max_length=255)
    status: TicketStatus = TicketStatus.open

# Request schema for POST
class TicketCreate(TicketBase):
    pass

# Request schema for PUT
class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    summary: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    assignee: Optional[str] = Field(None, max_length=255)
    status: Optional[TicketStatus] = None

# Response schema for a single ticket
class TicketOut(TicketBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2
        json_encoders = {}

# Response schema for list endpoints
class TicketListOut(BaseModel):
    tickets: List[TicketOut]
    total: int

    class Config:
        from_attributes = True
