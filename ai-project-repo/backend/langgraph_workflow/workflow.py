"""
LangGraph workflow implementation for multi-agent interview assessment.
Orchestrates the complete evaluation pipeline.
"""

import logging
from typing import Any, Dict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph

# Handle both relative and absolute imports for LangGraph Studio compatibility
try:
    from .agents import (BehavioralAssessmentAgent, CulturalFitAgent,
                         DataPreprocessingAgent, ExperienceRelevanceAgent,
                         QualityAssuranceAgent, ReportGenerationAgent,
                         ScoringDecisionAgent, TechnicalSkillsAgent)
    from .models import DecisionStatus, WorkflowState
except ImportError:
    # Fallback for LangGraph Studio (absolute imports)
    from agents import (BehavioralAssessmentAgent, CulturalFitAgent,
                        DataPreprocessingAgent, ExperienceRelevanceAgent,
                        QualityAssuranceAgent, ReportGenerationAgent,
                        ScoringDecisionAgent, TechnicalSkillsAgent)
    from models import DecisionStatus, WorkflowState

logger = logging.getLogger(__name__)


# Global request storage (temporary solution for serialization issue)
_current_request = None

def set_current_request(request):
    """Store request globally to avoid serialization issues."""
    global _current_request
    _current_request = request

def get_current_request():
    """Get stored request."""
    return _current_request


