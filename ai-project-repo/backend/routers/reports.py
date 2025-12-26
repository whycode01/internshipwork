import logging

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/reports",
    tags=["Report Generation"]
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriptFetchRequest(BaseModel):
    job_id: int
    candidate_id: int

@router.post("/fetch-transcript")
async def fetch_transcript_for_report(request: TranscriptFetchRequest):
    """
    Fetch transcript for report generation (simplified version)
    """
    try:
        # Use the existing transcript API
        response = requests.get(
            f"http://localhost:8000/api/transcripts/fetch",
            params={"job_id": request.job_id, "candidate_id": request.candidate_id},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "content": data.get("content", ""),
                "source": data.get("source", "API")
            }
        else:
            logger.error(f"Failed to fetch transcript: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch transcript: {response.text}"
            )
            
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Transcript service is not available"
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Transcript service request timed out"
        )
    except Exception as e:
        logger.error(f"Error fetching transcript: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/health")
async def check_report_health():
    """Check if the report service is working"""
    return {
        "status": "healthy",
        "service": "reports",
        "message": "Report service is running"
    }