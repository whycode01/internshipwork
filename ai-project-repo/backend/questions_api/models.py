"""
Pydantic models for the Questions API
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    """Enumeration of question types"""
    BEHAVIORAL = "Behavioral"
    TECHNICAL = "Technical"
    SITUATIONAL = "Situational"
    POLICY_COMPLIANCE = "Policy/Compliance"
    CULTURAL_FIT = "Cultural Fit"

class SortBy(str, Enum):
    """Enumeration of sort options"""
    TIMESTAMP = "timestamp"
    QUESTION_TYPE = "question_type"
    CANDIDATE_ID = "candidate_id"
    JOB_ID = "job_id"

class Question(BaseModel):
    """Model for individual question"""
    id: int = Field(..., description="Sequential question ID")
    question_text: str = Field(..., description="The interview question text")
    question_type: str = Field(..., description="Type of question (Behavioral, Technical, etc.)")
    objective: str = Field(..., description="What the question aims to assess")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional question metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "question_text": "Can you describe a situation where you had to analyze a large dataset?",
                "question_type": "Behavioral",
                "objective": "Assess ability to analyze complex data and communicate insights",
                "metadata": {
                    "difficulty": "intermediate",
                    "estimated_time": "5-7 minutes",
                    "skills_assessed": ["data_analysis", "communication"]
                }
            }
        }

class QuestionMetadata(BaseModel):
    """Metadata about the question file and generation"""
    candidate_id: int = Field(..., description="Candidate ID")
    job_id: Optional[int] = Field(None, description="Job ID")
    job_category: Optional[str] = Field(None, description="Job category")
    policy_context: Optional[str] = Field(None, description="Policy context used for generation")
    generated_at: datetime = Field(..., description="When the questions were generated")
    source_file: str = Field(..., description="Source CSV file path")
    total_questions: int = Field(..., description="Total number of questions in the file")
    
    class Config:
        schema_extra = {
            "example": {
                "candidate_id": 24,
                "job_id": 5,
                "job_category": "corporate_roles",
                "policy_context": "corporate_finance_analyst",
                "generated_at": "2025-09-08T09:59:37Z",
                "source_file": "jobs/5_corporate_roles/interview_questions_24_20250908_095937.csv",
                "total_questions": 12
            }
        }

class PaginationInfo(BaseModel):
    """Pagination information"""
    current_page: int = Field(..., description="Current page number")
    total_pages: int = Field(..., description="Total number of pages")
    total_items: int = Field(..., description="Total number of items")
    items_per_page: int = Field(..., description="Number of items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")
    
    class Config:
        schema_extra = {
            "example": {
                "current_page": 1,
                "total_pages": 2,
                "total_items": 15,
                "items_per_page": 10,
                "has_next": True,
                "has_previous": False
            }
        }

class SearchParams(BaseModel):
    """Parameters for advanced search"""
    query: Optional[str] = Field(None, description="Search text in question content")
    candidate_id: Optional[int] = Field(None, description="Filter by candidate ID")
    job_id: Optional[int] = Field(None, description="Filter by job ID")
    question_type: Optional[str] = Field(None, description="Filter by question type")
    policy_name: Optional[str] = Field(None, description="Filter by policy/job category")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")
    sort_by: str = Field("timestamp", description="Field to sort by")

class QuestionsListResponse(BaseModel):
    """Response model for list of questions"""
    status: str = Field(default="success", description="Response status")
    data: Dict[str, Any] = Field(..., description="Response data")
    pagination: PaginationInfo = Field(..., description="Pagination information")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "data": {
                    "metadata": {
                        "candidate_id": 24,
                        "job_id": 5,
                        "job_category": "corporate_roles",
                        "policy_context": "corporate_finance_analyst",
                        "generated_at": "2025-09-08T09:59:37Z",
                        "source_file": "jobs/5_corporate_roles/interview_questions_24_20250908_095937.csv",
                        "total_questions": 12
                    },
                    "questions": [
                        {
                            "id": 1,
                            "question_text": "Can you describe a situation where you had to analyze a large dataset?",
                            "question_type": "Behavioral",
                            "objective": "Assess ability to analyze complex data and communicate insights",
                            "metadata": {
                                "difficulty": "intermediate",
                                "estimated_time": "5-7 minutes"
                            }
                        }
                    ]
                },
                "pagination": {
                    "current_page": 1,
                    "total_pages": 2,
                    "total_items": 12,
                    "items_per_page": 10,
                    "has_next": True,
                    "has_previous": False
                }
            }
        }

class QuestionResponse(BaseModel):
    """Response model for single question operations"""
    status: str = Field(default="success", description="Response status")
    data: Question = Field(..., description="Question data")
    metadata: QuestionMetadata = Field(..., description="Question metadata")

class ErrorResponse(BaseModel):
    """Error response model"""
    status: str = Field(default="error", description="Response status")
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "error",
                "error": "No questions found for candidate 999",
                "details": "The specified candidate ID does not exist in our records",
                "timestamp": "2025-09-08T10:30:00Z"
            }
        }

class FileIndexInfo(BaseModel):
    """Information about the file index"""
    total_files: int = Field(..., description="Total number of indexed files")
    total_candidates: int = Field(..., description="Total number of unique candidates")
    total_jobs: int = Field(..., description="Total number of unique jobs")
    job_categories: List[str] = Field(..., description="List of available job categories")
    last_updated: datetime = Field(..., description="When the index was last updated")
    index_size: int = Field(..., description="Size of the index in bytes")
    
    class Config:
        schema_extra = {
            "example": {
                "total_files": 45,
                "total_candidates": 23,
                "total_jobs": 8,
                "job_categories": ["corporate_roles", "marketing_roles", "tech_roles"],
                "last_updated": "2025-09-08T10:00:00Z",
                "index_size": 2048
            }
        }
