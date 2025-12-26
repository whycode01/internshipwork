"""
LangGraph Question Generation Workflow for Studio Visualization
==============================================================

This is the optimized workflow for LangGraph Studio integration.
Clean, focused implementation with embedded policies and proper tracing.
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

# LangGraph imports
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import Annotated

# LangSmith tracing
try:
    from langsmith.run_helpers import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    def traceable(name=None):
        def decorator(func):
            return func
        return decorator
    LANGSMITH_AVAILABLE = False

# LLM imports (will be imported dynamically in the call_llm_node)
# from langchain_groq import ChatGroq
# from langchain_openai import ChatOpenAI


# --- State Definition ---
class WorkflowState(TypedDict):
    """State that flows through the LangGraph workflow"""
    # Input parameters (configurable in Studio)
    job_id: Optional[int]
    candidate_id: Optional[int] 
    policy_id: Optional[str]
    role_index: Optional[int]  # For cycling through multiple roles
    
    # Data fields
    job: Optional[Dict[str, Any]]
    candidate: Optional[Dict[str, Any]]
    policies: Optional[str]
    selected_role: Optional[str]  # Currently selected job role
    available_roles: Optional[List[Dict[str, Any]]]  # All available roles
    
    # Processing fields
    prompt: Optional[str]
    llm_response: Optional[str]
    questions_data: Optional[List[Dict]]
    validation_result: Optional[Dict[str, Any]]
    
    # Output fields
    questions_file_path: Optional[str]
    questions_count: Optional[int]
    
    # Control fields
    current_step: Optional[str]
    error_message: Optional[str]
    retry_count: Optional[int]
    max_retries: Optional[int]
    
    # Messages for Studio visualization
    messages: Annotated[List[Dict], add_messages]


# --- Policy Loading ---
def load_policies_simple(specific_policy_id: Optional[str] = None) -> str:
    """Load company policies dynamically for question generation"""
    try:
        # Try multiple sources for policies
        config_files = ['langgraph.dev.json', 'langgraph.json']
        config_policies = []
        
        # 1. Try loading from LangGraph config files
        for config_path in config_files:
            if os.path.exists(config_path):
                print(f"🔍 Checking config file: {config_path}")
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    policies = config_data.get('config', {}).get('policies', [])
                    if policies:
                        config_policies = policies
                        print(f"✅ Found {len(config_policies)} policies in {config_path}")
                        break
        
        # 2. Try loading from database if config files don't have policies
        if not config_policies:
            try:
                import sys

                # Add parent directory to path to import sql_ops
                current_dir = os.path.dirname(os.path.abspath(__file__))
                parent_dir = os.path.dirname(current_dir)
                sys.path.insert(0, parent_dir)
                
                from sql_ops import get_all_policies, get_policy_by_id
                
                if specific_policy_id:
                    policy_data = get_policy_by_id(specific_policy_id)
                    if policy_data:
                        config_policies = [policy_data]
                        print(f"✅ Loaded specific policy from database: {policy_data.get('name', 'Unknown')}")
                else:
                    config_policies = get_all_policies()
                    print(f"✅ Loaded {len(config_policies)} policies from database")
                    
            except ImportError:
                print("⚠️ sql_ops not available for database policy loading")
            except Exception as e:
                print(f"⚠️ Database policy loading failed: {e}")
        
        # 3. Process loaded policies
        if config_policies:
            if specific_policy_id:
                for policy in config_policies:
                    if policy.get('id') == specific_policy_id:
                        content = f"**Policy: {policy.get('name')}**\n{policy.get('content', '')}"
                        print(f"📋 Using specific policy: {policy.get('name')} ({specific_policy_id})")
                        return content
            
            # Return all policies dynamically
            policies_text = []
            for policy in config_policies:
                policy_name = policy.get('name', f'Policy_{policy.get("id", "Unknown")}')
                policy_content = policy.get('content', policy.get('description', ''))
                if policy_content:  # Only add policies with actual content
                    policies_text.append(f"**Policy: {policy_name}**\n{policy_content}")
                    print(f"📋 Added policy: {policy_name}")
            
            if policies_text:
                result = "\n\n".join(policies_text)
                print(f"📋 Dynamically loaded {len(config_policies)} policies ({len(result)} chars total)")
                return result
        
        # 4. Try loading from files in policies directory
        policies_dir = os.path.join(os.path.dirname(__file__), '..', 'storage', 'policies')
        if os.path.exists(policies_dir):
            policy_files = [f for f in os.listdir(policies_dir) if f.endswith('.json')]
            if policy_files:
                policies_text = []
                for file in policy_files:
                    file_path = os.path.join(policies_dir, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            policy_data = json.load(f)
                            policy_name = policy_data.get('name', file.replace('.json', ''))
                            policy_content = policy_data.get('content', policy_data.get('description', ''))
                            if policy_content:
                                policies_text.append(f"**Policy: {policy_name}**\n{policy_content}")
                                print(f"📋 Loaded policy from file: {policy_name}")
                    except Exception as e:
                        print(f"⚠️ Failed to load policy file {file}: {e}")
                
                if policies_text:
                    result = "\n\n".join(policies_text)
                    print(f"📋 Loaded {len(policy_files)} policies from files ({len(result)} chars total)")
                    return result
        
        # 5. No policies found anywhere
        print("❌ No policies found in any source (config files, database, or policy files)")
        return ""
        
    except Exception as e:
        print(f"❌ Error loading policies: {e}")
        return ""


# --- Dynamic Data Fetching Functions ---
def extract_all_job_roles(policies: str) -> List[Dict[str, Any]]:
    """
    Extract all available job roles from policies content
    Returns list of all job roles found in policies
    """
    import re
    
    job_roles = []
    
    if not policies:
        return job_roles
    
    # Look for common job title patterns in policies
    title_patterns = [
        r'(?i)(corporate finance analyst|finance analyst)',
        r'(?i)(marketing manager|marketing)',
        r'(?i)(software engineer|developer)',
        r'(?i)(data scientist)',
        r'(?i)(product manager)',
        r'(?i)(business analyst)',
        r'(?i)(project manager)'
    ]
    
    print(f"🔍 Extracting all job roles from policies ({len(policies)} chars)")
    
    for pattern in title_patterns:
        match = re.search(pattern, policies)
        if match:
            job_name = match.group(1).title()
            
            # Extract role-specific content from policies
            role_content = ""
            policy_sections = policies.split("**Policy:")
            for section in policy_sections:
                if job_name.lower() in section.lower():
                    role_content = section
                    break
            
            job_roles.append({
                "name": job_name,
                "content": role_content,
                "pattern": pattern
            })
            print(f"✅ Found job role: {job_name}")
    
    print(f"📋 Total job roles extracted: {len(job_roles)}")
    return job_roles

def fetch_job_data(job_id: int, policies: str, selected_role: str = None) -> Dict[str, Any]:
    """
    Fetch job data dynamically based on policies content and selected role
    Returns dynamic job information for question generation
    """
    print(f"🔍 Fetching job data for job_id: {job_id}, selected_role: {selected_role}")
    
    try:
        # Try to import database operations (non-blocking approach)
        try:
            # Add parent directory to path to import sql_ops
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            
            from sql_ops import get_job_by_id
            job_data = get_job_by_id(job_id)
            if job_data:
                print(f"🎯 Fetched job from database: {job_data.get('name', 'Unknown')}")
                return job_data
        except ImportError:
            print("⚠️ sql_ops not available, using policy-based detection")
        except Exception as e:
            print(f"⚠️ Database fetch failed: {e}, using policy-based detection")
        
        # Extract all available job roles
        available_roles = extract_all_job_roles(policies)
        
        # If no specific role selected, let user choose or use all roles
        if not selected_role and available_roles:
            # For demo, we'll cycle through all roles or use first one
            selected_role = available_roles[0]["name"]
            print(f"🎯 Auto-selecting first available role: {selected_role}")
            print(f"📋 Available roles: {[role['name'] for role in available_roles]}")
        elif not selected_role:
            selected_role = "Software Engineer"
            print(f"🎯 Using default role: {selected_role}")
        
        # Find the selected role's content
        job_name = selected_role
        job_description = "We are looking for an experienced professional to join our team."
        job_requirements = []
        role_content = ""
        
        # Get content for selected role
        for role in available_roles:
            if role["name"].lower() == selected_role.lower():
                role_content = role["content"]
                job_name = role["name"]
                break
        
        # Dynamic extraction from policies
        if policies:
            import re

            # Extract requirements dynamically from policy content
            requirement_indicators = [
                'must have', 'required', 'essential', 'mandatory', 
                'should have', 'experience in', 'knowledge of', 'skills in'
            ]
            
            for indicator in requirement_indicators:
                pattern = rf'(?i){indicator}[:\s]+([^\.]+)'
                matches = re.findall(pattern, policies)
                job_requirements.extend([match.strip() for match in matches])
            
            # Create dynamic job description based on policy content
            if 'finance' in job_name.lower():
                job_description = "Dynamic finance role requiring analytical skills and financial expertise as defined by company policies."
            elif 'marketing' in job_name.lower():
                job_description = "Dynamic marketing role focusing on strategy and campaign management as outlined in company policies."
            elif 'software' in job_name.lower():
                job_description = "Dynamic software engineering role requiring technical skills as specified in company policies."
            else:
                job_description = f"Dynamic {job_name} role based on company policy requirements."
        
        # Create dynamic job object with all available roles
        return {
            "id": job_id,
            "name": job_name,
            "description": job_description,
            "requirements": job_requirements[:5],  # Top 5 requirements
            "policy_based": True,
            "available_roles": available_roles,  # Include all available roles
            "selected_role": selected_role,
            "aspects": [
                {"name": "Core Skills", "focusAreas": ["Domain Expertise", "Policy Compliance"]},
                {"name": "Experience", "focusAreas": ["Industry Knowledge", "Relevant Background"]}
            ]
        }
        
    except Exception as e:
        print(f"❌ Job data fetch failed: {e}")
        # Minimal fallback
        return {
            "id": job_id,
            "name": "Position",
            "description": "Role based on company policies",
            "requirements": [],
            "policy_based": True,
            "aspects": []
        }


def fetch_candidate_data(candidate_id: int) -> Dict[str, Any]:
    """Fetch candidate data dynamically from database or API"""
    try:
        # Try to import database operations (non-blocking approach)
        try:
            # Add parent directory to path to import sql_ops
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            
            from sql_ops import get_candidate_by_id
            candidate_data = get_candidate_by_id(candidate_id)
            if candidate_data:
                print(f"👤 Fetched candidate from database: {candidate_data.get('name', 'Unknown')}")
                return candidate_data
        except ImportError:
            print("⚠️ sql_ops not available, using dynamic generation")
        except Exception as e:
            print(f"⚠️ Database fetch failed: {e}, using dynamic generation")
        
        # Dynamic candidate generation based on ID
        candidate_names = [
            "Alex Johnson", "Sarah Chen", "Michael Rodriguez", "Emily Wang", 
            "David Kim", "Jessica Thompson", "Ryan Patel", "Maria Garcia",
            "James Wilson", "Lisa Zhang", "Carlos Martinez", "Anna Lee"
        ]
        
        # Use candidate_id to select name (modulo for cycling)
        name = candidate_names[candidate_id % len(candidate_names)]
        
        return {
            "id": candidate_id,
            "name": name,
            "dynamic_generation": True,
            "aspects": [
                {"name": "Experience", "focusAreas": ["Professional Background", "Industry Knowledge"]},
                {"name": "Education", "focusAreas": ["Relevant Degree", "Certifications"]},
                {"name": "Skills", "focusAreas": ["Technical Skills", "Soft Skills"]}
            ]
        }
        
    except Exception as e:
        print(f"❌ Candidate data fetch failed: {e}")
        # Minimal fallback
        return {
            "id": candidate_id,
            "name": f"Candidate {candidate_id}",
            "dynamic_generation": True,
            "aspects": []
        }


# --- Workflow Nodes ---
@traceable(name="gather_data")
def gather_data_node(state: WorkflowState) -> WorkflowState:
    """Gather data for question generation - Fully Dynamic"""
    print("🔍 [Node 1] Gathering Data Dynamically...")
    
    try:
        # Get IDs from state
        job_id = state.get('job_id', 1)
        candidate_id = state.get('candidate_id', 1) 
        policy_id = state.get('policy_id')
        
        # Load policies dynamically
        policies = load_policies_simple(policy_id)
        print(f"📋 Loaded policies: {len(policies)} characters")
        
        # First, extract all available job roles
        available_roles = extract_all_job_roles(policies)
        print(f"🎯 Available job roles: {[role['name'] for role in available_roles]}")
        
        # For demo purposes, we'll cycle through all roles or let user choose
        # In a real implementation, this would be a user input or parameter
        selected_role = None
        if available_roles:
            if len(available_roles) == 1:
                selected_role = available_roles[0]["name"]
                print(f"📋 Single role detected, auto-selecting: {selected_role}")
            else:
                # For demo: Use state to determine which role, or cycle through them
                role_index = state.get('role_index', 0) % len(available_roles)
                selected_role = available_roles[role_index]["name"]
                print(f"🔄 Multiple roles available, using role {role_index + 1}/{len(available_roles)}: {selected_role}")
                print(f"💡 All available roles: {[role['name'] for role in available_roles]}")
        
        # Fetch job data dynamically from database/API with selected role
        job = fetch_job_data(job_id, policies, selected_role)
        
        # Fetch candidate data dynamically from database/API  
        candidate = fetch_candidate_data(candidate_id)
        
        print(f"✅ Data gathered dynamically - Job: {job.get('name', 'Unknown')}, Candidate: {candidate.get('name', 'Unknown')}")
        
        return {
            **state,
            'job': job,
            'candidate': candidate,
            'policies': policies,
            'selected_role': selected_role,
            'available_roles': available_roles,
            'current_step': 'data_gathered',
            'retry_count': 0,
            'max_retries': 2,
            'messages': state.get('messages', []) + [
                {'role': 'assistant', 'content': f"Gathered data dynamically for {job.get('name', 'position')} (Selected role: {selected_role})"}
            ]
        }
        
    except Exception as e:
        print(f"❌ Gather data failed: {e}")
        return {
            **state,
            'error_message': f"Data gathering failed: {e}",
            'current_step': 'error'
        }


@traceable(name="build_prompt")
def build_prompt_node(state: WorkflowState) -> WorkflowState:
    """Build dynamic prompt for LLM based on actual data"""
    print("📝 [Node 2] Building Dynamic Prompt...")
    
    try:
        job = state.get('job', {})
        candidate = state.get('candidate', {})
        policies = state.get('policies', '')
        
        # Validate we have actual data
        if not policies:
            return {
                **state,
                'error_message': "No policies available for dynamic prompt generation",
                'current_step': 'error'
            }
        
        # Debug: Show what policies are being used
        print(f"🔍 Building prompt with policies ({len(policies)} chars)")
        if policies:
            # Show first 200 chars of policies
            preview = policies[:200] + "..." if len(policies) > 200 else policies
            print(f"📋 Policy preview: {preview}")
        
        # Extract dynamic data
        job_name = job.get('name', 'Position')
        job_description = job.get('description', 'Role based on company policies')
        job_requirements = job.get('requirements', [])
        candidate_name = candidate.get('name', 'Candidate')
        
        # Build completely dynamic prompt based on actual data
        requirements_text = ""
        if job_requirements:
            requirements_text = f"\nSPECIFIC REQUIREMENTS:\n" + "\n".join([f"- {req}" for req in job_requirements])
        
        candidate_aspects = candidate.get('aspects', [])
        candidate_info = ""
        if candidate_aspects:
            candidate_info = f"\nCANDIDATE FOCUS AREAS:\n"
            for aspect in candidate_aspects:
                focus_areas = aspect.get('focusAreas', [])
                if focus_areas:
                    candidate_info += f"- {aspect.get('name', 'Area')}: {', '.join(focus_areas)}\n"
        
        prompt = f"""You are an expert HR interviewer conducting a dynamic interview assessment. Generate interview questions specifically for the {job_name} position based on the actual company policies and data provided below.

