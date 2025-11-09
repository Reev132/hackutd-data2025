"""
Voice transcription routes for Deepgram integration.

Handles both live audio streaming and pre-recorded file uploads.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import traceback

from app.services.deepgram_service import deepgram_service
from app.services.agent_service import agent_service
from app.services.firebase_service import get_firestore_client


router = APIRouter(prefix="/api/voice", tags=["Voice"])


# Request/Response models
class ProcessMeetingRequest(BaseModel):
    transcript: str
    project_name: Optional[str] = None


@router.post("/transcribe-file")
async def transcribe_audio_file(file: UploadFile = File(...)):
    """
    Transcribe a pre-recorded audio file.
    
    Supports: MP3, WAV, M4A, WebM, OGG
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    try:
        print(f"[Voice API] Receiving file: {file.filename} ({file.content_type})")
        
        # Read file content
        file_content = await file.read()
        print(f"[Voice API] File size: {len(file_content)} bytes")
        
        # Get mimetype
        mimetype = file.content_type or "audio/wav"
        
        # Run Deepgram in thread pool to prevent blocking with timeout
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    pool,
                    deepgram_service.transcribe_file,
                    file_content,
                    mimetype
                ),
                timeout=120.0  # 2 minute timeout
            )
        
        print(f"[Voice API] Transcription result: {result.get('success')}")
        
        if not result["success"]:
            raise HTTPException(
                status_code=500, 
                detail=f"Transcription failed: {result.get('error', 'Unknown error')}"
            )
        
        return result["data"]
        
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Transcription timed out after 2 minutes. Please try a smaller file."
        )
    except ValueError as e:
        # API key not configured
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        print(f"[Voice API] Error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"File transcription failed: {str(e)}"
        )


@router.get("/api-key-status")
def check_deepgram_api_key():
    """Check if Deepgram API key is configured."""
    try:
        deepgram_service._ensure_client()
        return {"configured": True}
    except ValueError:
        return {"configured": False, "message": "DEEPGRAM_API_KEY not found in environment variables"}


@router.post("/process-meeting")
async def process_meeting(request: ProcessMeetingRequest):
    """
    Process meeting transcript through 3-agent workflow:
    1. Analyze transcript with Nemotron to extract tickets
    2. Create tickets in Firestore
    3. Generate Mermaid diagram

    Returns created tickets, diagram, and summary.
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    try:
        print(f"[Voice API] Processing meeting transcript ({len(request.transcript)} chars)")

        # Validate transcript
        if not request.transcript or len(request.transcript.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Transcript is too short. Please provide a meaningful meeting transcript."
            )

        # Get Firestore client
        db = get_firestore_client()

        # Run agent workflow in thread pool to prevent blocking
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    pool,
                    agent_service.process_meeting_transcript,
                    db,
                    request.transcript,
                    request.project_name
                ),
                timeout=300.0  # 5 minute timeout for complete workflow
            )

        print(f"[Voice API] Workflow result: {result.get('success')}")

        if not result["success"]:
            stage = result.get("stage", "unknown")
            error = result.get("error", "Unknown error")
            raise HTTPException(
                status_code=500,
                detail=f"Agent workflow failed at {stage} stage: {error}"
            )

        # Return results
        data = result["data"]
        return {
            "success": True,
            "tickets": data["tickets"],
            "project": data["project"],
            "diagram": data.get("diagram"),
            "summary": data["summary"],
            "ticket_count": data["ticket_count"]
        }

    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Meeting processing timed out after 5 minutes. Please try a shorter transcript."
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        print(f"[Voice API] Error processing meeting: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process meeting: {str(e)}"
        )

