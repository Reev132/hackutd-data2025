from sqlalchemy.orm import Session, joinedload
from sqlalchemy import inspect, text
from typing import List, Optional
from app.models.orm import Ticket, Label, User
from app.models.schemas import TicketCreate, TicketUpdate


class TicketService:
    @staticmethod
    def create_ticket(db: Session, ticket_data: TicketCreate) -> Ticket:
        """Create a new ticket with optional label relationships"""
        # Check if assignee_id column exists
        try:
            inspector = inspect(db.bind)
            if "tickets" in inspector.get_table_names():
                columns = [col["name"] for col in inspector.get_columns("tickets")]
                has_assignee_id = "assignee_id" in columns
            else:
                has_assignee_id = False
        except Exception:
            has_assignee_id = False
        
        # Extract label_ids before creating ticket
        data_dict = ticket_data.model_dump(exclude={'label_ids'})
        label_ids = ticket_data.label_ids or []
        
        # If assignee_id column doesn't exist, use raw SQL to insert
        if not has_assignee_id:
            # Remove assignee_id from data
            if 'assignee_id' in data_dict:
                del data_dict['assignee_id']
            
            # Build INSERT SQL dynamically
            columns_to_insert = list(data_dict.keys())
            placeholders = [f":{col}" for col in columns_to_insert]
            
            insert_sql = f"""
                INSERT INTO tickets ({', '.join(columns_to_insert)})
                VALUES ({', '.join(placeholders)})
            """
            
            result = db.execute(text(insert_sql), data_dict)
            db.commit()
            
            # Get the last inserted row id
            ticket_id = result.lastrowid
            
            # Add labels if provided
            if label_ids:
                for label_id in label_ids:
                    db.execute(
                        text("INSERT INTO ticket_labels (ticket_id, label_id) VALUES (:ticket_id, :label_id)"),
                        {"ticket_id": ticket_id, "label_id": label_id}
                    )
                db.commit()
            
            # Fetch and return the created ticket using raw SQL
            ticket_result = db.execute(
                text("""
                    SELECT id, title, summary, start_date, end_date, assignee, 
                           status, priority, estimated_hours, project_id, cycle_id, 
                           module_id, parent_ticket_id, created_at, updated_at
                    FROM tickets
                    WHERE id = :ticket_id
                """),
                {"ticket_id": ticket_id}
            ).first()
            
            if not ticket_result:
                raise Exception("Failed to retrieve created ticket")
            
            # Construct ticket object
            from app.models.orm import Project, Cycle, Module
            ticket = Ticket()
            ticket.id = ticket_result.id
            ticket.title = ticket_result.title
            ticket.summary = ticket_result.summary
            ticket.start_date = ticket_result.start_date
            ticket.end_date = ticket_result.end_date
            ticket.assignee = ticket_result.assignee
            ticket.status = ticket_result.status
            ticket.priority = ticket_result.priority
            ticket.estimated_hours = ticket_result.estimated_hours
            ticket.project_id = ticket_result.project_id
            ticket.cycle_id = ticket_result.cycle_id
            ticket.module_id = ticket_result.module_id
            ticket.parent_ticket_id = ticket_result.parent_ticket_id
            ticket.created_at = ticket_result.created_at
            ticket.updated_at = ticket_result.updated_at
            ticket.assignee_id = None
            
            # Load relationships
            if ticket.project_id:
                ticket.project = db.query(Project).filter_by(id=ticket.project_id).first()
            if ticket.cycle_id:
                ticket.cycle = db.query(Cycle).filter_by(id=ticket.cycle_id).first()
            if ticket.module_id:
                ticket.module = db.query(Module).filter_by(id=ticket.module_id).first()
            
            # Load parent using raw SQL
            if ticket.parent_ticket_id:
                parent_result = db.execute(
                    text("SELECT id, title, status FROM tickets WHERE id = :parent_id"),
                    {"parent_id": ticket.parent_ticket_id}
                ).first()
                if parent_result:
                    parent = Ticket()
                    parent.id = parent_result.id
                    parent.title = parent_result.title
                    parent.status = parent_result.status
                    ticket.parent = parent
            
            # Load labels
            if label_ids:
                ticket.labels = db.query(Label).filter(Label.id.in_(label_ids)).all()
            else:
                ticket.labels = []
            
            ticket.subtasks = []
            
            return ticket
        
        # Normal path when assignee_id exists
        # Create ticket
        db_ticket = Ticket(**data_dict)

        # Add labels if provided
        if label_ids:
            labels = db.query(Label).filter(Label.id.in_(label_ids)).all()
            db_ticket.labels = labels

        db.add(db_ticket)
        db.commit()
        db.refresh(db_ticket)
        return db_ticket

    @staticmethod
    def get_all_tickets(db: Session, project_id: Optional[int] = None) -> List[Ticket]:
        """Get all tickets, optionally filtered by project"""
        # Check if assignee_id column exists
        try:
            inspector = inspect(db.bind)
            if "tickets" in inspector.get_table_names():
                columns = [col["name"] for col in inspector.get_columns("tickets")]
                has_assignee_id = "assignee_id" in columns
                has_users_table = "users" in inspector.get_table_names()
            else:
                has_assignee_id = False
                has_users_table = False
        except Exception:
            has_assignee_id = False
            has_users_table = False
        
        # If assignee_id doesn't exist, we need to query without it
        # We'll use a workaround: query all columns except assignee_id
        if not has_assignee_id:
            # Use raw SQL to select only existing columns
            sql = """
                SELECT id, title, summary, start_date, end_date, assignee, 
                       status, priority, estimated_hours, project_id, cycle_id, 
                       module_id, parent_ticket_id, created_at, updated_at
                FROM tickets
            """
            params = {}
            if project_id is not None:
                sql += " WHERE project_id = :project_id"
                params["project_id"] = project_id
            sql += " ORDER BY created_at DESC"
            
            result = db.execute(text(sql), params)
            tickets = []
            for row in result:
                # Create a Ticket-like object without assignee_id
                ticket = Ticket()
                ticket.id = row.id
                ticket.title = row.title
                ticket.summary = row.summary
                ticket.start_date = row.start_date
                ticket.end_date = row.end_date
                ticket.assignee = row.assignee
                ticket.status = row.status
                ticket.priority = row.priority
                ticket.estimated_hours = row.estimated_hours
                ticket.project_id = row.project_id
                ticket.cycle_id = row.cycle_id
                ticket.module_id = row.module_id
                ticket.parent_ticket_id = row.parent_ticket_id
                ticket.created_at = row.created_at
                ticket.updated_at = row.updated_at
                # Set assignee_id to None since it doesn't exist
                ticket.assignee_id = None
                tickets.append(ticket)
            
            # Load relationships manually
            from app.models.orm import Project, Cycle, Module
            for ticket in tickets:
                if ticket.project_id:
                    ticket.project = db.query(Project).filter_by(id=ticket.project_id).first()
                if ticket.cycle_id:
                    ticket.cycle = db.query(Cycle).filter_by(id=ticket.cycle_id).first()
                if ticket.module_id:
                    ticket.module = db.query(Module).filter_by(id=ticket.module_id).first()
                
                # Load parent ticket using raw SQL to avoid assignee_id issue
                if ticket.parent_ticket_id:
                    parent_result = db.execute(
                        text("""
                            SELECT id, title, status
                            FROM tickets
                            WHERE id = :parent_id
                        """),
                        {"parent_id": ticket.parent_ticket_id}
                    ).first()
                    if parent_result:
                        parent = Ticket()
                        parent.id = parent_result.id
                        parent.title = parent_result.title
                        parent.status = parent_result.status
                        ticket.parent = parent
                    else:
                        ticket.parent = None
                else:
                    ticket.parent = None
                
                # Load labels using the association table
                label_result = db.execute(
                    text("SELECT label_id FROM ticket_labels WHERE ticket_id = :ticket_id"),
                    {"ticket_id": ticket.id}
                )
                label_ids = [row[0] for row in label_result]
                if label_ids:
                    ticket.labels = db.query(Label).filter(Label.id.in_(label_ids)).all()
                else:
                    ticket.labels = []
                
                # Load subtasks (skip for now if assignee_id doesn't exist to avoid recursion)
                ticket.subtasks = []
            
            return tickets
        
        # Normal query path (when assignee_id exists)
        query = db.query(Ticket)
        if has_assignee_id and has_users_table:
            try:
                query = query.options(joinedload(Ticket.assignee_user))
            except Exception:
                pass
        
        if project_id is not None:
            query = query.filter(Ticket.project_id == project_id)
        
        return query.order_by(Ticket.created_at.desc()).all()

    @staticmethod
    def get_ticket_by_id(db: Session, ticket_id: int) -> Optional[Ticket]:
        """Get a single ticket by ID with all relationships loaded"""
        query = db.query(Ticket)
        
        # Try to eager load assignee_user if possible (only if column exists)
        try:
            inspector = inspect(db.bind)
            if "tickets" in inspector.get_table_names():
                columns = [col["name"] for col in inspector.get_columns("tickets")]
                if "assignee_id" in columns and "users" in inspector.get_table_names():
                    query = query.options(joinedload(Ticket.assignee_user))
        except Exception:
            # If inspection fails, continue without eager loading
            pass
        
        # Execute query and handle any relationship errors
        try:
            return query.filter(Ticket.id == ticket_id).first()
        except Exception:
            # If query fails (e.g., due to missing column), retry without eager loading
            return db.query(Ticket).filter(Ticket.id == ticket_id).first()

    @staticmethod
    def update_ticket(db: Session, ticket_id: int, update_data: TicketUpdate) -> Optional[Ticket]:
        """Update a ticket including label relationships"""
        # Check if assignee_id column exists
        try:
            inspector = inspect(db.bind)
            if "tickets" in inspector.get_table_names():
                columns = [col["name"] for col in inspector.get_columns("tickets")]
                has_assignee_id = "assignee_id" in columns
            else:
                has_assignee_id = False
        except Exception:
            has_assignee_id = False
        
        # If assignee_id doesn't exist, use raw SQL to fetch and update
        if not has_assignee_id:
            # First check if ticket exists
            result = db.execute(
                text("SELECT id FROM tickets WHERE id = :ticket_id"),
                {"ticket_id": ticket_id}
            ).first()
            
            if not result:
                return None
            
            # Extract label_ids before updating other fields
            update_dict = update_data.model_dump(exclude_unset=True, exclude={'label_ids'})
            label_ids = update_data.label_ids
            
            # Build UPDATE SQL dynamically for only the fields being updated
            if update_dict:
                set_clauses = []
                params = {"ticket_id": ticket_id}
                for key, value in update_dict.items():
                    set_clauses.append(f"{key} = :{key}")
                    params[key] = value
                
                update_sql = f"UPDATE tickets SET {', '.join(set_clauses)} WHERE id = :ticket_id"
                db.execute(text(update_sql), params)
            
            # Update labels if provided
            if label_ids is not None:
                # Remove existing labels
                db.execute(
                    text("DELETE FROM ticket_labels WHERE ticket_id = :ticket_id"),
                    {"ticket_id": ticket_id}
                )
                # Add new labels
                for label_id in label_ids:
                    db.execute(
                        text("INSERT INTO ticket_labels (ticket_id, label_id) VALUES (:ticket_id, :label_id)"),
                        {"ticket_id": ticket_id, "label_id": label_id}
                    )
            
            db.commit()
            
            # Fetch and return the updated ticket using raw SQL
            ticket_result = db.execute(
                text("""
                    SELECT id, title, summary, start_date, end_date, assignee, 
                           status, priority, estimated_hours, project_id, cycle_id, 
                           module_id, parent_ticket_id, created_at, updated_at
                    FROM tickets
                    WHERE id = :ticket_id
                """),
                {"ticket_id": ticket_id}
            ).first()
            
            if not ticket_result:
                return None
            
            # Construct ticket object
            from app.models.orm import Project, Cycle, Module
            ticket = Ticket()
            ticket.id = ticket_result.id
            ticket.title = ticket_result.title
            ticket.summary = ticket_result.summary
            ticket.start_date = ticket_result.start_date
            ticket.end_date = ticket_result.end_date
            ticket.assignee = ticket_result.assignee
            ticket.status = ticket_result.status
            ticket.priority = ticket_result.priority
            ticket.estimated_hours = ticket_result.estimated_hours
            ticket.project_id = ticket_result.project_id
            ticket.cycle_id = ticket_result.cycle_id
            ticket.module_id = ticket_result.module_id
            ticket.parent_ticket_id = ticket_result.parent_ticket_id
            ticket.created_at = ticket_result.created_at
            ticket.updated_at = ticket_result.updated_at
            ticket.assignee_id = None
            
            # Load relationships
            if ticket.project_id:
                ticket.project = db.query(Project).filter_by(id=ticket.project_id).first()
            if ticket.cycle_id:
                ticket.cycle = db.query(Cycle).filter_by(id=ticket.cycle_id).first()
            if ticket.module_id:
                ticket.module = db.query(Module).filter_by(id=ticket.module_id).first()
            
            # Load parent using raw SQL
            if ticket.parent_ticket_id:
                parent_result = db.execute(
                    text("SELECT id, title, status FROM tickets WHERE id = :parent_id"),
                    {"parent_id": ticket.parent_ticket_id}
                ).first()
                if parent_result:
                    parent = Ticket()
                    parent.id = parent_result.id
                    parent.title = parent_result.title
                    parent.status = parent_result.status
                    ticket.parent = parent
            
            # Load labels
            label_result = db.execute(
                text("SELECT label_id FROM ticket_labels WHERE ticket_id = :ticket_id"),
                {"ticket_id": ticket.id}
            )
            label_ids_loaded = [row[0] for row in label_result]
            if label_ids_loaded:
                ticket.labels = db.query(Label).filter(Label.id.in_(label_ids_loaded)).all()
            else:
                ticket.labels = []
            
            ticket.subtasks = []
            
            return ticket
        
        # Normal path when assignee_id exists
        db_ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not db_ticket:
            return None

        # Extract label_ids before updating other fields
        update_dict = update_data.model_dump(exclude_unset=True, exclude={'label_ids'})
        label_ids = update_data.label_ids

        # Update regular fields
        for key, value in update_dict.items():
            setattr(db_ticket, key, value)

        # Update labels if provided
        if label_ids is not None:
            labels = db.query(Label).filter(Label.id.in_(label_ids)).all()
            db_ticket.labels = labels

        db.commit()
        db.refresh(db_ticket)
        return db_ticket

    @staticmethod
    def delete_ticket(db: Session, ticket_id: int) -> bool:
        """Delete a ticket (cascades to subtasks)"""
        # Check if assignee_id column exists
        try:
            inspector = inspect(db.bind)
            if "tickets" in inspector.get_table_names():
                columns = [col["name"] for col in inspector.get_columns("tickets")]
                has_assignee_id = "assignee_id" in columns
            else:
                has_assignee_id = False
        except Exception:
            has_assignee_id = False
        
        # If assignee_id doesn't exist, use raw SQL to delete
        if not has_assignee_id:
            # Check if ticket exists
            result = db.execute(
                text("SELECT id FROM tickets WHERE id = :ticket_id"),
                {"ticket_id": ticket_id}
            ).first()
            
            if not result:
                return False
            
            # Delete ticket (cascade is handled by database foreign keys)
            db.execute(
                text("DELETE FROM tickets WHERE id = :ticket_id"),
                {"ticket_id": ticket_id}
            )
            db.commit()
            return True
        
        # Normal path when assignee_id exists
        db_ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not db_ticket:
            return False

        db.delete(db_ticket)
        db.commit()
        return True


# Singleton instance
ticket_service = TicketService()
