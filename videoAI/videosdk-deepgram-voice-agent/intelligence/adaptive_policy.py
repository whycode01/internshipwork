"""
Adaptive Interview Policy using LangGraph

This module implements an intelligent interview flow using LangGraph to:
- Analyze candidate responses in real-time
- Decide between follow-up questions vs. moving to next topic
- Adapt difficulty based on performance
- Manage interview pacing and time allocation
"""

import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Dict, List, Optional, TypedDict

from groq import Groq
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph


class ResponseQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    PARTIAL = "partial"
    POOR = "poor"
    INCOMPLETE = "incomplete"


class InterviewAction(Enum):
    ASK_FOLLOWUP = "ask_followup"
    MOVE_TO_NEXT = "move_to_next"
    ASK_HINT = "ask_hint"
    CLARIFY_QUESTION = "clarify_question"
    PROVIDE_GUIDANCE = "provide_guidance"
    END_INTERVIEW = "end_interview"


class InterviewState(TypedDict):
    """State that flows through the LangGraph"""
    current_question: str
    question_category: str
    question_difficulty: str
    candidate_response: str
    candidate_name: str
    
    # Analysis results
    response_quality: str
    confidence_score: float
    completeness: float
    technical_accuracy: float
    key_concepts_covered: List[str]
    missing_concepts: List[str]
    
    # Decision results
    next_action: str
    followup_question: Optional[str]
    next_question: Optional[str]
    explanation: str
    
    # Session context
    total_questions_asked: int
    followup_count_current_question: int
    session_start_time: float
    question_start_time: float
    available_questions: List[str]
    questions_used: List[str]
    
    # Interview flow
    should_continue: bool
    final_response: str


class AdaptiveInterviewGraph:
    def __init__(self, groq_api_key: str, model: str = "llama-3.1-8b-instant"):
        try:
            # Try newer Groq client initialization
            self.groq_client = Groq(api_key=groq_api_key)
        except TypeError:
            # Fallback for older versions
            import os
            os.environ["GROQ_API_KEY"] = groq_api_key
            self.groq_client = Groq()
        
        self.model = model
        self.max_followups_per_question = 2
        self.target_session_duration = 1800  # 30 minutes
        
        # Build the LangGraph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for adaptive interview policy"""
        
        # Define the graph
        workflow = StateGraph(InterviewState)
        
        # Add nodes
        workflow.add_node("analyze_response", self._analyze_response_node)
        workflow.add_node("decide_action", self._decide_action_node)
        workflow.add_node("generate_followup", self._generate_followup_node)
        workflow.add_node("select_next_question", self._select_next_question_node)
        workflow.add_node("finalize_response", self._finalize_response_node)
        
        # Set entry point
        workflow.set_entry_point("analyze_response")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "decide_action",
            self._route_decision,
            {
                "followup": "generate_followup",
                "next_question": "select_next_question",
                "end": "finalize_response"
            }
        )
        
        # Add edges
        workflow.add_edge("analyze_response", "decide_action")
        workflow.add_edge("generate_followup", "finalize_response")
        workflow.add_edge("select_next_question", "finalize_response")
        workflow.add_edge("finalize_response", END)
        
        return workflow.compile()
    
    def _analyze_response_node(self, state: InterviewState) -> InterviewState:
        """Node: Analyze candidate response quality and completeness"""
        
        analysis_prompt = f"""
Analyze this technical interview response and provide a detailed assessment:

QUESTION: {state['current_question']}
CATEGORY: {state['question_category']}
DIFFICULTY: {state['question_difficulty']}
CANDIDATE RESPONSE: {state['candidate_response']}

Provide your analysis in JSON format:
{{
    "quality": "excellent|good|partial|poor|incomplete",
    "confidence_score": 0.8,
    "completeness": 0.7,
    "technical_accuracy": 0.9,
    "key_concepts_covered": ["concept1", "concept2"],
    "missing_concepts": ["missing1", "missing2"]
}}

Quality Guidelines:
- EXCELLENT: Complete, accurate, deep understanding, mentions edge cases
- GOOD: Mostly correct, covers main concepts, shows some depth
- PARTIAL: Basic understanding, missing key concepts
- POOR: Incorrect or very incomplete, fundamental misunderstanding
- INCOMPLETE: Too brief, vague, doesn't address the question

Focus on technical accuracy and depth of understanding.
"""

        try:
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.2,
                max_completion_tokens=512
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
                
                # Update state with analysis
                state.update({
                    "response_quality": analysis_data.get("quality", "partial"),
                    "confidence_score": analysis_data.get("confidence_score", 0.5),
                    "completeness": analysis_data.get("completeness", 0.5),
                    "technical_accuracy": analysis_data.get("technical_accuracy", 0.5),
                    "key_concepts_covered": analysis_data.get("key_concepts_covered", []),
                    "missing_concepts": analysis_data.get("missing_concepts", [])
                })
            else:
                # Fallback analysis
                self._fallback_analysis(state)
                
        except Exception as e:
            print(f"Error in response analysis: {e}")
            self._fallback_analysis(state)
        
        return state
    
    def _fallback_analysis(self, state: InterviewState):
        """Simple fallback analysis when LLM analysis fails"""
        response_length = len(state['candidate_response'].strip())
        
        if response_length < 20:
            quality = "incomplete"
            completeness = 0.2
        elif response_length < 100:
            quality = "partial"
            completeness = 0.5
        elif response_length < 300:
            quality = "good"
            completeness = 0.7
        else:
            quality = "excellent"
            completeness = 0.9
            
        state.update({
            "response_quality": quality,
            "confidence_score": 0.6,
            "completeness": completeness,
            "technical_accuracy": 0.6,
            "key_concepts_covered": [],
            "missing_concepts": []
        })
    
    def _decide_action_node(self, state: InterviewState) -> InterviewState:
        """Node: Decide what action to take based on response analysis"""
        
        # Get context
        quality = state['response_quality']
        elapsed_time = time.time() - state['session_start_time']
        time_pressure = elapsed_time > (self.target_session_duration * 0.7)
        at_followup_limit = state['followup_count_current_question'] >= self.max_followups_per_question
        
        # Decision logic
        if quality == "excellent":
            action = InterviewAction.MOVE_TO_NEXT.value
            explanation = "Excellent response demonstrates strong understanding. Moving to next topic."
            
        elif quality == "good":
            if not at_followup_limit and not time_pressure:
                action = InterviewAction.ASK_FOLLOWUP.value
                explanation = "Good response. Exploring deeper understanding with follow-up."
            else:
                action = InterviewAction.MOVE_TO_NEXT.value
                explanation = "Good response. Moving forward due to time/limit constraints."
                
        elif quality == "partial":
            if not at_followup_limit and not time_pressure:
                action = InterviewAction.ASK_FOLLOWUP.value
                explanation = "Partial understanding detected. Asking clarifying question."
            else:
                action = InterviewAction.MOVE_TO_NEXT.value
                explanation = "Partial response but moving forward due to constraints."
                
        elif quality == "poor":
            if not at_followup_limit:
                action = InterviewAction.PROVIDE_GUIDANCE.value
                explanation = "Poor understanding. Providing guidance and simpler approach."
            else:
                action = InterviewAction.MOVE_TO_NEXT.value
                explanation = "Moving to next question after guidance attempts."
                
        else:  # incomplete
            if not at_followup_limit:
                action = InterviewAction.CLARIFY_QUESTION.value
                explanation = "Response too brief. Asking for elaboration."
            else:
                action = InterviewAction.MOVE_TO_NEXT.value
                explanation = "Moving forward after multiple clarification attempts."
        
        # Check if we should end the interview
        if time_pressure and state['total_questions_asked'] >= 8:
            action = InterviewAction.END_INTERVIEW.value
            explanation = "Interview time limit reached. Concluding session."
        
        state.update({
            "next_action": action,
            "explanation": explanation
        })
        
        return state
    
    def _route_decision(self, state: InterviewState) -> str:
        """Route to appropriate node based on decision"""
        action = state['next_action']
        
        if action in [InterviewAction.ASK_FOLLOWUP.value, 
                     InterviewAction.PROVIDE_GUIDANCE.value, 
                     InterviewAction.CLARIFY_QUESTION.value]:
            return "followup"
        elif action == InterviewAction.MOVE_TO_NEXT.value:
            return "next_question"
        else:  # END_INTERVIEW
            return "end"
    
    def _generate_followup_node(self, state: InterviewState) -> InterviewState:
        """Node: Generate intelligent follow-up question"""
        
        action = state['next_action']
        original_question = state['current_question']
        missing_concepts = state['missing_concepts']
        
        if action == InterviewAction.ASK_FOLLOWUP.value:
            if missing_concepts:
                concept = missing_concepts[0]
                followup = f"You mentioned some good points. How would you handle {concept} in this scenario?"
            else:
                followup = "Can you walk me through your reasoning for that approach in more detail?"
                
        elif action == InterviewAction.PROVIDE_GUIDANCE.value:
            followup = "Let me give you a hint: think about the core problem step by step. What would be your first step in solving this?"
            
        elif action == InterviewAction.CLARIFY_QUESTION.value:
            followup = f"Could you elaborate more on your approach to: {original_question}"
            
        else:
            followup = "Could you explain your thinking process a bit more?"
        
        state.update({
            "followup_question": followup,
            "followup_count_current_question": state['followup_count_current_question'] + 1
        })
        
        return state
    
    def _select_next_question_node(self, state: InterviewState) -> InterviewState:
        """Node: Select next question from available pool"""
        
        available = [q for q in state['available_questions'] if q not in state['questions_used']]
        
        if available:
            # Simple selection - get the first unused question
            next_q = available[0]
            
            # Ensure we don't repeat the current question
            if next_q == state['current_question'] and len(available) > 1:
                next_q = available[1]
            
            state.update({
                "next_question": next_q,
                "questions_used": state['questions_used'] + [next_q],
                "total_questions_asked": state['total_questions_asked'] + 1,
                "followup_count_current_question": 0  # Reset for new question
            })
        else:
            # No more questions available
            state.update({
                "next_action": InterviewAction.END_INTERVIEW.value,
                "explanation": "No more questions available. Ending interview."
            })
        
        return state
    
    def _finalize_response_node(self, state: InterviewState) -> InterviewState:
        """Node: Prepare final response for the interviewer"""
        
        action = state['next_action']
        
        if action == InterviewAction.END_INTERVIEW.value:
            final_response = "Thank you for your time today. That concludes our technical interview. We'll be in touch soon!"
            state["should_continue"] = False
            
        elif state.get('followup_question'):
            final_response = state['followup_question']
            state["should_continue"] = True
            
        elif state.get('next_question'):
            # Present the new question clearly without "Great!" or transition
            next_q = state['next_question']
            # Check if it's a different question than the current one
            if next_q != state['current_question']:
                final_response = next_q
            else:
                # Fallback if somehow same question selected
                final_response = "Let me ask you about something different. Can you tell me about your experience with software development?"
            state["should_continue"] = True
            
        else:
            final_response = "Let me think of the next question for you."
            state["should_continue"] = True
        
        state.update({
            "final_response": final_response
        })
        
        return state
    
    def process_candidate_response(self, 
                                 current_question: str,
                                 question_category: str,
                                 question_difficulty: str,
                                 candidate_response: str,
                                 candidate_name: str,
                                 session_context: Dict) -> Dict:
        """
        Process candidate response through the adaptive policy graph
        
        Returns:
            Dict with 'action', 'response', 'should_continue', and updated context
        """
        
        # Prepare initial state
        initial_state = InterviewState(
            current_question=current_question,
            question_category=question_category,
            question_difficulty=question_difficulty,
            candidate_response=candidate_response,
            candidate_name=candidate_name,
            
            # Initialize analysis fields
            response_quality="",
            confidence_score=0.0,
            completeness=0.0,
            technical_accuracy=0.0,
            key_concepts_covered=[],
            missing_concepts=[],
            
            # Initialize decision fields
            next_action="",
            followup_question=None,
            next_question=None,
            explanation="",
            
            # Session context
            total_questions_asked=session_context.get('total_questions_asked', 0),
            followup_count_current_question=session_context.get('followup_count_current_question', 0),
            session_start_time=session_context.get('session_start_time', time.time()),
            question_start_time=session_context.get('question_start_time', time.time()),
            available_questions=session_context.get('available_questions', []),
            questions_used=session_context.get('questions_used', []),
            
            # Flow control
            should_continue=True,
            final_response=""
        )
        
        # Run the graph
        try:
            result = self.graph.invoke(initial_state)
            
            # Extract results
            return {
                'action': result['next_action'],
                'response': result['final_response'],
                'should_continue': result['should_continue'],
                'explanation': result['explanation'],
                'analysis': {
                    'quality': result['response_quality'],
                    'confidence': result['confidence_score'],
                    'completeness': result['completeness'],
                    'technical_accuracy': result['technical_accuracy'],
                    'concepts_covered': result['key_concepts_covered'],
                    'missing_concepts': result['missing_concepts']
                },
                'updated_context': {
                    'total_questions_asked': result['total_questions_asked'],
                    'followup_count_current_question': result['followup_count_current_question'],
                    'questions_used': result['questions_used'],
                    'session_start_time': result['session_start_time'],
                    'question_start_time': result.get('question_start_time', time.time()),
                    'available_questions': result['available_questions']
                }
            }
            
        except Exception as e:
            print(f"Error processing response through graph: {e}")
            return {
                'action': 'move_to_next',
                'response': 'Thank you for your response. Let\'s continue with the next question.',
                'should_continue': True,
                'explanation': 'Fallback due to processing error',
                'analysis': {},
                'updated_context': session_context
            }


# Usage example and integration helper
class InterviewFlowManager:
    """Helper class to integrate adaptive policy with existing interview system"""
    
    def __init__(self, groq_api_key: str, questions_manager=None):
        self.adaptive_graph = AdaptiveInterviewGraph(groq_api_key)
        self.questions_manager = questions_manager
        self.session_context = {
            'total_questions_asked': 0,
            'followup_count_current_question': 0,
            'session_start_time': time.time(),
            'questions_used': [],
            'available_questions': []
        }
        
        # Load available questions if manager provided
        if self.questions_manager:
            questions = self._get_questions_from_manager()
            self.session_context['available_questions'] = [q.text for q in questions]
    
    def _get_questions_from_manager(self):
        """Helper to get questions from either file or API manager"""
        if not self.questions_manager:
            return []
        
        # File-based manager
        if hasattr(self.questions_manager, 'get_current_questions'):
            return self.questions_manager.get_current_questions() or []
        
        # API-based manager  
        elif hasattr(self.questions_manager, 'questions_data'):
            if self.questions_manager.questions_data and 'questions' in self.questions_manager.questions_data:
                # Convert API questions to a compatible format
                api_questions = self.questions_manager.questions_data['questions']
                compatible_questions = []
                for q in api_questions:
                    class APIQuestion:
                        def __init__(self, text, category="general", difficulty="medium"):
                            self.text = text
                            self.category = type('Category', (), {'value': category})()
                            self.difficulty = difficulty
                    
                    question_text = q.get('text', q.get('question', ''))
                    category = q.get('category', 'general')
                    difficulty = q.get('difficulty', 'medium')
                    compatible_questions.append(APIQuestion(question_text, category, difficulty))
                
                return compatible_questions
        
        return []
    
    def process_response(self, current_question: str, candidate_response: str, 
                        candidate_name: str, question_category: str = "technical", 
                        question_difficulty: str = "medium") -> Dict:
        """Process candidate response and get next action"""
        
        result = self.adaptive_graph.process_candidate_response(
            current_question=current_question,
            question_category=question_category,
            question_difficulty=question_difficulty,
            candidate_response=candidate_response,
            candidate_name=candidate_name,
            session_context=self.session_context
        )
        
        # Update session context
        self.session_context.update(result['updated_context'])
        
        return result
    
    def get_session_stats(self) -> Dict:
        """Get current session statistics"""
        elapsed_time = time.time() - self.session_context['session_start_time']
        return {
            'total_questions': self.session_context['total_questions_asked'],
            'elapsed_time_minutes': elapsed_time / 60,
            'questions_remaining': len(self.session_context['available_questions']) - len(self.session_context['questions_used']),
            'current_followups': self.session_context['followup_count_current_question']
        }