class InterviewAssessmentWorkflow:
    """Main workflow orchestrator for multi-agent interview assessment."""
    
    def __init__(self):
        """Initialize the workflow with all agents and graph structure."""
        logger.info("Initializing interview assessment workflow")
        
        # Initialize agents
        self.preprocessing_agent = DataPreprocessingAgent()
        self.technical_agent = TechnicalSkillsAgent()
        self.behavioral_agent = BehavioralAssessmentAgent()
        self.experience_agent = ExperienceRelevanceAgent()
        self.cultural_agent = CulturalFitAgent()
        self.scoring_agent = ScoringDecisionAgent()
        self.report_agent = ReportGenerationAgent()
        self.qa_agent = QualityAssuranceAgent()
        
        # Initialize memory saver for state persistence
        self.checkpointer = MemorySaver()
        
        # Build the workflow graph
        self._build_workflow()
    
    def _build_workflow(self):
        """Build the LangGraph workflow structure."""
        workflow = StateGraph(WorkflowState)
        
        # Add all nodes
        workflow.add_node("preprocessing", self._data_preprocessing_node)
        workflow.add_node("technical_assessment", self._technical_assessment_node)
        workflow.add_node("behavioral_assessment", self._behavioral_assessment_node)
        workflow.add_node("experience_assessment", self._experience_assessment_node)
        workflow.add_node("cultural_assessment", self._cultural_assessment_node)
        workflow.add_node("scoring_decision", self._scoring_decision_node)
        workflow.add_node("report_generation", self._report_generation_node)
        workflow.add_node("quality_assurance", self._quality_assurance_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Set entry point
        workflow.set_entry_point("preprocessing")
        
        # Add edges - sequential processing to prevent concurrent updates
        workflow.add_edge("preprocessing", "technical_assessment")
        workflow.add_edge("technical_assessment", "behavioral_assessment")
        workflow.add_edge("behavioral_assessment", "experience_assessment")
        workflow.add_edge("experience_assessment", "cultural_assessment")
        workflow.add_edge("cultural_assessment", "scoring_decision")
        workflow.add_edge("scoring_decision", "report_generation")
        workflow.add_edge("report_generation", "quality_assurance")
        
        # Quality assurance with conditional regeneration (limited attempts)
        workflow.add_conditional_edges(
            "quality_assurance",
            self._should_regenerate_report,
            {
                "regenerate": "report_generation",
                "finalize": "finalize"
            }
        )
        
        workflow.add_edge("finalize", "__end__")
        
        # Compile the graph with checkpointer
        self.graph = workflow.compile(
            checkpointer=self.checkpointer
        )
        
        logger.info("Interview assessment workflow initialized successfully")
    
    async def _data_preprocessing_node(self, state: WorkflowState) -> WorkflowState:
        """Node for data preprocessing."""
        request = get_current_request()
        return await self.preprocessing_agent.process(state, request)
    
    async def _technical_assessment_node(self, state: WorkflowState) -> WorkflowState:
        """Node for technical skills assessment."""
        request = get_current_request()
        return await self.technical_agent.process(state, request)
    
    async def _behavioral_assessment_node(self, state: WorkflowState) -> WorkflowState:
        """Node for behavioral assessment."""
        request = get_current_request()
        return await self.behavioral_agent.process(state, request)
    
    async def _experience_assessment_node(self, state: WorkflowState) -> WorkflowState:
        """Node for experience relevance assessment."""
        request = get_current_request()
        return await self.experience_agent.process(state, request)
    
    async def _cultural_assessment_node(self, state: WorkflowState) -> WorkflowState:
        """Node for cultural fit assessment."""
        request = get_current_request()
        return await self.cultural_agent.process(state, request)
    
    async def _scoring_decision_node(self, state: WorkflowState) -> WorkflowState:
        """Node for final scoring and decision making."""
        return self.scoring_agent.process(state)
    
    async def _report_generation_node(self, state: WorkflowState) -> WorkflowState:
        """Node for comprehensive report generation."""
        request = get_current_request()
        return await self.report_agent.process(state, request)
    
    async def _quality_assurance_node(self, state: WorkflowState) -> WorkflowState:
        """Node for quality assurance and validation."""
        request = get_current_request()
        return await self.qa_agent.process(state, request)
    
    def _should_regenerate_report(self, state: WorkflowState) -> str:
        """Decide whether to regenerate report or finalize."""
        # Limit regeneration attempts to prevent infinite loops
        if state.regeneration_attempts >= 3:
            logger.warning(f"Maximum regeneration attempts reached for candidate {state.candidate_id}")
            return "finalize"
        
        if not state.quality_check_passed:
            state.regeneration_attempts += 1
            logger.info(f"Report quality check failed, regenerating (attempt {state.regeneration_attempts}/3)")
            return "regenerate"
        
        return "finalize"
    
    async def _finalize_node(self, state: WorkflowState) -> WorkflowState:
        """Final node to mark processing as complete."""
        import time
        state.processing_complete = True
        state.processing_end_time = time.time()
        
        logger.info(f"Assessment workflow completed for candidate {state.candidate_id}")
        logger.info(f"Final scores - Technical: {state.technical_score}, Behavioral: {state.behavioral_score}, "
                   f"Experience: {state.experience_score}, Cultural: {state.cultural_score}")
        logger.info(f"Final score: {state.final_score}/100, Decision: {state.decision}")
        
        return state
    
    async def run_assessment(self, input_data: Dict[str, Any], request) -> Dict[str, Any]:
        """Run the complete assessment workflow."""
        logger.info(f"Starting assessment workflow for candidate {input_data.get('candidate_id')}")
        
        try:
            # Store request globally to avoid serialization issues
            set_current_request(request)
            
            # Create initial state
            import time
            initial_state = WorkflowState(
                candidate_id=input_data['candidate_id'],
                candidate_name=input_data['candidate_name'],
                raw_transcript=input_data['raw_transcript'],
                resume_text=input_data.get('resume_text', ''),
                job_description=input_data['job_description'],
                policy_template=input_data['policy_template'],
                processing_start_time=time.time()
            )
            
            # Execute workflow
            config = {
                "thread_id": f"assessment_{input_data['candidate_id']}",
                "recursion_limit": 15  # Lower limit to prevent infinite loops
            }
            
            # Run the workflow
            final_state = await self.graph.ainvoke(initial_state, config)
            
            # Return results
            # Handle both dictionary and WorkflowState object responses from LangGraph
            if isinstance(final_state, dict):
                decision_value = final_state.get('decision')
                if hasattr(decision_value, 'value'):
                    decision = decision_value.value
                elif isinstance(decision_value, str):
                    decision = decision_value
                else:
                    decision = None
                    
                return {
                    'candidate_id': final_state.get('candidate_id'),
                    'candidate_name': final_state.get('candidate_name'),
                    'technical_score': final_state.get('technical_score'),
                    'behavioral_score': final_state.get('behavioral_score'),
                    'experience_score': final_state.get('experience_score'),
                    'cultural_score': final_state.get('cultural_score'),
                    'final_score': final_state.get('final_score'),
                    'decision': decision,
                    'generated_report': final_state.get('generated_report'),
                    'quality_check_passed': final_state.get('quality_check_passed'),
                    'processing_errors': final_state.get('processing_errors', []),
                    'processing_complete': final_state.get('processing_complete', False)
                }
            else:
                return {
                    'candidate_id': final_state.candidate_id,
                    'candidate_name': final_state.candidate_name,
                    'technical_score': final_state.technical_score,
                    'behavioral_score': final_state.behavioral_score,
                    'experience_score': final_state.experience_score,
                    'cultural_score': final_state.cultural_score,
                    'final_score': final_state.final_score,
                    'decision': final_state.decision.value if final_state.decision else None,
                    'generated_report': final_state.generated_report,
                    'quality_check_passed': final_state.quality_check_passed,
                    'processing_errors': final_state.processing_errors or [],
                    'processing_complete': final_state.processing_complete or False
                }
            
        except Exception as e:
            logger.error(f"Assessment workflow failed: {str(e)}")
            raise
        finally:
            # Clear global request
            set_current_request(None)


def get_workflow():
    """Factory function to create workflow instance for LangGraph Studio."""
    workflow_instance = InterviewAssessmentWorkflow()
    return workflow_instance.graph


async def run_interview_assessment(job_id, candidate_id, candidate_name, raw_transcript, 
                                 resume_text, job_description, policy_template, request):
    """
    Main entry point for running the interview assessment workflow.
    
    Args:
        job_id: Job identifier
        candidate_id: Candidate identifier  
        candidate_name: Candidate's name
        raw_transcript: Raw interview transcript
        resume_text: Candidate's resume text
        job_description: Job description dictionary
        policy_template: Report template/policy
        request: FastAPI request object
        
    Returns:
        Dict containing assessment results
    """
    workflow_instance = InterviewAssessmentWorkflow()
    
    # Set the global request for this workflow run
    set_current_request(request)
    
    try:
        # Create input data dictionary for run_assessment
        input_data = {
            'job_id': job_id,
            'candidate_id': candidate_id,
            'candidate_name': candidate_name,
            'raw_transcript': raw_transcript,
            'resume_text': resume_text,
            'job_description': job_description,
            'policy_template': policy_template
        }
        
        # Execute the workflow
        result = await workflow_instance.run_assessment(input_data, request)
        
        return result
        
    finally:
        # Clear global request
        set_current_request(None)