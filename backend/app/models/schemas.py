from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class MeetingNotesRequest(BaseModel):
    notes: str = Field(..., description="Raw meeting notes text")
    output_type: str = Field(..., description="Type of deliverable to generate (prd, user_story, action_items, summary)")

class ProcessedOutput(BaseModel):
    content: str = Field(..., description="Processed content from AI")
    output_type: str = Field(..., description="Type of deliverable generated")

class NotionExportRequest(BaseModel):
    content: str = Field(..., description="Content to export to Notion")
    page_title: str = Field(..., description="Title of the Notion page")
    database_id: Optional[str] = Field(None, description="Notion database ID if exporting to database")

class NotionExportResponse(BaseModel):
    success: bool
    notion_url: Optional[str] = Field(None, description="URL of created Notion page")
    message: str

class ActionItem(BaseModel):
    task: str
    assignee: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[str] = None

class UserStory(BaseModel):
    title: str
    as_a: str
    i_want: str
    so_that: str
    acceptance_criteria: List[str]

class PRDSection(BaseModel):
    section: str
    content: str
