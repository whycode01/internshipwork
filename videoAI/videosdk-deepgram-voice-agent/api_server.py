#!/usr/bin/env python3
"""
FastAPI Server for Transcript Downloads
Provides REST API endpoints for managing and downloading interview transcripts
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

from transcript.transcript_manager import (Transcript, TranscriptEntry,
                                           TranscriptManager)

# Initialize FastAPI app
app = FastAPI(
    title="Interview Transcript API",
    description="API for managing and downloading interview transcripts",
    version="1.0.0"
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize transcript manager
transcript_manager = TranscriptManager()

# Pydantic models for API responses
class TranscriptInfo(BaseModel):
    filename: str
    interview_id: str
    meeting_id: str
    start_time: str
    end_time: Optional[str] = None
    duration_total: float
    participants: List[str]
    message_count: int
    file_size: int

class TranscriptListResponse(BaseModel):
    transcripts: List[TranscriptInfo]
    total_count: int

class CurrentTranscriptResponse(BaseModel):
    is_recording: bool
    interview_id: Optional[str] = None
    meeting_id: Optional[str] = None
    start_time: Optional[str] = None
    participants: List[str]
    current_message_count: int

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Interview Transcript API is running",
        "version": "1.0.0",
        "endpoints": {
            "list_transcripts": "/transcripts/",
            "download_transcript": "/transcripts/{filename}/download",
            "get_transcript_text": "/transcripts/{filename}/text",
            "current_transcript": "/transcripts/current"
        }
    }

@app.get("/transcripts/", response_model=TranscriptListResponse)
async def list_transcripts(
    job_id: Optional[str] = Query(None, description="Filter by job ID"),
    candidate_id: Optional[str] = Query(None, description="Filter by candidate ID")
):
    """Get list of transcripts with optional filtering by job_id and/or candidate_id"""
    try:
        files = transcript_manager.list_transcripts(job_id=job_id, candidate_id=candidate_id)
        transcripts = []
        
        for filename in files:
            try:
                # Load transcript to get metadata - try with job/candidate context
                transcript = transcript_manager.load_transcript(filename, job_id=job_id, candidate_id=candidate_id)
                if transcript:
                    # Find the actual file path to get size
                    file_path = None
                    if transcript.job_id and transcript.candidate_id:
                        file_path = os.path.join(
                            transcript_manager._get_storage_path(transcript.job_id, transcript.candidate_id),
                            filename
                        )
                    else:
                        file_path = os.path.join(transcript_manager.storage_dir, filename)
                    
                    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    
                    transcript_info = TranscriptInfo(
                        filename=filename,
                        interview_id=transcript.interview_id,
                        meeting_id=transcript.meeting_id,
                        start_time=transcript.start_time,
                        end_time=transcript.end_time,
                        duration_total=transcript.duration_total,
                        participants=transcript.participants,
                        message_count=len(transcript.entries),
                        file_size=file_size
                    )
                    transcripts.append(transcript_info)
            except Exception as e:
                print(f"Error loading transcript {filename}: {e}")
                continue
        
        return TranscriptListResponse(
            transcripts=transcripts,
            total_count=len(transcripts)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing transcripts: {str(e)}")

@app.get("/transcripts/{filename}/download")
async def download_transcript(filename: str):
    """Download transcript file as JSON"""
    try:
        # Use the transcript manager's load_transcript method to find the file
        transcript = transcript_manager.load_transcript(filename)
        
        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript file not found")
        
        if not filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Invalid transcript file format")
        
        # Find the actual file path using recursive search
        file_path = None
        if os.path.exists(transcript_manager.transcripts_dir):
            for root, dirs, files in os.walk(transcript_manager.transcripts_dir):
                if filename in files:
                    file_path = os.path.join(root, filename)
                    break
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Transcript file not found")

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/json'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading transcript: {str(e)}")

@app.get("/transcripts/{filename}/text")
async def get_transcript_text(filename: str):
    """Get transcript as formatted text"""
    try:
        transcript = transcript_manager.load_transcript(filename)
        
        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript file not found")
        
        text_transcript = transcript_manager.generate_text_transcript(transcript)
        
        return PlainTextResponse(
            content=text_transcript,
            headers={
                "Content-Disposition": f"attachment; filename={filename.replace('.json', '.txt')}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating text transcript: {str(e)}")

@app.get("/transcripts/current", response_model=CurrentTranscriptResponse)
async def get_current_transcript():
    """Get information about currently recording transcript"""
    try:
        is_recording = transcript_manager.current_transcript is not None
        
        if is_recording:
            current = transcript_manager.current_transcript
            return CurrentTranscriptResponse(
                is_recording=True,
                interview_id=current.interview_id,
                meeting_id=current.meeting_id,
                start_time=current.start_time,
                participants=current.participants,
                current_message_count=len(current.entries)
            )
        else:
            return CurrentTranscriptResponse(
                is_recording=False,
                participants=[],
                current_message_count=0
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting current transcript: {str(e)}")

@app.get("/transcripts/current/text")
async def get_current_transcript_text():
    """Get current transcript as formatted text"""
    try:
        if not transcript_manager.current_transcript:
            raise HTTPException(status_code=404, detail="No active transcript recording")
        
        text_transcript = transcript_manager.get_current_transcript_text()
        current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"current-transcript-{current_time}.txt"
        
        return PlainTextResponse(
            content=text_transcript,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting current transcript text: {str(e)}")

@app.get("/transcripts/job/{job_id}", response_model=TranscriptListResponse)
async def get_transcripts_by_job(job_id: str):
    """Get all transcripts for a specific job"""
    try:
        files = transcript_manager.get_transcripts_by_job(job_id)
        transcripts = []
        
        for filename in files:
            try:
                transcript = transcript_manager.load_transcript(filename, job_id=job_id)
                if transcript:
                    file_path = os.path.join(
                        transcript_manager._get_storage_path(transcript.job_id, transcript.candidate_id),
                        filename
                    )
                    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    
                    transcript_info = TranscriptInfo(
                        filename=filename,
                        interview_id=transcript.interview_id,
                        meeting_id=transcript.meeting_id,
                        start_time=transcript.start_time,
                        end_time=transcript.end_time,
                        duration_total=transcript.duration_total,
                        participants=transcript.participants,
                        message_count=len(transcript.entries),
                        file_size=file_size
                    )
                    transcripts.append(transcript_info)
            except Exception as e:
                print(f"Error loading transcript {filename}: {e}")
                continue
        
        return TranscriptListResponse(
            transcripts=transcripts,
            total_count=len(transcripts)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting transcripts for job {job_id}: {str(e)}")

@app.get("/transcripts/candidate/{candidate_id}", response_model=TranscriptListResponse)
async def get_transcripts_by_candidate(candidate_id: str):
    """Get all transcripts for a specific candidate"""
    try:
        files = transcript_manager.get_transcripts_by_candidate(candidate_id)
        transcripts = []
        
        for filename in files:
            try:
                transcript = transcript_manager.load_transcript(filename, candidate_id=candidate_id)
                if transcript:
                    file_path = os.path.join(
                        transcript_manager._get_storage_path(transcript.job_id, transcript.candidate_id),
                        filename
                    )
                    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    
                    transcript_info = TranscriptInfo(
                        filename=filename,
                        interview_id=transcript.interview_id,
                        meeting_id=transcript.meeting_id,
                        start_time=transcript.start_time,
                        end_time=transcript.end_time,
                        duration_total=transcript.duration_total,
                        participants=transcript.participants,
                        message_count=len(transcript.entries),
                        file_size=file_size
                    )
                    transcripts.append(transcript_info)
            except Exception as e:
                print(f"Error loading transcript {filename}: {e}")
                continue
        
        return TranscriptListResponse(
            transcripts=transcripts,
            total_count=len(transcripts)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting transcripts for candidate {candidate_id}: {str(e)}")

@app.get("/transcripts/job/{job_id}/candidate/{candidate_id}", response_model=TranscriptListResponse)
async def get_transcripts_by_job_and_candidate(job_id: str, candidate_id: str):
    """Get all transcripts for a specific job and candidate combination"""
    try:
        files = transcript_manager.get_transcripts_by_job_and_candidate(job_id, candidate_id)
        transcripts = []
        
        for filename in files:
            try:
                transcript = transcript_manager.load_transcript(filename, job_id=job_id, candidate_id=candidate_id)
                if transcript:
                    file_path = os.path.join(
                        transcript_manager._get_storage_path(job_id, candidate_id),
                        filename
                    )
                    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    
                    transcript_info = TranscriptInfo(
                        filename=filename,
                        interview_id=transcript.interview_id,
                        meeting_id=transcript.meeting_id,
                        start_time=transcript.start_time,
                        end_time=transcript.end_time,
                        duration_total=transcript.duration_total,
                        participants=transcript.participants,
                        message_count=len(transcript.entries),
                        file_size=file_size
                    )
                    transcripts.append(transcript_info)
            except Exception as e:
                print(f"Error loading transcript {filename}: {e}")
                continue
        
        return TranscriptListResponse(
            transcripts=transcripts,
            total_count=len(transcripts)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting transcripts for job {job_id}, candidate {candidate_id}: {str(e)}")

@app.post("/transcripts/start")
async def start_transcript_recording(
    meeting_id: str, 
    job_id: Optional[str] = None,
    candidate_id: Optional[str] = None,
    participants: List[str] = None
):
    """Start a new transcript recording with job and candidate info"""
    try:
        if transcript_manager.current_transcript:
            raise HTTPException(status_code=400, detail="A transcript recording is already active")
        
        interview_id = transcript_manager.start_recording(
            meeting_id=meeting_id,
            job_id=job_id,
            candidate_id=candidate_id,
            participants=participants or [],
            metadata={"api_started": True, "job_id": job_id, "candidate_id": candidate_id}
        )
        
        return {
            "message": "Transcript recording started",
            "interview_id": interview_id,
            "meeting_id": meeting_id,
            "job_id": job_id,
            "candidate_id": candidate_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting transcript: {str(e)}")

@app.post("/transcripts/stop")
async def stop_transcript_recording():
    """Stop current transcript recording"""
    try:
        if not transcript_manager.current_transcript:
            raise HTTPException(status_code=400, detail="No active transcript recording")
        
        filename = transcript_manager.end_recording()
        
        return {
            "message": "Transcript recording stopped",
            "filename": filename
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping transcript: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Interview Transcript API Server...")
    print("📊 Available endpoints:")
    print("   GET  /transcripts/                    - List all transcripts")
    print("   GET  /transcripts/{filename}/download - Download transcript JSON")
    print("   GET  /transcripts/{filename}/text     - Download transcript as text")
    print("   GET  /transcripts/current             - Get current transcript info")
    print("   GET  /transcripts/current/text        - Download current transcript as text")
    print("   POST /transcripts/start               - Start recording")
    print("   POST /transcripts/stop                - Stop recording")
    print("🌐 Server will run on: http://localhost:8001")
    print("📚 API docs available at: http://localhost:8001/docs")
    print()
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )