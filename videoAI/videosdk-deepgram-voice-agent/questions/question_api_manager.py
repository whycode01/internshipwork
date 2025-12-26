#!/usr/bin/env python3
"""
API-based Question Manager
Fetches questions from REST API instead of MD files
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

import requests


class QuestionCategory(Enum):
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    CODING = "coding"
    SYSTEM_DESIGN = "system_design"
    AI_ML = "ai_ml"
    PYTHON = "python"
    DSA = "dsa"

class QuestionDifficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

@dataclass
class APIQuestion:
    id: int
    text: str
    category: QuestionCategory
    difficulty: QuestionDifficulty
    job_id: int
    order: int
    metadata: Optional[Dict] = None

class QuestionAPIManager:
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.api_base_url = self.base_url  # Keep both for compatibility
        self.timeout = timeout
        self.questions_data = None  # Store raw API response
        self.questions: List[APIQuestion] = []
        self.current_index = 0
        self.job_id = None
        self.candidate_id = None
        self.interview_metadata = {}
    
    def fetch_questions(self, job_id: str, candidate_id: str) -> Optional[Dict]:
        """
        Fetch questions from API using the new format expected by main.py
        
        Returns:
            Dict with questions and metadata, or None if failed
        """
        try:
            print(f"🌐 [API] Fetching questions for job_id={job_id}, candidate_id={candidate_id}")
            
            # Make API call to fetch questions
            url = f"{self.base_url}/api/questions/candidate/{candidate_id}"
            params = {"job_id": job_id} if job_id else {}
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse response
            api_response = response.json()
            
            # Handle the actual API response format
            if api_response.get('status') == 'success' and 'data' in api_response:
                data = api_response['data']
                
                # Extract questions and convert field names to expected format
                questions = []
                for q in data.get('questions', []):
                    # Convert API question format to expected format
                    converted_question = {
                        'id': q.get('id'),
                        'text': q.get('question_text', ''),  # Map question_text to text
                        'question': q.get('question_text', ''),  # Also provide as question for compatibility
                        'category': self._map_question_type_to_category(q.get('question_type', 'Technical')),
                        'difficulty': q.get('metadata', {}).get('difficulty', 'medium'),
                        'type': q.get('question_type', 'Technical'),
                        'objective': q.get('objective', ''),
                        'metadata': q.get('metadata', {})
                    }
                    questions.append(converted_question)
                
                # Store the processed data in the format expected by the intelligence client
                self.questions_data = {
                    'questions': questions,
                    'metadata': {
                        'candidate_id': data.get('metadata', {}).get('candidate_id', candidate_id),
                        'job_id': data.get('metadata', {}).get('job_id', job_id),
                        'job_category': data.get('metadata', {}).get('job_category', ''),
                        'interview_type': self._derive_interview_type(data.get('metadata', {})),
                        'total_questions': data.get('metadata', {}).get('total_questions', len(questions)),
                        'generated_at': data.get('metadata', {}).get('generated_at', ''),
                        'policy_context': data.get('metadata', {}).get('policy_context', '')
                    }
                }
                
                self.job_id = job_id
                self.candidate_id = candidate_id
                
                print(f"✅ [API] Loaded {len(questions)} questions successfully")
                print(f"   📊 Job Category: {self.questions_data['metadata'].get('job_category', 'N/A')}")
                print(f"   🎯 Interview Type: {self.questions_data['metadata'].get('interview_type', 'N/A')}")
                return self.questions_data
            else:
                print(f"❌ [API] Unexpected response format or failed status")
                return None
            
        except requests.exceptions.RequestException as e:
            print(f"❌ [API] Network error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ [API] JSON parsing error: {e}")
            return None
        except Exception as e:
            print(f"❌ [API] Unexpected error: {e}")
            return None
    
    def _map_question_type_to_category(self, question_type: str) -> str:
        """Map API question_type to our category system"""
        type_mapping = {
            'Technical': 'technical',
            'Behavioral': 'behavioral', 
            'Situational': 'situational',
            'Policy/Compliance': 'policy',
            'Cultural Fit': 'cultural',
        }
        return type_mapping.get(question_type, 'general')
    
    def _derive_interview_type(self, metadata: Dict) -> str:
        """Derive interview type from API metadata for personality detection"""
        job_category = metadata.get('job_category', '').lower()
        policy_context = metadata.get('policy_context', '').lower()
        
        # Map job categories to interview types
        if 'corporate' in job_category or 'finance' in policy_context:
            return 'corporate_interview'
        elif 'technical' in job_category or 'software' in job_category:
            return 'technical_interview'
        elif 'marketing' in policy_context:
            return 'marketing_interview'
        else:
            return 'general_interview'
    def load_questions_from_api(self, job_id: int, candidate_id: int) -> bool:
        """
        Load questions from API for specific job and candidate (legacy method)
        
        Args:
            job_id: Job ID for the interview
            candidate_id: Candidate ID for the interview
            
        Returns:
            bool: True if questions loaded successfully, False otherwise
        """
        result = self.fetch_questions(str(job_id), str(candidate_id))
        return result is not None
    
    def get_current_questions(self) -> List[APIQuestion]:
        """Get all loaded questions"""
        return self.questions
    
    def get_next_question(self) -> Optional[APIQuestion]:
        """Get the next question in sequence"""
        if self.current_index < len(self.questions):
            question = self.questions[self.current_index]
            self.current_index += 1
            return question
        return None
    
    def get_current_question(self) -> Optional[APIQuestion]:
        """Get the current question without advancing"""
        if 0 <= self.current_index - 1 < len(self.questions):
            return self.questions[self.current_index - 1]
        return None
    
    def get_questions_summary(self) -> Dict:
        """Get summary of loaded questions"""
        if not self.questions:
            return {'total': 0, 'categories': {}, 'difficulties': {}}
            
        categories = {}
        difficulties = {}
        
        for question in self.questions:
            cat = question.category.value
            diff = question.difficulty.value
            categories[cat] = categories.get(cat, 0) + 1
            difficulties[diff] = difficulties.get(diff, 0) + 1
        
        return {
            'total': len(self.questions),
            'categories': categories,
            'difficulties': difficulties,
            'job_id': self.job_id,
            'candidate_id': self.candidate_id,
            'metadata': self.interview_metadata
        }
    
    def _get_categories_summary(self) -> List[str]:
        """Get list of unique categories"""
        return list(set(q.category.value for q in self.questions))
    
    def _get_difficulties_summary(self) -> List[str]:
        """Get list of unique difficulties"""
        return list(set(q.difficulty.value for q in self.questions))
    
    def send_response_to_api(self, question_id: int, candidate_response: str, 
                           analysis: Optional[Dict] = None) -> bool:
        """
        Send candidate response back to API for tracking/analysis
        
        Args:
            question_id: ID of the question that was answered
            candidate_response: The candidate's response text
            analysis: Optional analysis data from adaptive policy
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            url = f"{self.api_base_url}/api/responses"
            
            payload = {
                'question_id': question_id,
                'candidate_id': self.candidate_id,
                'job_id': self.job_id,
                'response_text': candidate_response,
                'timestamp': self._get_current_timestamp(),
                'analysis': analysis or {}
            }
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            print(f"✅ [API] Response sent for question {question_id}")
            return True
            
        except Exception as e:
            print(f"⚠️ [API] Failed to send response: {e}")
            return False
    
    def get_interview_personality(self) -> str:
        """
        Get interview personality from API metadata
        Falls back to analyzing question content if not provided
        """
        # Check if API provided personality
        if 'personality' in self.interview_metadata:
            return self.interview_metadata['personality']
        
        # Check if API provided interview type
        if 'interview_type' in self.interview_metadata:
            type_mapping = {
                'python': 'python_expert',
                'ai_ml': 'ai_ml_expert',
                'data_science': 'ai_ml_expert',
                'algorithms': 'dsa_expert',
                'system_design': 'system_design_expert',
                'general': 'sde_interviewer'
            }
            return type_mapping.get(self.interview_metadata['interview_type'], 'sde_interviewer')
        
        # Fallback to analyzing question categories
        if not self.questions:
            return 'sde_interviewer'
        
        categories = [q.category.value for q in self.questions]
        
        if 'python' in categories:
            return 'python_expert'
        elif 'ai_ml' in categories:
            return 'ai_ml_expert'
        elif 'dsa' in categories or 'coding' in categories:
            return 'dsa_expert'
        elif 'system_design' in categories:
            return 'system_design_expert'
        else:
            return 'sde_interviewer'
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def list_uploaded_files(self) -> List[str]:
        """Compatibility method for file-based question manager"""
        return []  # API doesn't use files
    
    def load_existing_file(self, filename: str) -> bool:
        """Compatibility method for file-based question manager"""
        print(f"⚠️ [API] load_existing_file called but using API mode")
        return False
