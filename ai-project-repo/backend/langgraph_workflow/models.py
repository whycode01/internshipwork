"""
Data models for the LangGraph interview assessment workflow.
Defines the state and data structures used throughout the workflow.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DecisionStatus(str, Enum):
    SELECTED = "selected"
    CONDITIONAL = "conditional" 
    UNDER_REVIEW = "under_review"
    REJECTED = "rejected"


class WorkflowState(BaseModel):
    """Main state object that flows through the LangGraph workflow."""
    
    # Input data
    job_id: Optional[int] = None
    candidate_id: str
    candidate_name: str
    raw_transcript: str
    resume_text: Optional[str] = ""  # Make optional with default empty string to handle missing resume
    job_description: Dict[str, Any]
    policy_template: Dict[str, Any]
    
    # Processed data
    structured_transcript: Optional[Dict[str, Any]] = None
    parsed_resume: Optional[Dict[str, Any]] = None
    job_requirements: Optional[Dict[str, Any]] = None
    
    # Agent assessments
    technical_assessment: Optional[Dict[str, Any]] = None
    behavioral_assessment: Optional[Dict[str, Any]] = None
    experience_assessment: Optional[Dict[str, Any]] = None
    cultural_assessment: Optional[Dict[str, Any]] = None
    
    # Final results
    technical_score: Optional[float] = None
    behavioral_score: Optional[float] = None
    experience_score: Optional[float] = None
    cultural_score: Optional[float] = None
    final_score: Optional[float] = None
    decision: Optional[DecisionStatus] = None
    
    # Report generation
    generated_report: Optional[str] = None
    quality_check_passed: Optional[bool] = None
    
    # Workflow state
    processing_complete: bool = False
    regeneration_attempts: int = 0
    
    # Metadata
    processing_errors: List[str] = []
    processing_start_time: Optional[float] = None
    processing_end_time: Optional[float] = None


class TechnicalAssessment(BaseModel):
    """Technical skills evaluation results."""
    overall_score: float
    skill_matches: Dict[str, float]
    technical_depth: float
    problem_solving: float
    evidence: List[str]
    gaps_identified: List[str]
    strengths: List[str]


class BehavioralAssessment(BaseModel):
    """Behavioral competencies evaluation results."""
    overall_score: float
    communication_clarity: float
    leadership_indicators: float
    teamwork_ability: float
    problem_solving_approach: float
    evidence: List[str]
    improvement_areas: List[str]


class ExperienceAssessment(BaseModel):
    """Experience relevance evaluation results."""
    overall_score: float
    role_alignment: float
    experience_depth: float
    career_progression: float
    relevant_projects: List[str]
    experience_gaps: List[str]
    evidence: List[str]


class CulturalAssessment(BaseModel):
    """Cultural fit evaluation results."""
    overall_score: float
    value_alignment: float
    adaptability: float
    growth_mindset: float
    cultural_integration_potential: float
    evidence: List[str]
    recommendations: List[str]


class FinalAssessment(BaseModel):
    """Final scoring and decision results."""
    technical_score: float
    behavioral_score: float
    experience_score: float
    cultural_score: float
    weighted_final_score: float
    decision: DecisionStatus
    justification: str
    development_recommendations: List[str]


class QualityCheck(BaseModel):
    """Quality assurance results."""
    template_completion: bool
    score_consistency: bool
    evidence_validation: bool
    recommendation_alignment: bool
    overall_quality_score: float
    issues_found: List[str]