COMPANY POLICIES (DYNAMIC):
{policies}

JOB DETAILS (DYNAMIC):
- Position: {job_name}
- Description: {job_description}{requirements_text}
- Candidate: {candidate_name}{candidate_info}

DYNAMIC INSTRUCTIONS:
1. Analyze the provided company policies in detail - these are REAL policies, not examples
2. Generate 8-12 interview questions that directly test compliance with these specific policies
3. Focus on the exact competencies, scenarios, and requirements mentioned in the policies
4. Ensure questions are relevant to {job_name} and test both technical and behavioral aspects
5. Include situational questions that test the candidate's ability to handle policy-specific scenarios
6. Questions must be derived from the actual policy content provided above

OUTPUT FORMAT:
Return ONLY a valid JSON array with this exact structure:
[
  {{
    "question_text": "Your specific question derived from the policies",
    "question_type": "behavioral|technical|situational",
    "objective": "What specific policy requirement or competency this evaluates",
    "policy_reference": "Brief reference to which policy section this relates to"
  }}
]

CRITICAL REQUIREMENTS: 
- ALL questions must be derived from the actual policy content provided above
- Do NOT use generic questions - base everything on the specific policies
- Questions must be relevant to the {job_name} role as defined in the policies
- Test real scenarios and requirements mentioned in the policies
- Ensure JSON is properly formatted and valid
- Include policy_reference to show traceability to actual policy content"""

        print("✅ Dynamic prompt built successfully from actual data")
        print(f"🎯 Prompt includes {len(job_requirements)} specific requirements")
        print(f"👤 Prompt includes {len(candidate_aspects)} candidate focus areas")
        
        return {
            **state,
            'prompt': prompt,
            'current_step': 'prompt_built'
        }
        
    except Exception as e:
        print(f"❌ Dynamic prompt building failed: {e}")
        return {
            **state,
            'error_message': f"Dynamic prompt building failed: {e}",
            'current_step': 'error'
        }


@traceable(name="call_llm")
async def call_llm_node(state: WorkflowState) -> WorkflowState:
    """Call LLM for question generation"""
    print("🤖 [Node 3] Calling LLM...")
    
    try:
        # Get the prompt from state
        prompt = state.get('prompt', '')
        job = state.get('job', {})
        job_name = job.get('name', 'Software Engineer')
        policies = state.get('policies', '')
        
        print(f"🎯 Generating dynamic questions for: {job_name}")
        print(f"📝 Using prompt ({len(prompt)} chars)")
        print(f"📋 Based on policies ({len(policies)} chars)")
        
        # Load environment variables (non-blocking)
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            # Try loading from .env file
            env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
            if os.path.exists(env_path):
                try:
                    with open(env_path, 'r') as f:
                        for line in f:
                            if line.startswith('GROQ_API_KEY='):
                                groq_api_key = line.split('=', 1)[1].strip()
                                break
                except Exception as e:
                    print(f"⚠️ Could not read .env file: {e}")
        
        if not groq_api_key:
            return {
                **state,
                'error_message': "GROQ_API_KEY not found in environment variables or .env file",
                'current_step': 'retry_or_error'
            }
        
        # Use Groq with your specified model
        try:
            from langchain_groq import ChatGroq

            # Initialize Groq LLM with OpenAI compatible model
            llm = ChatGroq(
                model="openai/gpt-oss-20b",  # Using OpenAI GPT-OSS-20B model
                temperature=0.1,
                max_tokens=4000,
                api_key=groq_api_key
            )
            
            print("🔄 Calling Groq LLM with dynamic policy-based prompt...")
            
            # Call LLM with the constructed prompt
            response = await llm.ainvoke(prompt)
            llm_response = response.content
            
            print(f"✅ Groq LLM responded with {len(llm_response)} characters")
            print(f"📊 Generated content for {job_name} based on policies")
            
            # Clean up the response to ensure it's valid JSON
            # Sometimes LLMs add extra text before/after JSON
            try:
                # Find JSON array in the response
                import re
                json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
                if json_match:
                    llm_response = json_match.group(0)
                    print("✅ Extracted JSON from LLM response")
                else:
                    print("⚠️  No JSON array found in response, using full response")
            except Exception as e:
                print(f"⚠️  JSON extraction failed: {e}, using full response")
            
        except ImportError:
            print("❌ ChatGroq not available! Please install: pip install langchain-groq")
            return {
                **state,
                'error_message': "ChatGroq package not available. Install with: pip install langchain-groq",
                'current_step': 'retry_or_error'
            }
        except Exception as e:
            print(f"❌ Groq API call failed: {e}")
            if "API key" in str(e).lower():
                return {
                    **state,
                    'error_message': f"Groq API key issue: {e}",
                    'current_step': 'retry_or_error'
                }
            else:
                return {
                    **state,
                    'error_message': f"Groq LLM call failed: {e}",
                    'current_step': 'retry_or_error'
                }
        
        print(f"✅ Dynamic question generation completed for {job_name}")
        print(f"📈 Questions generated based on actual policy content")
        
        return {
            **state,
            'llm_response': llm_response,
            'current_step': 'llm_called'
        }
        
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        return {
            **state,
            'error_message': f"LLM call failed: {e}",
            'current_step': 'retry_or_error'
        }


@traceable(name="parse_response")
def parse_response_node(state: WorkflowState) -> WorkflowState:
    """Parse LLM response"""
    print("🔍 [Node 4] Parsing Response...")
    
    try:
        response = state.get('llm_response', '[]')
        questions_data = json.loads(response)
        
        print(f"✅ Parsed {len(questions_data)} questions")
        
        return {
            **state,
            'questions_data': questions_data,
            'current_step': 'response_parsed'
        }
        
    except Exception as e:
        print(f"❌ Parse failed: {e}")
        return {
            **state,
            'error_message': f"Response parsing failed: {e}",
            'current_step': 'retry_or_error'
        }


@traceable(name="validate_questions")
def validate_questions_node(state: WorkflowState) -> WorkflowState:
    """Validate generated questions"""
    print("✅ [Node 5] Validating Questions...")
    
    try:
        questions_data = state.get('questions_data', [])
        
        validation_result = {
            'is_valid': len(questions_data) >= 5,
            'errors': [],
            'warnings': []
        }
        
        if len(questions_data) == 0:
            validation_result['errors'].append("No questions generated")
        elif len(questions_data) < 5:
            validation_result['errors'].append(f"Too few questions: {len(questions_data)}")
        elif len(questions_data) < 8:
            validation_result['warnings'].append(f"Fewer than recommended: {len(questions_data)}")
        
        print(f"✅ Validation {'passed' if validation_result['is_valid'] else 'failed'}")
        
        return {
            **state,
            'validation_result': validation_result,
            'current_step': 'questions_validated' if validation_result['is_valid'] else 'validation_failed'
        }
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return {
            **state,
            'error_message': f"Validation failed: {e}",
            'current_step': 'error'
        }


@traceable(name="save_questions")
def save_questions_node(state: WorkflowState) -> WorkflowState:
    """Save generated questions dynamically"""
    print("💾 [Node 6] Saving Questions Dynamically...")
    
    try:
        questions_data = state.get('questions_data', [])
        candidate_id = state.get('candidate_id', 1)
        job_id = state.get('job_id', 1)
        job = state.get('job', {})
        candidate = state.get('candidate', {})
        
        # Create dynamic filename based on actual data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        job_name = job.get('name', 'Position').replace(' ', '_').lower()
        candidate_name = candidate.get('name', f'candidate_{candidate_id}').replace(' ', '_').lower()
        
        file_path = f"interview_questions_{job_name}_{candidate_name}_{timestamp}.json"
        
        # Try to save to actual storage location
        try:
            import os
            import sys

            # Add parent directory to path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            
            # Try to save to storage directory
            storage_dir = os.path.join(parent_dir, 'storage', 'questions')
            if not os.path.exists(storage_dir):
                os.makedirs(storage_dir, exist_ok=True)
            
            full_path = os.path.join(storage_dir, file_path)
            
            # Create comprehensive question data
            question_document = {
                "metadata": {
                    "job_id": job_id,
                    "candidate_id": candidate_id,
                    "job_name": job.get('name', 'Position'),
                    "candidate_name": candidate.get('name', f'Candidate {candidate_id}'),
                    "generated_at": datetime.now().isoformat(),
                    "question_count": len(questions_data),
                    "policy_based": job.get('policy_based', True)
                },
                "job_details": job,
                "candidate_details": candidate,
                "questions": questions_data
            }
            
            # Save to actual file
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(question_document, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Questions saved dynamically to: {full_path}")
            file_path = full_path  # Use full path for response
            
        except Exception as e:
            print(f"⚠️ Could not save to storage directory: {e}")
            print(f"✅ Questions would be saved to: {file_path}")
        
        # Try to save to database as well
        try:
            sys.path.insert(0, parent_dir)
            from sql_ops import save_interview_questions
            
            save_interview_questions({
                "job_id": job_id,
                "candidate_id": candidate_id,
                "questions": questions_data,
                "file_path": file_path,
                "metadata": {
                    "job_name": job.get('name'),
                    "candidate_name": candidate.get('name'),
                    "generated_dynamically": True
                }
            })
            print("✅ Questions also saved to database")
            
        except ImportError:
            print("⚠️ sql_ops not available for database saving")
        except Exception as e:
            print(f"⚠️ Database save failed: {e}")
        
        return {
            **state,
            'questions_file_path': file_path,
            'questions_count': len(questions_data),
            'current_step': 'completed',
            'messages': state.get('messages', []) + [
                {
                    'role': 'assistant',
                    'content': f"Successfully generated {len(questions_data)} dynamic interview questions for {job.get('name', 'position')}"
                }
            ]
        }
        
    except Exception as e:
        print(f"❌ Dynamic save failed: {e}")
        return {
            **state,
            'error_message': f"Dynamic save failed: {e}",
            'current_step': 'error'
        }


@traceable(name="retry")
def retry_node(state: WorkflowState) -> WorkflowState:
    """Handle retries"""
    retry_count = state.get('retry_count', 0)
    max_retries = state.get('max_retries', 2)
    
    print(f"🔄 [Node 7] Retry - Attempt {retry_count + 1}/{max_retries}")
    
    if retry_count < max_retries:
        return {
            **state,
            'retry_count': retry_count + 1,
            'current_step': 'retrying',
            'error_message': None
        }
    else:
        print(f"❌ Max retries exceeded")
        return {
            **state,
            'current_step': 'max_retries_exceeded'
        }


@traceable(name="error_handler")
def error_handler_node(state: WorkflowState) -> WorkflowState:
    """Handle errors"""
    error_msg = state.get('error_message', 'Unknown error')
    print(f"❌ [Node 8] Error Handler - {error_msg}")
    
    return {
        **state,
        'current_step': 'error_handled',
        'messages': state.get('messages', []) + [
            {'role': 'assistant', 'content': f"Workflow failed: {error_msg}"}
        ]
    }


# --- Routing Functions ---
def should_retry(state: WorkflowState) -> str:
    """Determine next step after potential retry scenarios"""
    current_step = state.get('current_step', '')
    
    if current_step == 'retry_or_error':
        retry_count = state.get('retry_count', 0)
        max_retries = state.get('max_retries', 2)
        if retry_count < max_retries:
            return "retry"
        else:
            return "error_handler"
    elif current_step in ['error', 'max_retries_exceeded']:
        return "error_handler"
    else:
        return END


def route_after_validation(state: WorkflowState) -> str:
    """Route after validation"""
    current_step = state.get('current_step', '')
    
    if current_step == 'questions_validated':
        return "save_questions"
    elif current_step == 'validation_failed':
        retry_count = state.get('retry_count', 0)
        max_retries = state.get('max_retries', 2)
        if retry_count < max_retries:
            return "retry"
        else:
            return "error_handler"
    elif current_step in ['retry_or_error', 'error']:
        retry_count = state.get('retry_count', 0)
        max_retries = state.get('max_retries', 2)
        if retry_count < max_retries:
            return "retry"
        else:
            return "error_handler"
    else:
        return "error_handler"


# --- Workflow Creation ---
def create_workflow() -> StateGraph:
    """Create the LangGraph workflow for Studio visualization"""
    
    # Create workflow
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("gather_data", gather_data_node)
    workflow.add_node("build_prompt", build_prompt_node)
    workflow.add_node("call_llm", call_llm_node)
    workflow.add_node("parse_response", parse_response_node)
    workflow.add_node("validate_questions", validate_questions_node)
    workflow.add_node("save_questions", save_questions_node)
    workflow.add_node("retry", retry_node)
    workflow.add_node("error_handler", error_handler_node)
    
    # Set entry point
    workflow.set_entry_point("gather_data")
    
    # Linear flow edges
    workflow.add_edge("gather_data", "build_prompt")
    workflow.add_edge("build_prompt", "call_llm")
    workflow.add_edge("call_llm", "parse_response")
    workflow.add_edge("parse_response", "validate_questions")
    
    # Conditional edges
    workflow.add_conditional_edges(
        "validate_questions",
        route_after_validation,
        {
            "save_questions": "save_questions",
            "retry": "retry",
            "error_handler": "error_handler"
        }
    )
    
    # Retry routing
    workflow.add_edge("retry", "call_llm")
    
    # Terminal edges
    workflow.add_edge("save_questions", END)
    workflow.add_edge("error_handler", END)
    
    return workflow.compile()


# --- Main Execution Function ---
@traceable(name="execute_workflow")
async def execute_question_generation_workflow_simple(
    job_id: int = 1,
    candidate_id: int = 1,
    job: Dict[str, Any] = None,
    candidate: Dict[str, Any] = None,
    request: Any = None,
    specific_policy_id: Optional[str] = None
) -> Dict[str, Any]:
    """Execute the question generation workflow"""
    
    try:
        print(f"🚀 Starting workflow for job {job_id}, candidate {candidate_id}")
        
        # Create workflow
        app = create_workflow()
        
        # Initial state
        initial_state = {
            'job_id': job_id,
            'candidate_id': candidate_id,
            'policy_id': specific_policy_id,
            'messages': []
        }
        
        # Execute workflow
        result_state = None
        async for state in app.astream(initial_state):
            result_state = state
            current_step = list(state.keys())[-1] if state else "unknown"
            print(f"📍 Current step: {current_step}")
        
        # Process results
        if result_state:
            final_state = list(result_state.values())[-1]
            
            if final_state.get('current_step') == 'completed':
                return {
                    "success": True,
                    "status": "completed",
                    "questions_file_path": final_state.get('questions_file_path'),
                    "questions_count": final_state.get('questions_count', 0),
                    "error_message": None
                }
            else:
                return {
                    "success": False,
                    "status": final_state.get('current_step', 'failed'),
                    "error_message": final_state.get('error_message', 'Workflow did not complete'),
                    "questions_count": 0
                }
        else:
            return {
                "success": False,
                "status": "no_result",
                "error_message": "No result state received",
                "questions_count": 0
            }
            
    except Exception as e:
        print(f"💥 Critical error: {e}")
        return {
            "success": False,
            "status": "critical_error",
            "error_message": str(e),
            "questions_count": 0
        }


async def run_workflow_for_all_roles(job_id: int = 1, candidate_id: int = 1, policy_id: str = None):
    """
    Demo function to run the workflow for all available job roles
    This shows how the dynamic role selection works
    """
    print("🎯 Running workflow for all available job roles...")
    
    try:
        # First, load policies to see available roles
        policies = load_policies_simple(policy_id)
        available_roles = extract_all_job_roles(policies)
        
        if not available_roles:
            print("⚠️ No job roles found in policies")
            return []
        
        print(f"📋 Found {len(available_roles)} job roles:")
        for i, role in enumerate(available_roles):
            print(f"  {i+1}. {role['name']}")
        
        results = []
        
        # Run workflow for each role
        for i, role in enumerate(available_roles):
            print(f"\n🔄 Running workflow for role {i+1}/{len(available_roles)}: {role['name']}")
            
            # Create workflow and compile it
            workflow = create_workflow()
            
            # Initial state with role selection
            initial_state = {
                'job_id': job_id,
                'candidate_id': candidate_id,
                'policy_id': policy_id,
                'role_index': i,  # Use role index to select specific role
                'messages': []
            }
            
            # Run the workflow
            result_state = await workflow.ainvoke(initial_state)
            
            success = result_state.get('questions_file_path') is not None
            
            result = {
                "success": success,
                "questions_count": result_state.get('questions_count', 0),
                "questions_file_path": result_state.get('questions_file_path'),
                "selected_role": result_state.get('selected_role'),
                "status": "completed" if success else "failed"
            }
            
            results.append({
                "role": role['name'],
                "role_index": i,
                "result": result
            })
            
            if result.get("success"):
                print(f"✅ Generated {result.get('questions_count', 0)} questions for {role['name']}")
                print(f"📄 File: {result.get('questions_file_path', 'N/A')}")
            else:
                print(f"❌ Failed to generate questions for {role['name']}")
        
        return results
        
    except Exception as e:
        print(f"💥 Error running workflow for all roles: {e}")
        return []


def demo_role_selection():
    """
    Synchronous demo function to show available roles
    """
    try:
        policies = load_policies_simple()
        available_roles = extract_all_job_roles(policies)
        
        if available_roles:
            print(f"\n📋 Available job roles in policies:")
            for i, role in enumerate(available_roles):
                print(f"  {i+1}. {role['name']}")
            
            print(f"\n💡 To run for different roles in LangGraph Studio:")
            print(f"   - Set 'role_index' parameter to 0-{len(available_roles)-1}")
            print(f"   - role_index=0 → {available_roles[0]['name']}")
            if len(available_roles) > 1:
                print(f"   - role_index=1 → {available_roles[1]['name']}")
            
            print(f"\n💡 To run programmatically for all roles:")
            print(f"   await run_workflow_for_all_roles()")
            
        else:
            print("⚠️ No job roles found in policies")
            
    except Exception as e:
        print(f"❌ Error in demo: {e}")


if __name__ == "__main__":
    print("🎯 LangGraph Question Generation Workflow")
    print("✅ Ready for Studio visualization")
    
    # Test workflow creation
    try:
        workflow = create_workflow()
        print("✅ Workflow compiled successfully")
        
        # Show available roles demo
        demo_role_selection()
        
    except Exception as e:
        print(f"❌ Workflow compilation failed: {e}")
