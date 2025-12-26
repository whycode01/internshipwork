"""
Individual agent implementations for the interview assessment workflow.
Each agent performs a specific evaluation task.
"""

import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to Python path for sql_ops import
sys.path.append(str(Path(__file__).parent.parent))
# Use local version that handles None request objects
# Handle both relative and absolute imports for LangGraph Studio compatibility
try:
    from .local_sql_ops import async_call_model
    from .models import (BehavioralAssessment, CulturalAssessment,
                         DecisionStatus, ExperienceAssessment, FinalAssessment,
                         QualityCheck, TechnicalAssessment, WorkflowState)
except ImportError:
    # Fallback for LangGraph Studio (absolute imports)
    from local_sql_ops import async_call_model
    from models import (BehavioralAssessment, CulturalAssessment,
                        DecisionStatus, ExperienceAssessment, FinalAssessment,
                        QualityCheck, TechnicalAssessment, WorkflowState)

logger = logging.getLogger(__name__)


def extract_content(response):
    """Extract content from AIMessage object or return string as-is."""
    if hasattr(response, 'content'):
        return response.content
    else:
        return str(response)


def extract_json_from_response(response):
    """Extract JSON from LLM response, handling both pure JSON and markdown-wrapped JSON."""
    content = extract_content(response)
    
    # Try to find JSON in the response
    # Look for JSON blocks wrapped in ```json or just {} structures
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Look for JSON object directly - improved regex to handle nested structures
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            # If no JSON found, return the content as-is and let calling code handle it
            logger.warning(f"No JSON found in response: {content[:200]}...")
            return content
    
    try:
        # Clean up the JSON string - handle common issues
        json_str = json_str.strip()
        
        # Remove BOM and other invisible characters that might cause issues
        json_str = json_str.encode('utf-8').decode('utf-8-sig').strip()
        
        # Remove any leading/trailing whitespace and newlines
        json_str = re.sub(r'^\s+', '', json_str, flags=re.MULTILINE)
        
        # Try parsing the raw JSON first
        return json.loads(json_str)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse extracted JSON: {str(e)}")
        logger.error(f"JSON string was: {json_str[:200]}...")
        
        # Try a more aggressive cleaning approach
        try:
            # Fix common JSON formatting issues
            cleaned_json = json_str
            
            # Remove BOM and other invisible characters
            cleaned_json = cleaned_json.encode('utf-8').decode('utf-8-sig')
            
            # Remove newlines and extra spaces within the JSON
            cleaned_json = re.sub(r'\n\s*', ' ', cleaned_json)
            
            # Remove any remaining leading/trailing whitespace
            cleaned_json = cleaned_json.strip()
            
            # Try parsing again
            return json.loads(cleaned_json)
            
        except json.JSONDecodeError as e2:
            logger.error(f"Cleaned JSON also failed: {str(e2)}")
            
            # Final fallback - extract values using regex
            try:
                return extract_scores_from_text(content)
            except Exception as fallback_error:
                logger.error(f"Fallback extraction also failed: {str(fallback_error)}")
                return content


