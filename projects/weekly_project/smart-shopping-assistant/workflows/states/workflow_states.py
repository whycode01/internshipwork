"""
Workflow State Definitions for Smart Shopping Assistant
Defines all state objects used in LangGraph workflows
"""

from typing import Dict, List, Optional, Any, TypedDict
from dataclasses import dataclass
from datetime import datetime
import json

class SearchPlanningState(TypedDict):
    """State for search planning and strategy"""
    query: str
    user_intent: str
    selected_sites: List[str]
    search_strategy: str
    product_category: str
    price_range: Optional[Dict[str, float]]
    user_preferences: Dict[str, Any]
    planning_timestamp: str

class BrowserNavigationState(TypedDict):
    """State for browser navigation and session management"""
    current_page: str
    navigation_history: List[str]
    cookies: Dict[str, Any]
    session_id: str
    browser_context: Dict[str, Any]
    anti_bot_detected: bool
    last_action: str
    retry_count: int

class DataExtractionState(TypedDict):
    """State for extracted product data"""
    extracted_products: List[Dict[str, Any]]
    current_site: str
    extraction_status: str
    extraction_errors: List[str]
    raw_html: str
    structured_data: Dict[str, Any]
    confidence_score: float
    extraction_timestamp: str

class ValidationState(TypedDict):
    """State for data quality validation"""
    validated_products: List[Dict[str, Any]]
    duplicate_products: List[Dict[str, Any]]
    validation_errors: List[str]
    quality_score: float
    missing_fields: List[str]
    data_consistency: Dict[str, Any]
    validation_timestamp: str

class ComparisonState(TypedDict):
    """State for product comparison and matching"""
    matched_products: List[Dict[str, Any]]
    price_comparisons: List[Dict[str, Any]]
    best_deals: List[Dict[str, Any]]
    product_similarities: Dict[str, float]
    comparison_metrics: Dict[str, Any]
    recommendation_score: float
    comparison_timestamp: str

class NotificationState(TypedDict):
    """State for notification triggers and alerts"""
    alert_triggers: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    notification_queue: List[Dict[str, Any]]
    sent_notifications: List[Dict[str, Any]]
    notification_status: str
    alert_timestamp: str

class WorkflowState(TypedDict):
    """Main workflow state that combines all sub-states"""
    # Core workflow info
    workflow_id: str
    session_id: str
    user_id: str
    start_timestamp: str
    current_step: str
    workflow_status: str
    
    # Sub-states
    search_planning: SearchPlanningState
    browser_navigation: BrowserNavigationState
    data_extraction: DataExtractionState
    validation: ValidationState
    comparison: ComparisonState
    notification: NotificationState
    
    # Workflow metadata
    execution_history: List[Dict[str, Any]]
    error_log: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    retry_attempts: int
    max_retries: int

@dataclass
class WorkflowConfig:
    """Configuration for workflow execution"""
    max_retries: int = 3
    timeout: int = 300
    headless_browser: bool = True
    stealth_mode: bool = True
    parallel_execution: bool = True
    cache_results: bool = True
    enable_notifications: bool = True
    debug_mode: bool = False

def create_initial_state(query: str, user_id: str = "default") -> WorkflowState:
    """Create initial workflow state"""
    timestamp = datetime.now().isoformat()
    workflow_id = f"workflow_{int(datetime.now().timestamp())}"
    session_id = f"session_{int(datetime.now().timestamp())}"
    
    return WorkflowState(
        # Core workflow info
        workflow_id=workflow_id,
        session_id=session_id,
        user_id=user_id,
        start_timestamp=timestamp,
        current_step="planning",
        workflow_status="initialized",
        
        # Sub-states
        search_planning=SearchPlanningState(
            query=query,
            user_intent="",
            selected_sites=[],
            search_strategy="",
            product_category="",
            price_range=None,
            user_preferences={},
            planning_timestamp=timestamp
        ),
        
        browser_navigation=BrowserNavigationState(
            current_page="",
            navigation_history=[],
            cookies={},
            session_id=session_id,
            browser_context={},
            anti_bot_detected=False,
            last_action="",
            retry_count=0
        ),
        
        data_extraction=DataExtractionState(
            extracted_products=[],
            current_site="",
            extraction_status="pending",
            extraction_errors=[],
            raw_html="",
            structured_data={},
            confidence_score=0.0,
            extraction_timestamp=timestamp
        ),
        
        validation=ValidationState(
            validated_products=[],
            duplicate_products=[],
            validation_errors=[],
            quality_score=0.0,
            missing_fields=[],
            data_consistency={},
            validation_timestamp=timestamp
        ),
        
        comparison=ComparisonState(
            matched_products=[],
            price_comparisons=[],
            best_deals=[],
            product_similarities={},
            comparison_metrics={},
            recommendation_score=0.0,
            comparison_timestamp=timestamp
        ),
        
        notification=NotificationState(
            alert_triggers=[],
            user_preferences={},
            notification_queue=[],
            sent_notifications=[],
            notification_status="pending",
            alert_timestamp=timestamp
        ),
        
        # Workflow metadata
        execution_history=[],
        error_log=[],
        performance_metrics={},
        retry_attempts=0,
        max_retries=3
    )

def update_state_step(state: WorkflowState, step: str) -> WorkflowState:
    """Update current workflow step"""
    state["current_step"] = step
    state["execution_history"].append({
        "step": step,
        "timestamp": datetime.now().isoformat(),
        "status": "started"
    })
    return state

def log_error(state: WorkflowState, error: str, step: str = None) -> WorkflowState:
    """Log error in workflow state"""
    error_entry = {
        "error": error,
        "step": step or state["current_step"],
        "timestamp": datetime.now().isoformat()
    }
    state["error_log"].append(error_entry)
    return state

def increment_retry(state: WorkflowState) -> WorkflowState:
    """Increment retry counter"""
    state["retry_attempts"] += 1
    return state