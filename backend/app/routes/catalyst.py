from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.models.schemas import TicketCreate, TicketUpdate, TicketOut, TicketListOut
from app.services.db_service import get_db
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["Tickets"])

ticket_service = TicketService()


@router.post("/", response_model=TicketOut)
def create_ticket(ticket: TicketCreate, db: Session = Depends(get_db)):
    """Create a new ticket"""
    try:
        created_ticket = ticket_service.create_ticket(db, ticket)
        return created_ticket
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ticket creation failed: {str(e)}")


@router.get("/", response_model=TicketListOut)
def list_tickets(db: Session = Depends(get_db)):
    """Get all tickets, ordered by creation date"""
    try:
        tickets = ticket_service.get_all_tickets(db)
        return {"tickets": tickets, "total": len(tickets)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tickets: {str(e)}")


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Retrieve a single ticket by ID"""
    ticket = ticket_service.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.put("/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, update_data: TicketUpdate, db: Session = Depends(get_db)):
    """Update an existing ticket"""
    try:
        updated_ticket = ticket_service.update_ticket(db, ticket_id, update_data)
        if not updated_ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return updated_ticket
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ticket update failed: {str(e)}")


@router.delete("/{ticket_id}")
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Delete a ticket by ID"""
    try:
        deleted = ticket_service.delete_ticket(db, ticket_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return {"message": f"Ticket {ticket_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ticket deletion failed: {str(e)}")
