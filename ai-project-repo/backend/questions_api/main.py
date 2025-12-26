"""
FastAPI service for serving interview questions from CSV files
"""
import asyncio
import csv
import logging
import os
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path as PathLib
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware

# Use absolute imports when running as script, relative when as module
try:
    from .dependencies import get_file_index_service, get_question_service
    from .models import (PaginationInfo, Question, QuestionMetadata,
                         QuestionResponse, QuestionsListResponse, SearchParams)
    from .services import FileIndexService, QuestionService
except ImportError:
    from dependencies import get_file_index_service, get_question_service
    from models import (PaginationInfo, Question, QuestionMetadata,
                        QuestionResponse, QuestionsListResponse, SearchParams)
    from services import FileIndexService, QuestionService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Interview Questions API",
    description="REST API for serving AI-generated interview questions from CSV files",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Interview Questions API...")
    # Initialize file index service
    file_service = get_file_index_service()
    await file_service.initialize_index()
    logger.info("File index initialized successfully")

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {"message": "Interview Questions API is running", "status": "healthy"}

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Interview Questions API",
        "version": "1.0.0"
    }

@app.get(
    "/api/questions/candidate/{candidate_id}",
    response_model=QuestionsListResponse,
    tags=["Questions"],
    summary="Get all questions for a candidate"
)
async def get_questions_by_candidate(
    candidate_id: int = Path(..., description="Candidate ID"),
    limit: int = Query(10, ge=1, le=100, description="Number of questions to return"),
    offset: int = Query(0, ge=0, description="Number of questions to skip"),
    question_type: Optional[str] = Query(None, description="Filter by question type"),
    sort_by: str = Query("timestamp", description="Sort by field (timestamp, question_type)"),
    question_service: QuestionService = Depends(get_question_service)
):
    """Get all questions for a specific candidate ID"""
    try:
        result = await question_service.get_questions_by_candidate(
            candidate_id=candidate_id,
            limit=limit,
            offset=offset,
            question_type=question_type,
            sort_by=sort_by
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No questions found for candidate {candidate_id}")
    except Exception as e:
        logger.error(f"Error fetching questions for candidate {candidate_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get(
    "/api/questions/candidate/{candidate_id}/job/{job_id}",
    response_model=QuestionsListResponse,
    tags=["Questions"],
    summary="Get questions for specific candidate and job"
)
async def get_questions_by_candidate_and_job(
    candidate_id: int = Path(..., description="Candidate ID"),
    job_id: int = Path(..., description="Job ID"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    question_type: Optional[str] = Query(None, description="Filter by question type"),
    question_service: QuestionService = Depends(get_question_service)
):
    """Get questions for a specific candidate and job combination"""
    try:
        result = await question_service.get_questions_by_candidate_and_job(
            candidate_id=candidate_id,
            job_id=job_id,
            limit=limit,
            offset=offset,
            question_type=question_type
        )
        return result
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, 
            detail=f"No questions found for candidate {candidate_id} and job {job_id}"
        )
    except Exception as e:
        logger.error(f"Error fetching questions for candidate {candidate_id}, job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get(
    "/api/questions/job/{job_id}/latest",
    response_model=QuestionsListResponse,
    tags=["Questions"],
    summary="Get latest questions for a job"
)
async def get_latest_questions_by_job(
    job_id: int = Path(..., description="Job ID"),
    limit: int = Query(10, ge=1, le=100),
    question_service: QuestionService = Depends(get_question_service)
):
    """Get the most recent questions for a specific job ID"""
    try:
        result = await question_service.get_latest_questions_by_job(
            job_id=job_id,
            limit=limit
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No questions found for job {job_id}")
    except Exception as e:
        logger.error(f"Error fetching latest questions for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get(
    "/api/questions/policy/{policy_name}",
    response_model=QuestionsListResponse,
    tags=["Questions"],
    summary="Get questions by policy/job category"
)
async def get_questions_by_policy(
    policy_name: str = Path(..., description="Policy name or job category"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    question_type: Optional[str] = Query(None, description="Filter by question type"),
    question_service: QuestionService = Depends(get_question_service)
):
    """Get questions filtered by policy name or job category"""
    try:
        result = await question_service.get_questions_by_policy(
            policy_name=policy_name,
            limit=limit,
            offset=offset,
            question_type=question_type
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No questions found for policy '{policy_name}'")
    except Exception as e:
        logger.error(f"Error fetching questions for policy {policy_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get(
    "/api/questions/search",
    response_model=QuestionsListResponse,
    tags=["Questions"],
    summary="Advanced search for questions"
)
async def search_questions(
    query: Optional[str] = Query(None, description="Search text in question content"),
    candidate_id: Optional[int] = Query(None, description="Filter by candidate ID"),
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    question_type: Optional[str] = Query(None, description="Filter by question type"),
    policy_name: Optional[str] = Query(None, description="Filter by policy/job category"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("timestamp", description="Sort by field"),
    question_service: QuestionService = Depends(get_question_service)
):
    """Advanced search with multiple filters"""
    try:
        search_params = SearchParams(
            query=query,
            candidate_id=candidate_id,
            job_id=job_id,
            question_type=question_type,
            policy_name=policy_name,
            limit=limit,
            offset=offset,
            sort_by=sort_by
        )
        
        result = await question_service.search_questions(search_params)
        return result
    except Exception as e:
        logger.error(f"Error in search: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get(
    "/api/questions/files/index",
    response_model=Dict[str, Any],
    tags=["Admin"],
    summary="Get file index information"
)
async def get_file_index(
    file_service: FileIndexService = Depends(get_file_index_service)
):
    """Get information about indexed files"""
    try:
        index_info = await file_service.get_index_info()
        return index_info
    except Exception as e:
        logger.error(f"Error getting file index: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post(
    "/api/questions/files/refresh",
    tags=["Admin"],
    summary="Refresh file index"
)
async def refresh_file_index(
    file_service: FileIndexService = Depends(get_file_index_service)
):
    """Manually refresh the file index"""
    try:
        await file_service.refresh_index()
        return {"message": "File index refreshed successfully"}
    except Exception as e:
        logger.error(f"Error refreshing file index: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
