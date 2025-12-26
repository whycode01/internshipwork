import logging
from typing import List, Optional

import requests
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/transcripts",
    tags=["Transcripts"]
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration for the external transcript API
TRANSCRIPT_API_BASE_URL = "http://localhost:8001"

# Pydantic models for API responses
class TranscriptResponse(BaseModel):
    content: str
    source: str = "API"

class TranscriptFetchRequest(BaseModel):
    job_id: int
    candidate_id: int

@router.get("/fetch")
async def fetch_transcripts(
    job_id: int = Query(..., description="Job ID for the transcript"),
    candidate_id: int = Query(..., description="Candidate ID for the transcript")
):
    """
    Fetch interview transcripts from the external transcript API.
    
    Args:
        job_id: Job ID for the transcript
        candidate_id: Candidate ID for the transcript
    
    Returns:
        TranscriptResponse: The fetched transcript content
    """
    try:
        # Step 1: List available transcripts
        list_url = f"{TRANSCRIPT_API_BASE_URL}/transcripts/job/{job_id}/candidate/{candidate_id}"
        logger.info(f"Listing transcripts from {list_url}")
        list_response = requests.get(list_url, timeout=30)
        if list_response.status_code != 200:
            logger.error(f"Transcript list request failed with status {list_response.status_code}: {list_response.text}")
            raise HTTPException(
                status_code=list_response.status_code,
                detail=f"Failed to list transcripts: {list_response.text}"
            )
        transcript_list = list_response.json()
        transcripts = transcript_list.get("transcripts", [])
        if not transcripts:
            raise HTTPException(status_code=404, detail="No transcripts found for this job/candidate")

        # Step 2: Fetch the first transcript file using the correct download endpoint
        transcript_filename = transcripts[0]["filename"]
        logger.info(f"Got transcript filename: {transcript_filename}")
        
        # Try the download endpoint first
        file_url = f"{TRANSCRIPT_API_BASE_URL}/transcripts/{transcript_filename}/download"
        logger.info(f"Trying download endpoint: {file_url}")
        file_response = requests.get(file_url, timeout=30)
        
        # If download fails, try without the .json extension
        if file_response.status_code == 404 and transcript_filename.endswith('.json'):
            filename_without_ext = transcript_filename[:-5]  # Remove .json
            file_url = f"{TRANSCRIPT_API_BASE_URL}/transcripts/{filename_without_ext}/download"
            logger.info(f"Retrying with filename without extension: {file_url}")
            file_response = requests.get(file_url, timeout=30)
            
        # If still failing, try the text endpoint as fallback
        if file_response.status_code == 404:
            file_url = f"{TRANSCRIPT_API_BASE_URL}/transcripts/{transcript_filename}/text"
            logger.info(f"Trying text endpoint as fallback: {file_url}")
            file_response = requests.get(file_url, timeout=30)
            
        # If text endpoint also fails, try without extension
        if file_response.status_code == 404 and transcript_filename.endswith('.json'):
            filename_without_ext = transcript_filename[:-5]
            file_url = f"{TRANSCRIPT_API_BASE_URL}/transcripts/{filename_without_ext}/text"
            logger.info(f"Trying text endpoint without extension: {file_url}")
            file_response = requests.get(file_url, timeout=30)
        if file_response.status_code != 200:
            logger.error(f"All transcript file requests failed. Last attempt was: {file_url}")
            logger.error(f"Last response status: {file_response.status_code}, text: {file_response.text}")
            logger.error(f"Available transcript filenames: {[t['filename'] for t in transcripts]}")
            raise HTTPException(
                status_code=file_response.status_code,
                detail=f"Failed to fetch transcript file after trying multiple endpoints. Last error: {file_response.text}"
            )
        
        # Try to parse as JSON first, if that fails, treat as text
        try:
            transcript_data = file_response.json()
        except:
            # If JSON parsing fails, treat the response as text
            transcript_data = {"content": file_response.text, "source": "text_endpoint"}

        # Format the response
        formatted_content = format_transcript_content(transcript_data)
        return TranscriptResponse(
            content=formatted_content,
            source="External API"
        )
    except requests.exceptions.ConnectionError:
        logger.error(f"Failed to connect to transcript API at {TRANSCRIPT_API_BASE_URL}")
        raise HTTPException(
            status_code=503,
            detail="Transcript service is not available"
        )
    except requests.exceptions.Timeout:
        logger.error("Transcript API request timed out")
        raise HTTPException(
            status_code=504,
            detail="Transcript service request timed out"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching transcript: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/fetch")
async def fetch_transcripts_post(request: TranscriptFetchRequest):
    """
    Fetch interview transcripts using POST method.
    
    Args:
        request: Request body containing job_id and candidate_id
    
    Returns:
        TranscriptResponse: The fetched transcript content
    """

@router.get("/health")
async def check_transcript_service():
    """
    Check if the transcript service is available.
    
    Returns:
        dict: Service health status
    """
    try:
        response = requests.get(f"{TRANSCRIPT_API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            return {
                "status": "healthy",
                "service": "transcript_api",
                "url": TRANSCRIPT_API_BASE_URL
            }
        else:
            return {
                "status": "unhealthy",
                "service": "transcript_api",
                "url": TRANSCRIPT_API_BASE_URL,
                "error": f"Status code: {response.status_code}"
            }
    except Exception as e:
        return {
            "status": "unavailable",
            "service": "transcript_api", 
            "url": TRANSCRIPT_API_BASE_URL,
            "error": str(e)
        }

def format_transcript_content(transcript_data) -> str:
    """
    Format the transcript data into a readable text format.
    
    Args:
        transcript_data: Raw transcript data from the API
    
    Returns:
        str: Formatted transcript content
    """
    if isinstance(transcript_data, dict):
        # Handle text endpoint response (already formatted)
        if "content" in transcript_data and "source" in transcript_data:
            if transcript_data["source"] == "text_endpoint":
                # The content is already nicely formatted from the text endpoint
                return transcript_data["content"]
        
        # Handle JSON response with entries
        if "entries" in transcript_data and isinstance(transcript_data["entries"], list):
            formatted_parts = []
            
            # Add header with metadata
            formatted_parts.append("=" * 60)
            formatted_parts.append("INTERVIEW TRANSCRIPT")
            formatted_parts.append("=" * 60)
            
            if "job_id" in transcript_data:
                formatted_parts.append(f"Job ID: {transcript_data['job_id']}")
            if "candidate_id" in transcript_data:
                formatted_parts.append(f"Candidate ID: {transcript_data['candidate_id']}")
            if "interview_id" in transcript_data:
                formatted_parts.append(f"Interview ID: {transcript_data['interview_id']}")
            if "meeting_id" in transcript_data:
                formatted_parts.append(f"Meeting ID: {transcript_data['meeting_id']}")
            if "start_time" in transcript_data and "end_time" in transcript_data:
                formatted_parts.append(f"Start Time: {transcript_data['start_time']}")
                formatted_parts.append(f"End Time: {transcript_data['end_time']}")
            if "duration_total" in transcript_data:
                duration_min = int(transcript_data['duration_total'] // 60)
                duration_sec = int(transcript_data['duration_total'] % 60)
                formatted_parts.append(f"Duration: {duration_min}:{duration_sec:02d}")
            if "participants" in transcript_data:
                formatted_parts.append(f"Participants: {', '.join(transcript_data['participants'])}")
            
            formatted_parts.append("")
            formatted_parts.append("CONVERSATION:")
            formatted_parts.append("-" * 60)
            
            # Process entries/messages
            for entry in transcript_data["entries"]:
                if isinstance(entry, dict):
                    speaker = entry.get("speaker", "Unknown")
                    message = entry.get("message", "")
                    timestamp = entry.get("timestamp", "")
                    message_type = entry.get("message_type", "")
                    
                    # Format system messages differently
                    if message_type == "system":
                        formatted_parts.append(f"[{timestamp}] ** {message} **")
                    else:
                        # Regular speech messages
                        formatted_parts.append(f"[{timestamp}] {speaker}: {message}")
            
            formatted_parts.append("-" * 60)
            formatted_parts.append("End of Transcript")
            formatted_parts.append("=" * 60)
            
            return "\n".join(formatted_parts)
        
        # Handle other dictionary formats
        else:
            return str(transcript_data)
    
    elif isinstance(transcript_data, list):
        # Handle array of transcript objects (if multiple transcripts)
        if len(transcript_data) == 0:
            return "No transcripts found for the specified job and candidate."
        
        formatted_content = []
        for i, transcript in enumerate(transcript_data, 1):
            formatted_content.append(f"--- Transcript {i} ---")
            formatted_content.append(format_transcript_content(transcript))
            formatted_content.append("")
        
        return "\n".join(formatted_content)
    
    else:
        # Handle simple string format or other types
        return str(transcript_data)