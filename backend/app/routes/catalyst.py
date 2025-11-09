from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.schemas import (
    # Project schemas
    ProjectCreate, ProjectUpdate, ProjectOut, ProjectListOut,
    # Label schemas
    LabelCreate, LabelUpdate, LabelOut, LabelListOut,
    # Cycle schemas
    CycleCreate, CycleUpdate, CycleOut, CycleListOut,
    # Module schemas
    ModuleCreate, ModuleUpdate, ModuleOut, ModuleListOut,
    # Ticket schemas
    TicketCreate, TicketUpdate, TicketOut, TicketListOut,
    # User schemas
    UserCreate, UserUpdate, UserOut, UserListOut,
)
from app.services.db_service import get_db
from app.services.project_service import project_service
from app.services.label_service import label_service
from app.services.cycle_service import cycle_service
from app.services.module_service import module_service
from app.services.ticket_service import ticket_service
from app.services.user_service import user_service


# Main router that will be included in the app
router = APIRouter()


# ============================================================================
# PROJECT ROUTES
# ============================================================================

project_router = APIRouter(prefix="/projects", tags=["Projects"])


@project_router.post("/", response_model=ProjectOut, status_code=201)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project"""
    try:
        created_project = project_service.create_project(db, project)
        return created_project
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Project creation failed: {str(e)}")


@project_router.get("/", response_model=ProjectListOut)
def list_projects(db: Session = Depends(get_db)):
    """Get all projects"""
    try:
        projects = project_service.get_all_projects(db)
        return {"projects": projects, "total": len(projects)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")


@project_router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get a single project by ID"""
    project = project_service.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@project_router.put("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, update_data: ProjectUpdate, db: Session = Depends(get_db)):
    """Update a project"""
    try:
        updated_project = project_service.update_project(db, project_id, update_data)
        if not updated_project:
            raise HTTPException(status_code=404, detail="Project not found")
        return updated_project
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Project update failed: {str(e)}")


@project_router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Delete a project"""
    try:
        deleted = project_service.delete_project(db, project_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"message": f"Project {project_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Project deletion failed: {str(e)}")


# ============================================================================
# LABEL ROUTES
# ============================================================================

label_router = APIRouter(prefix="/labels", tags=["Labels"])


@label_router.post("/", response_model=LabelOut, status_code=201)
def create_label(label: LabelCreate, db: Session = Depends(get_db)):
    """Create a new label"""
    try:
        created_label = label_service.create_label(db, label)
        return created_label
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Label creation failed: {str(e)}")


@label_router.get("/", response_model=LabelListOut)
def list_labels(project_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """Get all labels, optionally filtered by project"""
    try:
        labels = label_service.get_all_labels(db, project_id)
        return {"labels": labels, "total": len(labels)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch labels: {str(e)}")


@label_router.get("/{label_id}", response_model=LabelOut)
def get_label(label_id: int, db: Session = Depends(get_db)):
    """Get a single label by ID"""
    label = label_service.get_label_by_id(db, label_id)
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    return label


@label_router.put("/{label_id}", response_model=LabelOut)
def update_label(label_id: int, update_data: LabelUpdate, db: Session = Depends(get_db)):
    """Update a label"""
    try:
        updated_label = label_service.update_label(db, label_id, update_data)
        if not updated_label:
            raise HTTPException(status_code=404, detail="Label not found")
        return updated_label
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Label update failed: {str(e)}")


@label_router.delete("/{label_id}")
def delete_label(label_id: int, db: Session = Depends(get_db)):
    """Delete a label"""
    try:
        deleted = label_service.delete_label(db, label_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Label not found")
        return {"message": f"Label {label_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Label deletion failed: {str(e)}")


# ============================================================================
# CYCLE ROUTES
# ============================================================================

cycle_router = APIRouter(prefix="/cycles", tags=["Cycles"])


@cycle_router.post("/", response_model=CycleOut, status_code=201)
def create_cycle(cycle: CycleCreate, db: Session = Depends(get_db)):
    """Create a new cycle"""
    try:
        created_cycle = cycle_service.create_cycle(db, cycle)
        return created_cycle
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cycle creation failed: {str(e)}")


@cycle_router.get("/", response_model=CycleListOut)
def list_cycles(project_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """Get all cycles, optionally filtered by project"""
    try:
        cycles = cycle_service.get_all_cycles(db, project_id)
        return {"cycles": cycles, "total": len(cycles)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch cycles: {str(e)}")


@cycle_router.get("/{cycle_id}", response_model=CycleOut)
def get_cycle(cycle_id: int, db: Session = Depends(get_db)):
    """Get a single cycle by ID"""
    cycle = cycle_service.get_cycle_by_id(db, cycle_id)
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    return cycle


@cycle_router.put("/{cycle_id}", response_model=CycleOut)
def update_cycle(cycle_id: int, update_data: CycleUpdate, db: Session = Depends(get_db)):
    """Update a cycle"""
    try:
        updated_cycle = cycle_service.update_cycle(db, cycle_id, update_data)
        if not updated_cycle:
            raise HTTPException(status_code=404, detail="Cycle not found")
        return updated_cycle
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cycle update failed: {str(e)}")


@cycle_router.delete("/{cycle_id}")
def delete_cycle(cycle_id: int, db: Session = Depends(get_db)):
    """Delete a cycle"""
    try:
        deleted = cycle_service.delete_cycle(db, cycle_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Cycle not found")
        return {"message": f"Cycle {cycle_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cycle deletion failed: {str(e)}")


# ============================================================================
# MODULE ROUTES
# ============================================================================

module_router = APIRouter(prefix="/modules", tags=["Modules"])


@module_router.post("/", response_model=ModuleOut, status_code=201)
def create_module(module: ModuleCreate, db: Session = Depends(get_db)):
    """Create a new module"""
    try:
        created_module = module_service.create_module(db, module)
        return created_module
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Module creation failed: {str(e)}")


@module_router.get("/", response_model=ModuleListOut)
def list_modules(project_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """Get all modules, optionally filtered by project"""
    try:
        modules = module_service.get_all_modules(db, project_id)
        return {"modules": modules, "total": len(modules)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch modules: {str(e)}")


@module_router.get("/{module_id}", response_model=ModuleOut)
def get_module(module_id: int, db: Session = Depends(get_db)):
    """Get a single module by ID"""
    module = module_service.get_module_by_id(db, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module


@module_router.put("/{module_id}", response_model=ModuleOut)
def update_module(module_id: int, update_data: ModuleUpdate, db: Session = Depends(get_db)):
    """Update a module"""
    try:
        updated_module = module_service.update_module(db, module_id, update_data)
        if not updated_module:
            raise HTTPException(status_code=404, detail="Module not found")
        return updated_module
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Module update failed: {str(e)}")


@module_router.delete("/{module_id}")
def delete_module(module_id: int, db: Session = Depends(get_db)):
    """Delete a module"""
    try:
        deleted = module_service.delete_module(db, module_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Module not found")
        return {"message": f"Module {module_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Module deletion failed: {str(e)}")


# ============================================================================
# TICKET ROUTES (Updated)
# ============================================================================

ticket_router = APIRouter(prefix="/tickets", tags=["Tickets"])


@ticket_router.post("/", response_model=TicketOut, status_code=201)
def create_ticket(ticket: TicketCreate, db: Session = Depends(get_db)):
    """Create a new ticket"""
    try:
        created_ticket = ticket_service.create_ticket(db, ticket)
        return created_ticket
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ticket creation failed: {str(e)}")


@ticket_router.get("/")
def list_tickets(project_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """Get all tickets, optionally filtered by project"""
    try:
        tickets = ticket_service.get_all_tickets(db, project_id)
        # Serialize tickets manually to handle missing assignee_user gracefully
        from app.models.schemas import TicketOut
        serialized_tickets = []
        for ticket in tickets:
            try:
                # Try normal serialization first
                ticket_out = TicketOut.model_validate(ticket)
                serialized_tickets.append(ticket_out.model_dump())
            except Exception:
                # If serialization fails (e.g., due to missing assignee_user relationship),
                # manually construct the dict
                ticket_dict = {
                    "id": ticket.id,
                    "title": ticket.title,
                    "summary": ticket.summary,
                    "start_date": ticket.start_date,
                    "end_date": ticket.end_date,
                    "assignee": ticket.assignee,
                    "assignee_id": getattr(ticket, "assignee_id", None),
                    "status": ticket.status,
                    "priority": ticket.priority,
                    "estimated_hours": ticket.estimated_hours,
                    "project_id": ticket.project_id,
                    "cycle_id": ticket.cycle_id,
                    "module_id": ticket.module_id,
                    "parent_ticket_id": ticket.parent_ticket_id,
                    "created_at": ticket.created_at,
                    "updated_at": ticket.updated_at,
                    "project": {"id": ticket.project.id, "name": ticket.project.name, "identifier": ticket.project.identifier} if ticket.project else None,
                    "cycle": {"id": ticket.cycle.id, "name": ticket.cycle.name, "start_date": ticket.cycle.start_date, "end_date": ticket.cycle.end_date} if ticket.cycle else None,
                    "module": {"id": ticket.module.id, "name": ticket.module.name} if ticket.module else None,
                    "parent": {"id": ticket.parent.id, "title": ticket.parent.title, "status": ticket.parent.status} if ticket.parent else None,
                    "labels": [{"id": label.id, "name": label.name, "color": label.color} for label in ticket.labels],
                    "subtasks": [{"id": subtask.id, "title": subtask.title, "status": subtask.status} for subtask in ticket.subtasks],
                    "assignee_user": None,
                }
                # Try to get assignee_user if column exists
                try:
                    if hasattr(ticket, "assignee_id") and ticket.assignee_id:
                        # Check if assignee_user attribute exists and can be accessed
                        assignee_user = getattr(ticket, "assignee_user", None)
                        if assignee_user:
                            ticket_dict["assignee_user"] = {
                                "id": assignee_user.id,
                                "name": assignee_user.name,
                                "email": assignee_user.email,
                                "avatar_url": assignee_user.avatar_url,
                                "color": assignee_user.color,
                            }
                except Exception:
                    pass  # If assignee_user can't be accessed, leave it as None
                serialized_tickets.append(ticket_dict)
        return {"tickets": serialized_tickets, "total": len(serialized_tickets)}
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Failed to fetch tickets: {str(e)}\n{traceback.format_exc()}")


@ticket_router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Retrieve a single ticket by ID"""
    ticket = ticket_service.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@ticket_router.put("/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, update_data: TicketUpdate, db: Session = Depends(get_db)):
    """Update an existing ticket"""
    try:
        updated_ticket = ticket_service.update_ticket(db, ticket_id, update_data)
        if not updated_ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return updated_ticket
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ticket update failed: {str(e)}")


@ticket_router.delete("/{ticket_id}")
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Delete a ticket by ID"""
    try:
        deleted = ticket_service.delete_ticket(db, ticket_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return {"message": f"Ticket {ticket_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ticket deletion failed: {str(e)}")


# ============================================================================
# USER ROUTES
# ============================================================================

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.post("/", response_model=UserOut, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    try:
        created_user = user_service.create_user(db, user)
        return created_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User creation failed: {str(e)}")


@user_router.get("/", response_model=UserListOut)
def list_users(db: Session = Depends(get_db)):
    """Get all users"""
    try:
        users = user_service.get_all_users(db)
        return {"users": users, "total": len(users)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")


@user_router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Retrieve a single user by ID"""
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@user_router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, update_data: UserUpdate, db: Session = Depends(get_db)):
    """Update an existing user"""
    try:
        updated_user = user_service.update_user(db, user_id, update_data)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return updated_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User update failed: {str(e)}")


@user_router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user by ID"""
    try:
        success = user_service.delete_user(db, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User deletion failed: {str(e)}")


# ============================================================================
# Include all sub-routers in the main router
# ============================================================================

router.include_router(project_router)
router.include_router(label_router)
router.include_router(cycle_router)
router.include_router(module_router)
router.include_router(ticket_router)
router.include_router(user_router)
