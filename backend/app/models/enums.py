import enum

class TicketStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"

class Priority(str, enum.Enum):
    urgent = "urgent"
    high = "high"
    medium = "medium"
    low = "low"
    none = "none"

class CycleStatus(str, enum.Enum):
    planned = "planned"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"
