"""
Mermaid diagram generation routes.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.nemotron_service import generate_mermaid_from_prompt


router = APIRouter(prefix="/mermaid", tags=["Mermaid"])


class MermaidRequest(BaseModel):
    """Request model for Mermaid diagram generation."""
    prompt: str


@router.post("/generate")
async def generate_mermaid(request: MermaidRequest):
    """
    Generate a Mermaid diagram from a text prompt.

    This endpoint uses NVIDIA Nemotron to convert natural language
    descriptions into Mermaid diagram syntax.

    Args:
        request: MermaidRequest with prompt field

    Returns:
        Dict with 'mermaid' field containing the diagram syntax
    """
    try:
        mermaid = generate_mermaid_from_prompt(request.prompt)
        return {"mermaid": mermaid}
    except ValueError as e:
        # Handle API key or validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle generation errors
        raise HTTPException(status_code=500, detail=f"Failed to generate diagram: {str(e)}")
