from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    MeetingNotesRequest,
    ProcessedOutput,
    NotionExportRequest,
    NotionExportResponse
)
from app.services.nemotron_service import NemotronService
from app.services.notion_service import NotionService

router = APIRouter()

nemotron_service = NemotronService()
notion_service = NotionService()

@router.post("/process", response_model=ProcessedOutput)
async def process_meeting_notes(request: MeetingNotesRequest):
    """Process meeting notes and generate structured deliverables."""
    try:
        if request.output_type == "prd":
            content = nemotron_service.generate_prd(request.notes)
        elif request.output_type == "user_story":
            content = nemotron_service.generate_user_stories(request.notes)
        elif request.output_type == "action_items":
            content = nemotron_service.generate_action_items(request.notes)
        elif request.output_type == "summary":
            content = nemotron_service.generate_summary(request.notes)
        else:
            raise HTTPException(status_code=400, detail="Invalid output_type")

        return ProcessedOutput(
            content=content,
            output_type=request.output_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export-notion", response_model=NotionExportResponse)
async def export_to_notion(request: NotionExportRequest):
    """Export processed content to Notion."""
    try:
        if request.database_id:
            result = notion_service.add_to_database(
                content=request.content,
                title=request.page_title,
                database_id=request.database_id
            )
        else:
            result = notion_service.create_page(
                content=request.content,
                title=request.page_title
            )

        if result["success"]:
            return NotionExportResponse(
                success=True,
                notion_url=result["url"],
                message="Successfully exported to Notion"
            )
        else:
            # Return detailed error message from Notion service
            raise HTTPException(status_code=400, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notion export failed: {str(e)}")