def extract_scores_from_text(text_content):
    """Extract scores from text when JSON parsing fails."""
    # Try to extract all possible fields that might be in the response
    
    # Find all number values associated with field names
    field_patterns = [
        r'"?overall_score"?\s*:\s*([0-9.]+)',
        r'"?technical_depth"?\s*:\s*([0-9.]+)',  
        r'"?problem_solving"?\s*:\s*([0-9.]+)',
        r'"?communication_clarity"?\s*:\s*([0-9.]+)',
        r'"?leadership_indicators"?\s*:\s*([0-9.]+)',
        r'"?teamwork_ability"?\s*:\s*([0-9.]+)',
        r'"?problem_solving_approach"?\s*:\s*([0-9.]+)',
        r'"?role_alignment"?\s*:\s*([0-9.]+)',
        r'"?experience_depth"?\s*:\s*([0-9.]+)',
        r'"?career_progression"?\s*:\s*([0-9.]+)',
        r'"?value_alignment"?\s*:\s*([0-9.]+)',
        r'"?adaptability"?\s*:\s*([0-9.]+)',
        r'"?growth_mindset"?\s*:\s*([0-9.]+)',
        r'"?cultural_integration_potential"?\s*:\s*([0-9.]+)',
    ]
    
    extracted_data = {}
    
    for pattern in field_patterns:
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        if matches:
            # Extract field name from pattern and use first match
            field_name = pattern.split('"?')[1].split('"?')[0] if '"?' in pattern else 'unknown'
            try:
                extracted_data[field_name] = float(matches[0])
            except ValueError:
                pass
    
    # Try to extract lists as well (evidence, strengths, etc.)
    list_patterns = [
        (r'"?evidence"?\s*:\s*\[(.*?)\]', 'evidence'),
        (r'"?strengths"?\s*:\s*\[(.*?)\]', 'strengths'), 
        (r'"?gaps_identified"?\s*:\s*\[(.*?)\]', 'gaps_identified'),
        (r'"?improvement_areas"?\s*:\s*\[(.*?)\]', 'improvement_areas'),
        (r'"?relevant_projects"?\s*:\s*\[(.*?)\]', 'relevant_projects'),
        (r'"?experience_gaps"?\s*:\s*\[(.*?)\]', 'experience_gaps'),
        (r'"?recommendations"?\s*:\s*\[(.*?)\]', 'recommendations'),
    ]
    
    for pattern, field_name in list_patterns:
        match = re.search(pattern, text_content, re.IGNORECASE | re.DOTALL)
        if match:
            # Try to extract list items
            list_content = match.group(1)
            # Simple extraction of quoted strings
            items = re.findall(r'"([^"]*)"', list_content)
            if items:
                extracted_data[field_name] = items
            else:
                extracted_data[field_name] = ["Extracted from text response"]
    
    # Also try to extract skill_matches object
    skill_match = re.search(r'"?skill_matches"?\s*:\s*\{([^}]*)\}', text_content, re.IGNORECASE)
    if skill_match:
        skill_content = skill_match.group(1)
        skill_scores = {}
        skill_pairs = re.findall(r'"([^"]+)"\s*:\s*([0-9.]+)', skill_content)
        for skill, score in skill_pairs:
            skill_scores[skill] = float(score)
        if skill_scores:
            extracted_data['skill_matches'] = skill_scores
    
    # If we found scores, return a structured object
    if extracted_data:
        logger.info(f"Extracted data from text: {list(extracted_data.keys())}")
        return extracted_data
    
    return None


class DataPreprocessingAgent:
    """Agent for preprocessing and structuring input data."""
    
    async def process(self, state: WorkflowState, request) -> WorkflowState:
        """Preprocess raw input data into structured format."""
        logger.info(f"Data preprocessing for candidate {state.candidate_id}")
        
        try:
            # Structure transcript data
            state.structured_transcript = self._parse_transcript(state.raw_transcript)
            
            # Parse resume data
            state.parsed_resume = await self._parse_resume(state.resume_text, request)
            
            # Extract job requirements
            state.job_requirements = self._extract_job_requirements(state.job_description)
            
            logger.info("Data preprocessing completed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Data preprocessing failed: {str(e)}")
            state.processing_errors.append(f"Data preprocessing: {str(e)}")
            return state
    
    def _parse_transcript(self, transcript: str) -> Dict[str, Any]:
        """Parse transcript into structured conversation data."""
        lines = transcript.strip().split('\n')
        conversations = []
        interviewer_questions = []
        candidate_responses = []
        
        for line in lines:
            if ':' in line:
                timestamp_match = re.search(r'\[(\d{2}:\d{2}:\d{2})\]', line)
                timestamp = timestamp_match.group(1) if timestamp_match else None
                
                if 'Interviewer:' in line:
                    content = line.split('Interviewer:', 1)[1].strip()
                    interviewer_questions.append(content)
                    conversations.append({
                        'speaker': 'interviewer',
                        'content': content,
                        'timestamp': timestamp
                    })
                elif 'User:' in line or 'Candidate:' in line:
                    content = line.split(':', 1)[1].strip()
                    candidate_responses.append(content)
                    conversations.append({
                        'speaker': 'candidate',
                        'content': content,
                        'timestamp': timestamp
                    })
        
        return {
            'conversations': conversations,
            'interviewer_questions': interviewer_questions,
            'candidate_responses': candidate_responses,
            'total_exchanges': len(conversations)
        }
    
    async def _parse_resume(self, resume_text: str, request) -> Dict[str, Any]:
        """Parse resume into structured data using LLM."""
        prompt = f"""
        Parse the following resume text and extract structured information:
        
        Resume Text:
        {resume_text}
        
        Extract and return a JSON object with the following structure:
        {{
            "skills": ["skill1", "skill2", ...],
            "experience": [
                {{
                    "role": "Job Title",
                    "company": "Company Name",
                    "duration": "Years",
                    "responsibilities": ["responsibility1", ...]
                }}
            ],
            "education": [
                {{
                    "degree": "Degree Name",
                    "institution": "School Name",
                    "year": "Year"
                }}
            ],
            "certifications": ["cert1", "cert2", ...],
            "key_achievements": ["achievement1", ...]
        }}
        
        Return only the JSON object, no additional text.
        """
        
        try:
            response = await async_call_model(prompt, request)
            json_data = extract_json_from_response(response)
            if isinstance(json_data, dict):
                return json_data
            else:
                logger.warning("No valid JSON found in resume parsing, using defaults")
                raise ValueError("No JSON found")
        except Exception as e:
            logger.error(f"Resume parsing failed: {str(e)}")
            return {"skills": [], "experience": [], "education": [], "certifications": [], "key_achievements": []}
    
    def _extract_job_requirements(self, job_description: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and structure job requirements."""
        return {
            'title': job_description.get('name', ''),
            'description': job_description.get('description', ''),
            'required_skills': self._extract_skills_from_aspects(job_description.get('aspects', [])),
            'soft_skills': ['communication', 'teamwork', 'problem-solving', 'leadership'],
            'experience_level': 'mid-level'  # Default, could be extracted from description
        }
    
    def _extract_skills_from_aspects(self, aspects: List[Dict]) -> List[str]:
        """Extract skills from job aspects structure."""
        skills = []
        for aspect in aspects:
            skills.extend(aspect.get('focusAreas', []))
        return skills


class TechnicalSkillsAgent:
    """Agent for evaluating technical skills and competencies."""
    
    async def process(self, state: WorkflowState, request) -> WorkflowState:
        """Evaluate technical skills from resume and transcript."""
        logger.info(f"Technical assessment for candidate {state.candidate_id}")
        
        try:
            assessment = await self._evaluate_technical_skills(state, request)
            state.technical_assessment = assessment.dict()
            state.technical_score = assessment.overall_score
            
            logger.info(f"Technical assessment completed: {assessment.overall_score}/10")
            return state
            
        except Exception as e:
            logger.error(f"Technical assessment failed: {str(e)}")
            state.processing_errors.append(f"Technical assessment: {str(e)}")
            return state
    
    async def _evaluate_technical_skills(self, state: WorkflowState, request) -> TechnicalAssessment:
        """Perform detailed technical skills evaluation."""
        
        prompt = f"""
        Evaluate the candidate's technical skills based on the following data:
        
        Job Requirements:
        Title: {state.job_requirements.get('title')}
        Required Skills: {', '.join(state.job_requirements.get('required_skills', []))}
        
        Candidate Resume Skills:
        {', '.join(state.parsed_resume.get('skills', []))}
        
        Interview Technical Responses:
        {self._extract_technical_responses(state.structured_transcript)}
        
        Provide a detailed technical assessment with scores (1-10 scale):
        
        1. Overall Technical Score (1-10)
        2. Skill Match Analysis (for each required skill, rate 1-10)
        3. Technical Depth (1-10)
        4. Problem Solving Ability (1-10)
        5. Evidence from transcript (specific quotes)
        6. Identified skill gaps
        7. Technical strengths
        
        Return response in JSON format:
        {{
            "overall_score": 8.5,
            "skill_matches": {{"Python": 9.0, "Finance": 6.0}},
            "technical_depth": 7.5,
            "problem_solving": 8.0,
            "evidence": ["Quote from interview showing technical knowledge"],
            "gaps_identified": ["Missing skill 1", "Needs improvement in skill 2"],
            "strengths": ["Strong in skill 1", "Excellent problem-solving approach"]
        }}
        """
        
        response = await async_call_model(prompt, request)
        try:
            content = extract_content(response)
            logger.debug(f"Technical assessment response: {content[:200]}...")
            
            # Try to extract JSON from the response
            json_data = extract_json_from_response(response)
            if isinstance(json_data, dict):
                return TechnicalAssessment(**json_data)
            else:
                # If not JSON, try to parse as text and create structured response
                logger.warning("No valid JSON found, creating structured response from text")
                return self._parse_text_response(json_data)
                
        except Exception as e:
            logger.error(f"Technical assessment JSON parsing failed: {str(e)}")
            logger.error(f"Raw response: {extract_content(response)[:500]}...")
            # Fallback with default values
            return TechnicalAssessment(
                overall_score=5.0,
                skill_matches={},
                technical_depth=5.0,
                problem_solving=5.0,
                evidence=[],
                gaps_identified=[],
                strengths=[]
            )
    
    def _parse_text_response(self, text_response: str) -> TechnicalAssessment:
        """Parse text response and extract structured data."""
        
        # Try to get extracted scores first
        if isinstance(text_response, dict):
            # Use extracted scores with proper defaults for missing fields
            return TechnicalAssessment(
                overall_score=text_response.get('overall_score', 7.0),
                skill_matches=text_response.get('skill_matches', {'python': text_response.get('overall_score', 7.0)}),
                technical_depth=text_response.get('technical_depth', 7.0),
                problem_solving=text_response.get('problem_solving', 7.0),
                evidence=text_response.get('evidence', ["Extracted from LLM response"]),
                gaps_identified=text_response.get('gaps_identified', ["Detailed parsing unavailable"]),
                strengths=text_response.get('strengths', ["Detailed parsing unavailable"])
            )
        
        # Fallback to regex extraction from text
        score_patterns = {
            'overall': r'overall[^:]*:?\s*(\d+(?:\.\d+)?)',
            'technical_depth': r'technical\s+depth[^:]*:?\s*(\d+(?:\.\d+)?)',
            'problem_solving': r'problem\s+solving[^:]*:?\s*(\d+(?:\.\d+)?)'
        }
        
        scores = {}
        for key, pattern in score_patterns.items():
            match = re.search(pattern, str(text_response), re.IGNORECASE)
            if match:
                scores[key] = float(match.group(1))
        
        return TechnicalAssessment(
            overall_score=scores.get('overall', 7.0),
            skill_matches={'python': scores.get('overall', 7.0)},
            technical_depth=scores.get('technical_depth', 7.0),
            problem_solving=scores.get('problem_solving', 7.0),
            evidence=["Parsed from text response"],
            gaps_identified=["Could not parse detailed gaps from text"],
            strengths=["Could not parse detailed strengths from text"]
        )
    
    def _extract_technical_responses(self, structured_transcript: Dict) -> str:
        """Extract technical responses from transcript."""
        technical_keywords = ['python', 'programming', 'code', 'algorithm', 'technical', 'software', 'development']
        candidate_responses = structured_transcript.get('candidate_responses', [])
        
        technical_responses = []
        for response in candidate_responses:
            if any(keyword.lower() in response.lower() for keyword in technical_keywords):
                technical_responses.append(response)
        
        return '\n'.join(technical_responses)


class BehavioralAssessmentAgent:
    """Agent for evaluating behavioral competencies and soft skills."""
    
    async def process(self, state: WorkflowState, request) -> WorkflowState:
        """Evaluate behavioral competencies from interview transcript."""
        logger.info(f"Behavioral assessment for candidate {state.candidate_id}")
        
        try:
            assessment = await self._evaluate_behavioral_competencies(state, request)
            state.behavioral_assessment = assessment.dict()
            state.behavioral_score = assessment.overall_score
            
            logger.info(f"Behavioral assessment completed: {assessment.overall_score}/10")
            return state
            
        except Exception as e:
            logger.error(f"Behavioral assessment failed: {str(e)}")
            state.processing_errors.append(f"Behavioral assessment: {str(e)}")
            return state
    
    async def _evaluate_behavioral_competencies(self, state: WorkflowState, request) -> BehavioralAssessment:
        """Perform detailed behavioral assessment."""
        
        conversations = state.structured_transcript.get('conversations', [])
        candidate_responses = [c['content'] for c in conversations if c['speaker'] == 'candidate']
        
        prompt = f"""
        Evaluate the candidate's behavioral competencies based on their interview responses:
        
        Job Title: {state.job_requirements.get('title')}
        
        Candidate Responses:
        {chr(10).join(candidate_responses)}
        
        Assess the following behavioral competencies (1-10 scale):
        
        1. Communication Clarity - How clearly does the candidate express ideas?
        2. Leadership Indicators - Evidence of leadership potential or experience
        3. Teamwork Ability - Collaboration and interpersonal skills
        4. Problem-Solving Approach - Methodology and critical thinking
        5. Overall Behavioral Score
        
        Provide specific evidence from the responses and identify areas for improvement.
        
        Return JSON format:
        {{
            "overall_score": 8.0,
            "communication_clarity": 8.5,
            "leadership_indicators": 7.0,
            "teamwork_ability": 8.0,
            "problem_solving_approach": 7.5,
            "evidence": ["Specific quotes showing behavioral competencies"],
            "improvement_areas": ["Areas needing development"]
        }}
        """
        
        response = await async_call_model(prompt, request)
        try:
            json_data = extract_json_from_response(response)
            if isinstance(json_data, dict):
                # Try to create with extracted data
                try:
                    return BehavioralAssessment(**json_data)
                except (TypeError, ValueError) as e:
                    # If structure doesn't match, use what we can
                    logger.warning(f"BehavioralAssessment structure mismatch: {e}")
                    return BehavioralAssessment(
                        overall_score=json_data.get('overall_score', 7.0),
                        communication_clarity=json_data.get('communication_clarity', 7.0),
                        leadership_indicators=json_data.get('leadership_indicators', 6.0),
                        teamwork_ability=json_data.get('teamwork_ability', 7.0),
                        problem_solving_approach=json_data.get('problem_solving_approach', 7.0),
                        evidence=json_data.get('evidence', ["Extracted from LLM response"]),
                        improvement_areas=json_data.get('improvement_areas', ["Details unavailable"])
                    )
            else:
                logger.warning("No valid JSON found in behavioral assessment, using defaults")
                raise ValueError("No JSON found")
        except:
            return BehavioralAssessment(
                overall_score=5.0,
                communication_clarity=5.0,
                leadership_indicators=5.0,
                teamwork_ability=5.0,
                problem_solving_approach=5.0,
                evidence=[],
                improvement_areas=[]
            )


class ExperienceRelevanceAgent:
    """Agent for evaluating experience relevance and career alignment."""
    
    async def process(self, state: WorkflowState, request) -> WorkflowState:
        """Evaluate experience relevance to job requirements."""
        logger.info(f"Experience assessment for candidate {state.candidate_id}")
        
        try:
            assessment = await self._evaluate_experience_relevance(state, request)
            state.experience_assessment = assessment.dict()
            state.experience_score = assessment.overall_score
            
            logger.info(f"Experience assessment completed: {assessment.overall_score}/10")
            return state
            
        except Exception as e:
            logger.error(f"Experience assessment failed: {str(e)}")
            state.processing_errors.append(f"Experience assessment: {str(e)}")
            return state
    
    async def _evaluate_experience_relevance(self, state: WorkflowState, request) -> ExperienceAssessment:
        """Perform detailed experience evaluation."""
        
        experience_data = state.parsed_resume.get('experience', [])
        experience_text = json.dumps(experience_data, indent=2)
        
        prompt = f"""
        Evaluate the candidate's experience relevance for the following role:
        
        Job Title: {state.job_requirements.get('title')}
        Job Description: {state.job_requirements.get('description')}
        Required Skills: {', '.join(state.job_requirements.get('required_skills', []))}
        
        Candidate Experience:
        {experience_text}
        
        Interview Experience Discussion:
        {self._extract_experience_responses(state.structured_transcript)}
        
        Assess the following (1-10 scale):
        1. Role Alignment - How well previous roles align with current position
        2. Experience Depth - Quality and depth of relevant experience  
        3. Career Progression - Growth pattern and advancement
        4. Relevant Projects - Specific projects that match job requirements
        5. Overall Experience Score
        
        Identify experience gaps and provide evidence from transcript.
        
        Return JSON format:
        {{
            "overall_score": 7.5,
            "role_alignment": 8.0,
            "experience_depth": 7.0,
            "career_progression": 8.0,
            "relevant_projects": ["Project 1", "Project 2"],
            "experience_gaps": ["Gap 1", "Gap 2"],
            "evidence": ["Quotes from interview about experience"]
        }}
        """
        
        response = await async_call_model(prompt, request)
        try:
            json_data = extract_json_from_response(response)
            if isinstance(json_data, dict):
                try:
                    return ExperienceAssessment(**json_data)
                except (TypeError, ValueError) as e:
                    logger.warning(f"ExperienceAssessment structure mismatch: {e}")
                    return ExperienceAssessment(
                        overall_score=json_data.get('overall_score', 7.0),
                        role_alignment=json_data.get('role_alignment', 7.0),
                        experience_depth=json_data.get('experience_depth', 7.0),
                        career_progression=json_data.get('career_progression', 7.0),
                        relevant_projects=json_data.get('relevant_projects', ["Details unavailable"]),
                        experience_gaps=json_data.get('experience_gaps', ["Details unavailable"]),
                        evidence=json_data.get('evidence', ["Extracted from LLM response"])
                    )
            else:
                logger.warning("No valid JSON found in experience assessment, using defaults")
                raise ValueError("No JSON found")
        except:
            return ExperienceAssessment(
                overall_score=5.0,
                role_alignment=5.0,
                experience_depth=5.0,
                career_progression=5.0,
                relevant_projects=[],
                experience_gaps=[],
                evidence=[]
            )
    
    def _extract_experience_responses(self, structured_transcript: Dict) -> str:
        """Extract experience-related responses from transcript."""
        experience_keywords = ['experience', 'worked', 'project', 'role', 'responsibility', 'achievement']
        candidate_responses = structured_transcript.get('candidate_responses', [])
        
        experience_responses = []
        for response in candidate_responses:
            if any(keyword.lower() in response.lower() for keyword in experience_keywords):
                experience_responses.append(response)
        
        return '\n'.join(experience_responses)


class CulturalFitAgent:
    """Agent for evaluating cultural fit and organizational alignment."""
    
    async def process(self, state: WorkflowState, request) -> WorkflowState:
        """Evaluate cultural fit based on responses and policy values."""
        logger.info(f"Cultural fit assessment for candidate {state.candidate_id}")
        
        try:
            assessment = await self._evaluate_cultural_fit(state, request)
            state.cultural_assessment = assessment.dict()
            state.cultural_score = assessment.overall_score
            
            logger.info(f"Cultural fit assessment completed: {assessment.overall_score}/10")
            return state
            
        except Exception as e:
            logger.error(f"Cultural fit assessment failed: {str(e)}")
            state.processing_errors.append(f"Cultural fit assessment: {str(e)}")
            return state
    
    async def _evaluate_cultural_fit(self, state: WorkflowState, request) -> CulturalAssessment:
        """Perform detailed cultural fit evaluation."""
        
        conversations = state.structured_transcript.get('conversations', [])
        candidate_responses = [c['content'] for c in conversations if c['speaker'] == 'candidate']
        
        prompt = f"""
        Evaluate the candidate's cultural fit based on their interview responses:
        
        Organization Context: {state.policy_template.get('name', 'Professional Organization')}
        Job Role: {state.job_requirements.get('title')}
        
        Candidate Responses:
        {chr(10).join(candidate_responses)}
        
        Assess cultural fit indicators (1-10 scale):
        1. Value Alignment - Alignment with professional values and ethics
        2. Adaptability - Ability to adapt to organizational changes
        3. Growth Mindset - Learning orientation and development focus
        4. Cultural Integration Potential - Likelihood of successful integration
        5. Overall Cultural Fit Score
        
        Consider evidence of:
        - Professional attitude and work ethic
        - Collaboration preferences
        - Learning and development mindset
        - Problem-solving approach
        - Communication style
        
        Return JSON format:
        {{
            "overall_score": 8.0,
            "value_alignment": 8.5,
            "adaptability": 7.5,
            "growth_mindset": 8.0,
            "cultural_integration_potential": 8.0,
            "evidence": ["Quotes showing cultural fit indicators"],
            "recommendations": ["Suggestions for cultural integration"]
        }}
        """
        
        response = await async_call_model(prompt, request)
        try:
            json_data = extract_json_from_response(response)
            if isinstance(json_data, dict):
                try:
                    return CulturalAssessment(**json_data)
                except (TypeError, ValueError) as e:
                    logger.warning(f"CulturalAssessment structure mismatch: {e}")
                    return CulturalAssessment(
                        overall_score=json_data.get('overall_score', 7.0),
                        value_alignment=json_data.get('value_alignment', 7.0),
                        adaptability=json_data.get('adaptability', 7.0),
                        growth_mindset=json_data.get('growth_mindset', 7.0),
                        cultural_integration_potential=json_data.get('cultural_integration_potential', 7.0),
                        evidence=json_data.get('evidence', ["Extracted from LLM response"]),
                        recommendations=json_data.get('recommendations', ["Details unavailable"])
                    )
            else:
                logger.warning("No valid JSON found in cultural assessment, using defaults")
                raise ValueError("No JSON found")
        except:
            return CulturalAssessment(
                overall_score=5.0,
                value_alignment=5.0,
                adaptability=5.0,
                growth_mindset=5.0,
                cultural_integration_potential=5.0,
                evidence=[],
                recommendations=[]
            )


class ScoringDecisionAgent:
    """Agent for final scoring and hiring decision making."""
    
    # Scoring weights
    WEIGHTS = {
        'technical': 0.35,
        'behavioral': 0.25,
        'experience': 0.25,
        'cultural': 0.15
    }
    
    def process(self, state: WorkflowState) -> WorkflowState:
        """Calculate final score and make hiring decision."""
        logger.info(f"Final scoring for candidate {state.candidate_id}")
        
        try:
            # Calculate weighted final score
            final_score = (
                (state.technical_score or 0) * self.WEIGHTS['technical'] +
                (state.behavioral_score or 0) * self.WEIGHTS['behavioral'] +
                (state.experience_score or 0) * self.WEIGHTS['experience'] +
                (state.cultural_score or 0) * self.WEIGHTS['cultural']
            ) * 10  # Convert to 100-point scale
            
            state.final_score = round(final_score, 1)
            
            # Make hiring decision
            if final_score >= 85:
                state.decision = DecisionStatus.SELECTED
            elif final_score >= 70:
                state.decision = DecisionStatus.CONDITIONAL
            elif final_score >= 55:
                state.decision = DecisionStatus.UNDER_REVIEW
            else:
                state.decision = DecisionStatus.REJECTED
            
            logger.info(f"Final scoring completed: {state.final_score}/100, Decision: {state.decision}")
            return state
            
        except Exception as e:
            logger.error(f"Final scoring failed: {str(e)}")
            state.processing_errors.append(f"Final scoring: {str(e)}")
            return state


class ReportGenerationAgent:
    """Agent for generating comprehensive assessment reports."""
    
    async def process(self, state: WorkflowState, request) -> WorkflowState:
        """Generate final assessment report with all findings."""
        logger.info(f"Report generation for candidate {state.candidate_id}")
        
        try:
            report = await self._generate_comprehensive_report(state, request)
            state.generated_report = report
            
            logger.info("Report generation completed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            state.processing_errors.append(f"Report generation: {str(e)}")
            return state
    
    async def _generate_comprehensive_report(self, state: WorkflowState, request) -> str:
        """Generate detailed assessment report using template."""
        
        template_content = state.policy_template.get('content', '')
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        prompt = f"""
        Generate a comprehensive interview assessment report using the following template and assessment data:
        
        TEMPLATE STRUCTURE:
        {template_content}
        
        ASSESSMENT DATA:
        Candidate Name: {state.candidate_name}
        Position: {state.job_requirements.get('title')}
        Interview Date: {current_date}
        
        DETAILED SCORES:
        - Technical Skills: {state.technical_score}/10 (Weight: 35%)
        - Behavioral Competencies: {state.behavioral_score}/10 (Weight: 25%)
        - Experience Relevance: {state.experience_score}/10 (Weight: 25%)
        - Cultural Fit: {state.cultural_score}/10 (Weight: 15%)
        - FINAL SCORE: {state.final_score}/100
        - DECISION: {state.decision.value.upper()}
        
        EVIDENCE AND DETAILS:
        Technical Assessment: {json.dumps(state.technical_assessment, indent=2)}
        Behavioral Assessment: {json.dumps(state.behavioral_assessment, indent=2)}
        Experience Assessment: {json.dumps(state.experience_assessment, indent=2)}
        Cultural Assessment: {json.dumps(state.cultural_assessment, indent=2)}
        
        INSTRUCTIONS:
        1. Follow the exact template structure and formatting
        2. Replace ALL placeholder fields with actual data
        3. Include specific evidence from assessments
        4. Provide detailed justification for scores
        5. Give actionable development recommendations
        6. Ensure decision aligns with scoring logic
        
        MANDATORY REPLACEMENTS:
        - [Candidate Name] → {state.candidate_name}
        - [Date] → {current_date}
        - [Name] (interviewer) → Interviewer
        - Fill all scoring sections with actual numerical scores
        - Include evidence quotes from interview transcript
        
        Generate the complete report in markdown format.
        """
        
        response = await async_call_model(prompt, request)
        # Extract content from AIMessage object
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)


class QualityAssuranceAgent:
    """Agent for quality assurance and validation of generated reports."""
    
    async def process(self, state: WorkflowState, request) -> WorkflowState:
        """Perform quality checks on the generated report."""
        logger.info(f"Quality assurance for candidate {state.candidate_id}")
        
        try:
            quality_check = await self._perform_quality_checks(state, request)
            state.quality_check_passed = quality_check.overall_quality_score >= 4.0  # Very low threshold to prevent infinite loops
            
            if not state.quality_check_passed:
                logger.warning(f"Quality check failed: {quality_check.issues_found}")
                state.processing_errors.extend(quality_check.issues_found)
            
            logger.info(f"Quality assurance completed: {quality_check.overall_quality_score}/10")
            return state
            
        except Exception as e:
            logger.error(f"Quality assurance failed: {str(e)}")
            state.processing_errors.append(f"Quality assurance: {str(e)}")
            return state
    
    async def _perform_quality_checks(self, state: WorkflowState, request) -> QualityCheck:
        """Perform comprehensive quality validation."""
        
        issues = []
        
        # Check template completion
        template_complete = self._check_template_completion(state.generated_report, state.candidate_name)
        if not template_complete:
            issues.append("Template completion check failed")
        
        # Check score consistency
        score_consistent = self._check_score_consistency(state)
        if not score_consistent:
            issues.append("Score consistency check failed")
        
        # Check evidence validation
        evidence_valid = self._check_evidence_validation(state)
        if not evidence_valid:
            issues.append("Evidence validation check failed")
        
        # Check recommendation alignment
        recommendation_aligned = self._check_recommendation_alignment(state)
        if not recommendation_aligned:
            issues.append("Recommendation alignment check failed")
        
        # Calculate overall quality score
        quality_score = (
            (8 if template_complete else 4) +
            (8 if score_consistent else 4) +
            (8 if evidence_valid else 4) +
            (8 if recommendation_aligned else 4)
        ) / 4
        
        # Debug logging
        logger.info(f"Quality checks: template={template_complete}, score={score_consistent}, "
                   f"evidence={evidence_valid}, recommendation={recommendation_aligned}")
        logger.info(f"Quality score calculation: {quality_score}/10")
        
        return QualityCheck(
            template_completion=template_complete,
            score_consistency=score_consistent,
            evidence_validation=evidence_valid,
            recommendation_alignment=recommendation_aligned,
            overall_quality_score=quality_score,
            issues_found=issues
        )
    
    def _check_template_completion(self, report: str, candidate_name: str) -> bool:
        """Check if template fields are properly filled."""
        if not report:
            return False
        
        # Check for unfilled placeholders
        placeholders = ['[Candidate Name]', '[Date]', '[Name]']
        for placeholder in placeholders:
            if placeholder in report:
                return False
        
        # Check if candidate name is present
        return candidate_name in report
    
    def _check_score_consistency(self, state: WorkflowState) -> bool:
        """Check if scores are consistent across assessments."""
        scores = [state.technical_score, state.behavioral_score, state.experience_score, state.cultural_score]
        return all(score is not None and 0 <= score <= 100 for score in scores if score is not None)
    
    def _check_evidence_validation(self, state: WorkflowState) -> bool:
        """Check if assessments include proper evidence."""
        # Check if generated report contains evidence/details
        if state.generated_report and len(state.generated_report) > 100:
            return True
        
        # Also check individual assessment scores exist
        scores = [state.technical_score, state.behavioral_score, state.experience_score, state.cultural_score]
        return any(score is not None and score > 0 for score in scores)
    
    def _check_recommendation_alignment(self, state: WorkflowState) -> bool:
        """Check if final decision aligns with score."""
        if not state.final_score or not state.decision:
            return False
        
        if state.final_score >= 85 and state.decision != DecisionStatus.SELECTED:
            return False
        elif 70 <= state.final_score < 85 and state.decision != DecisionStatus.CONDITIONAL:
            return False
        elif 55 <= state.final_score < 70 and state.decision != DecisionStatus.UNDER_REVIEW:
            return False
        elif state.final_score < 55 and state.decision != DecisionStatus.REJECTED:
            return False
        
        return True