import asyncio
import json
import os
import re
import shutil
import sys
from datetime import datetime
from typing import Any, List, Optional, Set

import pandas as pd
from anony import anonymize, denonymize
from fastapi import (APIRouter, BackgroundTasks, File, Form, Query, Request,
                     UploadFile)
from langchain_community.document_loaders import PyPDFLoader
from prompts.job_prompts import (prompt1, prompt2, prompt3,
                                 report_comparison_prompt,
                                 report_generation_prompt)
from prompts.lab_review_prompts import (cross_questionnaire_prompt,
                                        questionnare_prompt)
from pydantic import BaseModel
from routers.config import settings_service
from sql_ops import create_candidate  # Job Descriptions; Job Candidates
from sql_ops import (create_job, delete_job_by_id, get_all_jobs,
                     get_candidate_by_id, get_candidate_for_assessment,
                     get_candidates_by_job_id, get_job_by_id, update_candidate,
                     update_candidate_assessment_scores, update_job_by_id)

# Add current directory to Python path for workflow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import LangGraph workflow
try:
    from langgraph_workflow.workflow import run_interview_assessment
    LANGGRAPH_ENABLED = False  # Temporarily disabled to avoid infinite loops
except ImportError as e:
    print(f"Warning: LangGraph workflow not available: {e}")
    LANGGRAPH_ENABLED = False

router = APIRouter(
    prefix="/api/jobs",
    tags=["Jobs"]
)

# --- Configuration ---
JOBS_STORAGE_DIR = 'storage/jobs'
POLICIES_DIR = 'storage/policies'
TEMPLATES_DIR = 'storage/templates'
os.makedirs(JOBS_STORAGE_DIR, exist_ok=True)
os.makedirs(POLICIES_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# --- Pydantic Models For API Data ---
class FocusArea(BaseModel):
    name: str

class Aspect(BaseModel):
    name: str
    focusAreas: List[str]

class Job(BaseModel):
    name: str
    description: str
    aspects: List[Aspect]

class QuestionGenerationRequest(BaseModel):
    policyId: Optional[str] = None

# --- Helper Functions ---
def load_policies(specific_policy_id: Optional[str] = None) -> str:
    """Load policies specifically for question generation (from policies directory only)."""
    policies_text = []
    
    try:
        # If a specific policy ID is provided, load only that policy
        if specific_policy_id:
            # Try to find the specific policy file in policies directory
            policy_file = os.path.join(POLICIES_DIR, f"{specific_policy_id}.json")
            if os.path.exists(policy_file):
                with open(policy_file, 'r', encoding='utf-8') as f:
                    policy_data = json.load(f)
                    return f"**Selected Policy: {policy_data.get('name', 'Unnamed')}**\n{policy_data.get('content', '')}"
            
            print(f"Specific policy {specific_policy_id} not found, loading all policies")
        
        # Load all policies for question generation
        if os.path.exists(POLICIES_DIR):
            for filename in os.listdir(POLICIES_DIR):
                if filename.endswith('.json'):
                    file_path = os.path.join(POLICIES_DIR, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        policy_data = json.load(f)
                        policies_text.append(f"**Policy: {policy_data.get('name', 'Unnamed')}**\n{policy_data.get('content', '')}")
    
    except Exception as e:
        print(f"Error loading policies: {e}")
        return "No policies available."
    
    if policies_text:
        return "\n\n".join(policies_text)
    else:
        return "No policies available."

def load_report_template(template_id: str) -> Optional[dict]:
    """Load a specific report template for report generation."""
    try:
        template_file = os.path.join(TEMPLATES_DIR, f"{template_id}.json")
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
                return template_data
        return None
    except Exception as e:
        print(f"Error loading report template: {e}")
        return None

def call_model(user_message):
    llm = settings_service.get_cached_llm()
    """Call the LLM model and get a response."""
    response = llm.invoke(user_message)
    return response

async def async_call_model(user_message, request: Request):
    """Asynchronous wrapper for calling the model."""
    # Run the model call in a separate thread to avoid blocking
    loop = asyncio.get_event_loop()
    executor = request.app.state.executor
    return await loop.run_in_executor(executor, call_model, user_message)

def sanitize_directory_name(name: str) -> str:
    """
    Sanitizes the name to create a valid directory name.
    Removes special characters and replaces spaces with underscores.
    """
    sanitized = re.sub(r'[^\w\s-]', '', name)
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    return sanitized.lower()

def create_job_directory(job_id: int, job_name: str) -> str:
    """Creates a directory for the job using job_id + safe_name and returns the path."""
    safe_name = sanitize_directory_name(job_name)
    job_dir_name = f"{job_id}_{safe_name}"
    job_dir = os.path.join(JOBS_STORAGE_DIR, job_dir_name)
    os.makedirs(job_dir, exist_ok=True)
    return job_dir

def get_job_directory_name(job_id: int, job: dict = None) -> str:
    """Get the job directory name using job_id."""
    if job is None:
        job = get_job_by_id(job_id)
    if not job:
        return None
    safe_name = sanitize_directory_name(job["name"])
    return f"{job_id}_{safe_name}"

def find_latest_candidate_file(job_id: int, candidate_id: int, prefix: str, ext: str) -> Optional[str]:
    job = get_job_by_id(job_id)
    job_dir_name = get_job_directory_name(job_id, job)
    if not job_dir_name:
        return None
    job_dir = os.path.join(JOBS_STORAGE_DIR, job_dir_name)
    if not os.path.exists(job_dir):
        return None
    # If ext is empty string, match all files with the prefix and candidate_id
    if ext:
        files = [f for f in os.listdir(job_dir) if f.startswith(f"{prefix}_{candidate_id}_") and f.endswith(ext)]
    else:
        files = [f for f in os.listdir(job_dir) if f.startswith(f"{prefix}_{candidate_id}_")]
    if not files:
        return None
    return os.path.join(job_dir, max(files, key=lambda x: x))

def jobs_save_resume(file_content: bytes | str, job_id: int, candidate_id: str, filename: str) -> str:
    """
    Saves a resume file to the job's directory and returns the relative path.
    
    Args:
        file_content: Either bytes or string content to save
        job_id: ID of the job
        candidate_id: ID of the candidate
        filename: Name of the file to save
    
    Returns:
        str: Relative path to the saved file
    """
    job = get_job_by_id(job_id)
    job_dir_name = get_job_directory_name(job_id, job)
    if not job_dir_name:
        raise Exception("Job not found")
    
    job_dir = os.path.join(JOBS_STORAGE_DIR, job_dir_name)
    os.makedirs(job_dir, exist_ok=True)
    
    abs_path = os.path.join(job_dir, filename)
    
    # Create the relative path
    rel_path = os.path.join(job_dir_name, filename)
    
    # Handle both string and bytes content
    mode = 'wb' if isinstance(file_content, bytes) else 'w'
    with open(abs_path, mode) as f:
        f.write(file_content)
    
    return rel_path

def resume_to_str(resume_path:Optional[str]) -> Optional[str]:
    if not resume_path:
        return None
    try:
        abs_path = os.path.join(JOBS_STORAGE_DIR, resume_path)
        loader = PyPDFLoader(abs_path)
        pages = loader.load()
        text = "\n".join([page.page_content for page in pages])
        return text
    except Exception as e:
        print(f"Error in resume_to_str: {e}")
        return None

def aspects_to_str(aspects:list) -> Optional[str]:
    if not aspects:
        return None
    lines = []
    for aspect in aspects:
        aspect_name = aspect.get("name") if isinstance(aspect, dict) else getattr(aspect, "name", "")
        focus_areas = aspect.get("focusAreas") if isinstance(aspect, dict) else getattr(aspect, "focusAreas", [])
        if not focus_areas:
            lines.append(f"- {aspect_name}")
        else:
            for fa in focus_areas:
                lines.append(f"- {fa} ({aspect_name})")
    return "\n".join(lines)

def first_questions_prompt(job:dict[str, Any], aspects:Optional[list]=None, resume:Optional[str]=None, policies:Optional[str]=None) -> str:
    resume_str = resume_to_str(resume) if (resume and isinstance(resume, str)) else "N/A"
    aspect_str = aspects_to_str(aspects) if (not resume_str and aspects) else "N/A"
    policies_str = policies if policies else "N/A"
    
    job_title = job['name']
    job_description = job['description']
    job_aspect_str = aspects_to_str(job['aspects'])
    
    # For question generation, always use policy-enhanced prompt (no template-specific prompts)
    print("DEBUG: Using policy-enhanced prompt for question generation")
    from prompts.job_prompts import prompt1_with_policies
    prompt = prompt1_with_policies.format(
        job_title=job_title, 
        job_description=job_description, 
        job_aspect_str=job_aspect_str, 
        resume_str=resume_str, 
        aspect_str=aspect_str,
        policies_str=policies_str
    )

    return prompt

async def generate_first_questions(job_id:int, candidate_id:int, job:dict, candidate:dict, request: Request, specific_policy_id: Optional[str] = None):
    """
    Generate interview questions using LangGraph workflow with LangSmith tracing.
    
    This function uses our clean LangSmith integration for full workflow visibility
    and provides better error handling, validation, and extensibility.
    """
    try:
        print("🚀 Starting LangGraph-based question generation with LangSmith tracing")
        
        # Try the clean LangSmith integration workflow
        try:
            from workflows.langsmith_integration import \
                execute_workflow_with_tracing
            print("✅ Successfully imported clean LangSmith integration")
            
            # Execute the workflow with full LangSmith tracing
            result = await execute_workflow_with_tracing(
                candidate_id=candidate_id,
                job_id=job_id
            )
            
            print(f"📊 Workflow trace available at: {result.get('trace_url', 'N/A')}")
            
            # If LangSmith workflow succeeds, use the simple workflow for actual execution
            if result["status"] == "success":
                from workflows.simple_workflow import \
                    execute_question_generation_workflow_simple
                workflow_result = await execute_question_generation_workflow_simple(
                    job_id=job_id,
                    candidate_id=candidate_id,
                    job=job,
                    candidate=candidate,
                    request=request,
                    specific_policy_id=specific_policy_id
                )
                result["workflow_details"] = workflow_result
            
            # Log results
            if result["success"]:
                print(f"Simplified LangGraph workflow completed successfully for candidate {candidate_id}")
                print(f"Generated {result['questions_count']} questions")
                if result.get('retry_count', 0) > 0:
                    print(f"Workflow succeeded after {result['retry_count']} retries")
                return  # Success, exit early
            else:
                print(f"Simplified LangGraph workflow failed for candidate {candidate_id}")
                print(f"Error: {result.get('error_message', 'Unknown error')}")
                # Fall through to try full workflow or fallback
                
        except ImportError as import_error:
            print(f"DEBUG: Failed to import simplified workflow: {import_error}")
        
        # Try the full LangGraph workflow as backup
        try:
            from workflows.question_generation_workflow import \
                execute_question_generation_workflow
            print("DEBUG: Successfully imported full LangGraph workflow")
            
            # Execute the full LangGraph workflow
            result = await execute_question_generation_workflow(
                job_id=job_id,
                candidate_id=candidate_id,
                job=job,
                candidate=candidate,
                request=request,
                specific_policy_id=specific_policy_id
            )
            
            # Log results
            if result["success"]:
                print(f"Full LangGraph workflow completed successfully for candidate {candidate_id}")
                print(f"Generated {result['questions_count']} questions")
                if result.get('retry_count', 0) > 0:
                    print(f"Workflow succeeded after {result['retry_count']} retries")
                return  # Success, exit early
            else:
                print(f"Full LangGraph workflow failed for candidate {candidate_id}")
                print(f"Error: {result.get('error_message', 'Unknown error')}")
                if result.get('retry_count', 0) > 0:
                    print(f"Failed after {result['retry_count']} retry attempts")
                    
        except ImportError as import_error:
            print(f"DEBUG: Failed to import full LangGraph workflow: {import_error}")

        # Both workflows failed, fall back to original method
        print("DEBUG: Both LangGraph workflows failed, falling back to original method")
        await generate_first_questions_fallback(job_id, candidate_id, job, candidate, request, specific_policy_id)
                
    except Exception as e:
        print(f"Critical error in LangGraph question generation: {str(e)}")
        update_candidate(job_id, candidate_id, status="Questions Error")
        
        # Fallback to original method if LangGraph fails
        print("DEBUG: Falling back to original question generation method due to critical error")
        await generate_first_questions_fallback(job_id, candidate_id, job, candidate, request, specific_policy_id)


async def generate_first_questions_fallback(job_id:int, candidate_id:int, job:dict, candidate:dict, request: Request, specific_policy_id: Optional[str] = None):
    """
    Fallback method for question generation using the original approach.
    
    This method is used if the LangGraph workflow fails for any reason,
    ensuring system reliability and backward compatibility.
    """
    try:
        print("DEBUG: Using fallback question generation method")
        
        # Load company policies for question generation (specific policy if provided)
        policies = load_policies(specific_policy_id)
        
        print("DEBUG: Generating questions with policy-enhanced prompt (fallback)")
        # Use policy-enhanced prompt for question generation
        prompt = first_questions_prompt(job, candidate['aspects'], candidate['resume'], policies)
        
        # Call LLM
        response = await async_call_model(prompt, request)
        content = extract_response_content(response)
        
        # Parse JSON Response
        questions_data = parse_json_response(content)
        
        print(f"DEBUG: Generated {len(questions_data)} questions with policies (fallback)")

        # Convert To CSV
        df = pd.DataFrame(questions_data)
        
        # Save Questions To File
        questions_filename = f"interview_questions_{candidate_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        job_dir_name = get_job_directory_name(job_id, job)
        questions_path = os.path.join(job_dir_name, questions_filename)
        
        # Save File
        abs_path = os.path.join(JOBS_STORAGE_DIR, questions_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        df.to_csv(abs_path, index=False)
        
        # Update Candidate Status
        update_candidate(job_id, candidate_id, status="Generated Questions")
        
        print(f"Interview questions generated successfully for candidate {candidate_id} (fallback)")
    except Exception as e:
        update_candidate(job_id, candidate_id, status="Questions Error")
        print(f"Error in fallback question generation: {str(e)}")

def extract_response_content(response):
    """Extract content from LLM response"""
    if hasattr(response, 'content'):
        return response.content
    elif isinstance(response, dict) and 'content' in response:
        return response['content']
    elif isinstance(response, str):
        return response
    else:
        return str(response)

def parse_json_response(content):
    """Parse JSON response with cleanup"""
    try:
        # Clean the content before parsing
        content_cleaned = content.strip()
        
        # Try to extract JSON if it's wrapped in extra text
        if '```json' in content_cleaned:
            # Extract JSON from markdown code blocks
            start = content_cleaned.find('```json') + 7
            end = content_cleaned.find('```', start)
            if end != -1:
                content_cleaned = content_cleaned[start:end].strip()
        elif content_cleaned.startswith('```') and content_cleaned.endswith('```'):
            # Remove code block markers
            content_cleaned = content_cleaned[3:-3].strip()
        
        # Try to find JSON array markers
        if not content_cleaned.startswith('['):
            start_idx = content_cleaned.find('[')
            if start_idx != -1:
                content_cleaned = content_cleaned[start_idx:]
        
        if not content_cleaned.endswith(']'):
            end_idx = content_cleaned.rfind(']')
            if end_idx != -1:
                content_cleaned = content_cleaned[:end_idx + 1]
        
        questions_data = json.loads(content_cleaned)
        print(f"Successfully parsed {len(questions_data)} questions")
        return questions_data
        
    except json.JSONDecodeError as e:
        print(f"Could not parse LLM response as JSON: {e}")
        print(f"Raw response length: {len(content)}")
        print(f"Response preview: {content[:500]}...")
        print(f"Response ending: ...{content[-200:]}")
        raise Exception(f"Could not parse LLM response as JSON: {e}")
    except Exception as e:
        print(f"Unexpected error parsing response: {e}")
        print(f"Response content: {content}")
        raise Exception(f"Unexpected error parsing response: {e}")

def first_questions_prompt_general(job:dict[str, Any], aspects:Optional[list]=None, resume:Optional[str]=None, policies:Optional[str]=None) -> str:
    """General prompt that always works"""
    resume_str = resume_to_str(resume) if (resume and isinstance(resume, str)) else "N/A"
    aspect_str = aspects_to_str(aspects) if (not resume_str and aspects) else "N/A"
    policies_str = policies if policies else "N/A"
    
    job_title = job['name']
    job_description = job['description']
    job_aspect_str = aspects_to_str(job['aspects'])
    
    # Always use the reliable policy-enhanced prompt
    from prompts.job_prompts import prompt1_with_policies
    prompt = prompt1_with_policies.format(
        job_title=job_title, 
        job_description=job_description, 
        job_aspect_str=job_aspect_str, 
        resume_str=resume_str, 
        aspect_str=aspect_str,
        policies_str=policies_str
    )
    return prompt

def second_questions_prompt(candidate_id:int, job:dict[str, Any], csv_string:str, aspects:Optional[list]=None, resume:Optional[str]=None, policies:Optional[str]=None) -> str:
    resumeStr = resume_to_str(resume) if (resume and isinstance(resume, str)) else "N/A"
    aspectStr = aspects_to_str(aspects) if (not resumeStr and aspects) else "N/A"
    policies_str = policies if policies else "N/A"
    
    jobTitle = job['name']
    jobDesciption = job['description']
    jobAspectStr = aspects_to_str(job['aspects'])

    # Use enhanced prompt that includes policies for follow-up questions
    from prompts.job_prompts import prompt2_with_policies
    prompt = prompt2_with_policies.format(
        jobTitle=jobTitle, 
        jobDesciption=jobDesciption, 
        jobAspectStr=jobAspectStr, 
        resumeStr=resumeStr, 
        aspectStr=aspectStr, 
        csv_string=csv_string,
        policies_str=policies_str
    )
    
    return prompt

async def generate_second_questions(job_id:int, candidate_id:int, job:dict, candidate:dict, csv_bytes:bytes, request: Request):
    try:
        # Get CSV As String
        csv_string = csv_bytes.decode("utf-8")
        
        # Load company policies for follow-up question generation
        policies = load_policies()

        # Generate Prompt
        prompt = second_questions_prompt(candidate_id, job, csv_string, candidate['aspects'], candidate['resume'], policies)

        # Call LLM
        response = await async_call_model(prompt, request)

        # Extract Content From Response
        content = None
        if hasattr(response, 'content'):
            content = response.content
        elif isinstance(response, dict) and 'content' in response:
            content = response['content']
        elif isinstance(response, str):
            content = response
        else:
            content = str(response)

        # Parse JSON Response
        questions_data = None
        try:
            questions_data = json.loads(content)
        except json.JSONDecodeError:
            print("Could not parse LLM response as JSON")
            update_candidate(job_id, candidate_id, status="Cross Questions Error")
            raise Exception("Could not parse LLM response as JSON")

        # Convert To CSV
        df = pd.DataFrame(questions_data)

        # Save Questions To File
        questions_filename = f"cross_questions_{candidate_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        job_dir_name = get_job_directory_name(job_id, job)
        questions_path = os.path.join(job_dir_name, questions_filename)

        # Save File
        abs_path = os.path.join(JOBS_STORAGE_DIR, questions_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        df.to_csv(abs_path, index=False)

        # Update Candidate Status
        update_candidate(job_id, candidate_id, status="Generated Cross Questions")

        print(f"Cross interview questions generated successfully for candidate {candidate_id}")
    except Exception as e:
        update_candidate(job_id, candidate_id, status="Cross Questions Error")
        print(f"Error generating cross questions: {str(e)}")

def process_candidate_prompt(candidate_id:int, job:dict[str, Any], aspects:Optional[list]=None, resume:Optional[str]=None) -> str:
    resume_str = resume_to_str(resume) if (resume and isinstance(resume, str)) else "N/A"
    aspects_str = aspects_to_str(aspects) if (not resume_str and aspects) else "N/A"
    
    job_title = job['name']
    job_description = job['description']
    job_aspects_str = aspects_to_str(job['aspects'])

    # Find Latest questions_answers_ File
    job_dir_name = get_job_directory_name(job['id'], job)
    written_interview = ""
    if not job_dir_name:
        written_interview = ""
    else:
        latest_file_path = find_latest_candidate_file(job['id'], candidate_id, "questions_answers", ".csv")
        if not latest_file_path:
            written_interview = ""
        else:
            with open(latest_file_path, "r", encoding="utf-8") as f:
                written_interview = f.read()

    # Find Latest transcript_ File
    transcript = ""
    if not job_dir_name:
        transcript = ""
    else:
        latest_file_path = find_latest_candidate_file(job['id'], candidate_id, "transcript", "")
        if not latest_file_path:
            transcript = ""
        else:
            with open(latest_file_path, "r", encoding="utf-8") as f:
                transcript = f.read()

    prompt = prompt3.format(job_title=job_title, job_description=job_description, job_aspects_str=job_aspects_str, resume_str=resume_str, aspects_str=aspects_str, written_interview=written_interview, transcript=transcript)
    
    return prompt

async def process_candidate(job, candidate, request: Request):
    job_id = job['id']
    
    try:
        candidate_id = candidate['id']
    
        update_candidate(job_id, candidate_id, status="Processing")
        prompt = process_candidate_prompt(candidate_id, job, candidate['aspects'], candidate['resume'])

        response = await async_call_model(prompt, request)
        score_str = None
        if hasattr(response, 'content'):
            score_str = response.content
        elif isinstance(response, dict) and 'content' in response:
            score_str = response['content']
        elif isinstance(response, str):
            score_str = response
        else:
            score_str = str(response)
        
        score = int(score_str)

        print(score)
        update_candidate(job_id, candidate_id, status="Processed", score=score)
    except Exception as e:
        update_candidate(job_id, candidate_id, status="Error Processing")
        print(f"Error processing candidate {candidate_id}: {str(e)}")

async def check_candidate_for_processing(job_id, candidate_id, request: Request):
    # Get Job Details
    job = get_job_by_id(job_id)
    if not job:
        return {"error": "Job not found"}
    
    # Get Candidate Details
    candidate = get_candidate_by_id(job_id, candidate_id)
    if not candidate:
        return {"error": "Candidate not found"}
    
    # Check If questions_answers_
    job_dir_name = get_job_directory_name(job_id, job)
    written_interview = ""
    if not job_dir_name:
        written_interview = ""
    else:
        latest_file_path = find_latest_candidate_file(job['id'], candidate_id, "questions_answers", ".csv")
        if not latest_file_path:
            written_interview = ""
        else:
            with open(latest_file_path, "r", encoding="utf-8") as f:
                written_interview = f.read()
    if (written_interview == ""):
        return {"error": "Written interview not found"}

    transcript = ""
    if not job_dir_name:
        transcript = ""
    else:
        latest_file_path = find_latest_candidate_file(job['id'], candidate_id, "transcript", "")
        if not latest_file_path:
            transcript = ""
        else:
            with open(latest_file_path, "r", encoding="utf-8") as f:
                transcript = f.read()
    if (transcript == ""):
        return {"error": "Interview transcript not found"}
    
    await process_candidate(job, candidate, request)

# --- API Endpoints ---

# DESCRIPTIONS - Get All
@router.get("/descriptions")
async def get_job_descriptions():
    try:
        jobs = get_all_jobs()
        return jobs
    except Exception as e:
        return {"error": str(e)}

# DESCRIPTIONS - Create New
@router.post("/descriptions")
async def create_new_job_description(job: Job, background_tasks: BackgroundTasks):
    try:
        # Create the job in the database
        job_id = create_job(job.name, job.description, job.aspects)
        
        # Create directory for the new job using job_id + safe_name
        create_job_directory(job_id, job.name)
        
        return {"message": "Job created successfully", "id": job_id}
    except Exception as e:
        return {"error": str(e)}

# DESCRIPTIONS - Get (By ID)
@router.get('/descriptions/{job_id}')
async def get_job_description(job_id: int):
    try:
        jobs = get_job_by_id(job_id)
        return jobs
    except Exception as e:
        return {"error": str(e)}

# DESCRIPTIONS - Update (By ID)
@router.put("/descriptions/{job_id}")
async def update_job(job_id: int, job: Job, background_tasks: BackgroundTasks):
    try:
        # Get Current Job Name For Old Directory Reference
        old_job = get_job_by_id(job_id)
        old_job_name = old_job["name"] if old_job else None

        # Update Job In Database
        success = update_job_by_id(job_id, job.name, job.description, job.aspects)
        if not success:
            return {"error": "Job not found"}

        # Handle Directory Operations
        if old_job_name:
            old_safe_name = sanitize_directory_name(old_job_name)
            old_dir_name = f"{job_id}_{old_safe_name}"
            old_path = os.path.join(JOBS_STORAGE_DIR, old_dir_name)

        new_safe_name = sanitize_directory_name(job.name)
        new_dir_name = f"{job_id}_{new_safe_name}"
        new_path = os.path.join(JOBS_STORAGE_DIR, new_dir_name)

        def move_candidate_files(old_dir, new_dir):
            if os.path.exists(old_dir):
                os.makedirs(new_dir, exist_ok=True)
                for filename in os.listdir(old_dir):
                    old_file = os.path.join(old_dir, filename)
                    new_file = os.path.join(new_dir, filename)
                    if os.path.isfile(old_file):
                        shutil.move(old_file, new_file)
                # Remove Old Directory If Empty
                try:
                    os.rmdir(old_dir)
                except OSError:
                    pass

        # If Job Title Changed, Handle Directory Renaming and move candidate files
        if old_job_name and old_job_name != job.name and os.path.exists(old_path):
            background_tasks.add_task(move_candidate_files, old_path, new_path)
        else:
            # Create New Directory If Old Doesn't Exist
            os.makedirs(new_path, exist_ok=True)

        return {"message": "Job updated successfully"}
    except Exception as e:
        return {"error": str(e)}

# DESCRIPTIONS - Delete (By ID)
@router.delete("/descriptions/{job_id}")
async def delete_job(job_id: int):
    try:
        # Get Job Name For Directory Deletion
        job = get_job_by_id(job_id)
        if not job:
            return {"error": "Job not found"}
        
        job_name = job["name"]
        safe_name = sanitize_directory_name(job_name)
        job_dir_name = f"{job_id}_{safe_name}"
        job_dir = os.path.join(JOBS_STORAGE_DIR, job_dir_name)
        
        # Delete Job From Database
        success = delete_job_by_id(job_id)
        if not success:
            return {"error": "Job not found or couldn't be deleted"}
        
        # Delete Job Directory If Exists
        if os.path.exists(job_dir):
            try:
                shutil.rmtree(job_dir)
            except Exception as e:
                return {"error": f"Failed to delete job directory: {e}"}
        
        return {"message": "Job deleted successfully"}
    except Exception as e:
        return {"error": str(e)}
    
# CANDIDATES - Get All (By Job ID)
@router.get("/candidates/{job_id}")
async def get_candidates(job_id: int):
    try:
        candidates = get_candidates_by_job_id(job_id)
        return candidates
    except Exception as e:  
        return {"error": str(e)}

# CANDIDATES - Create New
@router.post("/candidates/{job_id}")
async def create_new_candidate(
    job_id: int,
    full_name: str = Form(...),
    phone_number: str = Form(""),
    email: str = Form(...),
    resume: UploadFile = File(...),
    aspects: str = Form("[]")
    ):
    try:
        resume_content = await resume.read()
        
        # Parse Aspects
        aspects_list = json.loads(aspects) if aspects else []
        
        # Create Candidate Record
        candidate_id = create_candidate(
            job_id, full_name, phone_number, email, 
            "", aspects_list, "New"
        )
        
        resume_filename = f"resume_{candidate_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{resume.filename}"
        resume_path = jobs_save_resume(resume_content, job_id, candidate_id, resume_filename)
        
        # Update Candidate Record With Correct resume_path
        update_candidate(job_id, candidate_id, resume=resume_path)
        
        return {"message": "Candidate added successfully", "id": candidate_id}
    except Exception as e:
        return {"error": str(e)}

# CANDIDATES - Get (By Job ID & Candidate ID)
@router.get("/candidates/{job_id}/{candidate_id}")
async def get_candidate_by_ids(job_id: int, candidate_id: int):
    try:
        candidate = get_candidate_by_id(job_id, candidate_id)
        if not candidate:
            return {"error": "Candidate not found"}
        return candidate
    except Exception as e:
        return {"error": str(e)}

# CANDIDATES - Update (By Job ID & Candidate ID)
@router.put("/candidates/{job_id}/{candidate_id}")
async def update_candidate_by_id(
    job_id: int,
    candidate_id: int,
    phone_number: str = Form(""),
    resume: UploadFile = File(None),
    aspects: str = Form("[]")
):
    try:
        # Get Current Candidate Details
        candidate = get_candidate_by_id(job_id, candidate_id)
        if not candidate:
            return {"error": "Candidate not found"}

        # Parse Aspects
        aspects_list = json.loads(aspects) if aspects else []

        # Update Candidate Record
        update_candidate(job_id, candidate_id, phone_number=phone_number, aspects=aspects_list)

        # Handle Resume Upload
        if resume:
            resume_filename = f"resume_{candidate_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{resume.filename}"
            resume_content = await resume.read()
            resume_path = jobs_save_resume(resume_content, job_id, candidate_id, resume_filename)
            update_candidate(job_id, candidate_id, resume=resume_path)

        return {"message": "Candidate updated successfully"}
    except Exception as e:
        return {"error": str(e)}

# CANDIDATES - Delete (By Job ID & Candidate ID)
@router.delete("/candidates/{job_id}/{candidate_id}")
async def delete_candidate_by_id(job_id: int, candidate_id: int):
    try:
        # Get Job Details First
        job = get_job_by_id(job_id)
        if not job:
            return {"error": "Job not found"}
            
        # Get Candidate Details
        candidate = get_candidate_by_id(job_id, candidate_id)
        if not candidate:
            return {"error": "Candidate not found"}

        # Delete All Related Files
        job_dir_name = get_job_directory_name(job_id, job)
        if job_dir_name:
            job_dir = os.path.join(JOBS_STORAGE_DIR, job_dir_name)
            if os.path.exists(job_dir):
                for filename in os.listdir(job_dir):
                    should_delete = False
                    
                    candidate_prefixes = [
                        f"resume_{candidate_id}_",
                        f"interview_questions_{candidate_id}_",
                        f"cross_questions_{candidate_id}_",
                        f"questions_answers_{candidate_id}_",
                        f"transcript_{candidate_id}_",
                        f"report_ai_{candidate_id}_",
                        f"report_user_{candidate_id}_",
                        f"report_comparison_{candidate_id}_"
                    ]
                    
                    if any(filename.startswith(prefix) for prefix in candidate_prefixes):
                        should_delete = True
                    
                    if should_delete:
                        file_path = os.path.join(job_dir, filename)
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            print(f"Failed to delete file {filename}: {str(e)}")

        # Delete Candidate From Database
        success = update_candidate(job_id, candidate_id, deleted=True)
        if not success:
            return {"error": "Candidate not found or couldn't be deleted"}

        return {"message": "Candidate deleted successfully"}
    except Exception as e:
        return {"error": str(e)}

# QUESTIONS - Generate Interview Questions (By Job ID & Candidate ID)
@router.post("/questions/{job_id}/{candidate_id}")
async def generate_interview_questions(
    job_id: int, 
    candidate_id: int, 
    request: Request, 
    background_tasks: BackgroundTasks,
    generation_request: QuestionGenerationRequest = QuestionGenerationRequest()
):
    """
    Generate interview questions using LangGraph workflow orchestration.
    
    This endpoint uses a sophisticated LangGraph-based workflow that provides:
    - Modular, step-by-step question generation process
    - Robust error handling and automatic retries
    - Validation of generated questions for quality assurance
    - Adaptive branching for different scenarios
    - Enhanced logging and monitoring capabilities
    
    The workflow includes the following steps:
    1. Data Gathering: Collect job, candidate, and policy information
    2. Prompt Construction: Build optimized prompts with policy integration
    3. LLM Interaction: Call language model with error handling
    4. Response Parsing: Extract and clean JSON responses
    5. Validation: Ensure question quality and completeness
    6. Persistence: Save questions to structured file format
    
    Fallback: If LangGraph workflow fails, automatically falls back to
    the original question generation method for system reliability.
    """
    # Get Job Details
    job = get_job_by_id(job_id)
    if not job:
        return {"error": "Job not found"}
    
    # Get Candidate Details
    candidate = get_candidate_by_id(job_id, candidate_id)
    if not candidate:
        return {"error": "Candidate not found"}
    
    # Update Candidate Status
    update_candidate(job_id, candidate_id, status="Generating Questions")
        
    # Start Background Task For Question Generation with LangGraph workflow
    background_tasks.add_task(
        generate_first_questions, 
        job_id, 
        candidate_id, 
        job, 
        candidate, 
        request, 
        generation_request.policyId
    )
        
    return {
        "message": "Interview question generation started (using LangGraph workflow)",
        "status": "Generating Questions",
        "workflow": "LangGraph-enhanced with fallback support"
    }

# QUESTIONS - Get Interview Questions (By Job ID & Candidate ID)
@router.get("/questions/{job_id}/{candidate_id}")
async def get_interview_questions(job_id:int, candidate_id:int):
    try:
        job = get_job_by_id(job_id)
        job_dir_name = get_job_directory_name(job_id, job)
        if not job_dir_name:
            return {"error": "Job not found"}

        latest_file_path = find_latest_candidate_file(job_id, candidate_id, "interview_questions", ".csv")
        if not latest_file_path:
            return {"error": "No questions found for this candidate"}

        with open(latest_file_path, "r", encoding="utf-8") as f:
            csv_content = f.read()

        return {
            "message": "Interview questions fetched successfully",
            "questions_csv": csv_content,
            "candidate_id": candidate_id,
            "job_id": job_id
        }
    except Exception as e:
        return {"error": str(e)}

# QUESTIONS - Generate Cross Questions (By Job ID & Candidate ID)
@router.post("/cross-questions/{job_id}/{candidate_id}")
async def generate_cross_questions(job_id: int, candidate_id: int, request: Request, background_tasks: BackgroundTasks, csv_file: UploadFile = File(...)):
    try:
        # Check If File Uploaded
        if not csv_file:
            return {"error": "No file uploaded"}
        
        # Get Job Details
        job = get_job_by_id(job_id)
        if not job:
            return {"error": "Job not found"}
    
        # Get Candidate Details
        candidate = get_candidate_by_id(job_id, candidate_id)
        if not candidate:
            return {"error": "Candidate not found"}
        
        # Update Candidate Status
        update_candidate(job_id, candidate_id, status="Generating Cross Questions")
        
        csv_bytes = await csv_file.read()

        # Save Uploaded Questions Answers
        job_dir_name = get_job_directory_name(job_id, job)
        if not job_dir_name:
            return {"error": "Job not found"}
        job_dir = os.path.join(JOBS_STORAGE_DIR, job_dir_name)
        os.makedirs(job_dir, exist_ok=True)
        questions_answers_filename = f"questions_answers_{candidate_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        questions_answers_path = os.path.join(job_dir, questions_answers_filename)
        with open(questions_answers_path, "wb") as f:
            f.write(csv_bytes)
        
        background_tasks.add_task(generate_second_questions, job_id, candidate_id, job, candidate, csv_bytes, request)
        
        return {
            "message": "Cross questions generation started",
            "status": "Generating Cross Questions"
        }
    except Exception as e:
        return {"error": str(e)}

# QUESTIONS - Get Cross Questions (By Job ID & Candidate ID)
@router.get("/cross-questions/{job_id}/{candidate_id}")
async def get_cross_questions(job_id: int, candidate_id:int):
    try:
        job = get_job_by_id(job_id)
        job_dir_name = get_job_directory_name(job_id, job)
        if not job_dir_name:
            return {"error": "Job not found"}

        latest_file_path = find_latest_candidate_file(job_id, candidate_id, "cross_questions", ".csv")
        if not latest_file_path:
            return {"error": "No cross questions found for this candidate"}

        with open(latest_file_path, "r", encoding="utf-8") as f:
            csv_content = f.read()

        return {
            "message": "Cross interview questions fetched successfully",
            "cross_questions_csv": csv_content,
            "candidate_id": candidate_id,
            "job_id": job_id
        }
    except Exception as e:
        return {"error": str(e)}

# REPORT - Generate Report (Background Task)
def template_based_report_prompt(job_title: str, job_description: str, job_aspects_str: str, 
                               resume_str: str, aspects_str: str, transcript: str, 
                               candidate_name: str, candidate_id: int, job_id: int, template: dict) -> str:
    """Generate a report prompt based on a specific report template."""
    
    template_name = template.get('name', 'Unnamed Template')
    template_content = template.get('content', '')
    
    prompt = f"""
You are an expert interviewer and report writer. Generate a comprehensive interview evaluation report using the provided report template structure.

**Report Template to Follow:**
{template_name}

**Template Structure:**
{template_content}

**Interview Data:**
Job Title: {job_title}
Job Description: {job_description}
Required Skills: {job_aspects_str}
Candidate Name: {candidate_name}
Candidate Resume: {resume_str}
Candidate Skills: {aspects_str}
Interview Transcript: {transcript}

**CRITICAL INSTRUCTIONS:**
1. Follow the EXACT structure and format of the provided template
2. Fill in all sections of the template with relevant information from the interview data
3. Use the transcript to evaluate the candidate against the criteria in the template
4. Maintain the template's rating scales, checkboxes, and format
5. MANDATORY REPLACEMENTS - Replace these placeholders with actual data:
   - Replace [Candidate Name] with: {candidate_name}
   - Replace [Date] with: {datetime.now().strftime('%Y-%m-%d')}
   - Replace [Name] with: Interviewer
6. NEVER use any other name except "{candidate_name}" for the candidate
7. Do not hallucinate or make up candidate names - only use "{candidate_name}"

**Template Placeholders to Replace:**
- [Candidate Name] → {candidate_name}
- [Date] → {datetime.now().strftime('%Y-%m-%d')}
- [Name] (for interviewer) → Interviewer
6. Provide specific examples from the transcript to support your evaluations
7. Keep the template's original formatting and structure intact

Generate the complete evaluation report following the template structure:
"""
    
    return prompt

async def generate_report(job_id: int, candidate_id: int, request: Request, template_id: Optional[str] = None):
    """Background task to generate report for a candidate using LangGraph workflow or template-based generation."""
    try:
        # Update status to "Generating Report"
        update_candidate(job_id, candidate_id, status="Generating Report")
        
        # Get Job Details
        job = get_job_by_id(job_id)
        if not job:
            update_candidate(job_id, candidate_id, status="Error Generating Report")
            print(f"Job {job_id} not found for report generation")
            return
        
        # Get Candidate Details
        candidate = get_candidate_by_id(job_id, candidate_id)
        if not candidate:
            update_candidate(job_id, candidate_id, status="Error Generating Report")
            print(f"Candidate {candidate_id} not found for report generation")
            return
        
        # Prepare Data For Report Generation
        job_title = job['name']
        job_description = job['description']
        job_aspects_str = aspects_to_str(job['aspects'])
        candidate_name = candidate['full_name']  # Get the actual candidate name
        resume_str = resume_to_str(candidate['resume']) if candidate['resume'] else "N/A"
        aspects_str = aspects_to_str(candidate['aspects']) if candidate['aspects'] else "N/A"
        
        # Get Job Directory Name
        job_dir_name = get_job_directory_name(job_id, job)
        
        # Get Transcript Data
        transcript = ""
        if job_dir_name:
            latest_file_path = find_latest_candidate_file(job_id, candidate_id, "transcript", ".txt")
            if latest_file_path:
                with open(latest_file_path, "r", encoding="utf-8") as f:
                    transcript = f.read()
        
        # Load report template if specified
        report_template = None
        if template_id:
            report_template = load_report_template(template_id)
            if report_template:
                print(f"DEBUG: Using report template: {report_template.get('name', 'Unnamed')}")
            else:
                print(f"DEBUG: Report template {template_id} not found, using default report generation")
        
        # Try LangGraph workflow if enabled and template is available
        if LANGGRAPH_ENABLED and report_template and transcript:
            try:
                print(f"DEBUG: Using LangGraph workflow for candidate {candidate_id}")
                
                # Prepare data for LangGraph workflow
                job_description_dict = {
                    'name': job_title,
                    'description': job_description,
                    'aspects': job['aspects'] if job['aspects'] else []
                }
                
                # Run the LangGraph assessment workflow
                workflow_result = await run_interview_assessment(
                    job_id=job_id,
                    candidate_id=str(candidate_id),
                    candidate_name=candidate_name,
                    raw_transcript=transcript,
                    resume_text=resume_str,
                    job_description=job_description_dict,
                    policy_template=report_template,
                    request=request
                )
                
                # Update candidate with assessment scores and report
                if workflow_result.get('processing_complete') and workflow_result.get('generated_report'):
                    success = update_candidate_assessment_scores(
                        candidate_id=candidate_id,
                        technical_score=workflow_result.get('technical_score') or 0,
                        behavioral_score=workflow_result.get('behavioral_score') or 0,
                        experience_score=workflow_result.get('experience_score') or 0,
                        cultural_score=workflow_result.get('cultural_score') or 0,
                        final_score=workflow_result.get('final_score') or 0,
                        decision=workflow_result.get('decision') or 'UNDER_REVIEW',
                        assessment_report=workflow_result.get('generated_report')
                    )
                    
                    if success:
                        # Save report to file for backward compatibility
                        report_filename = f"report_ai_langgraph_{candidate_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                        job_dir = os.path.join(JOBS_STORAGE_DIR, job_dir_name)
                        os.makedirs(job_dir, exist_ok=True)
                        report_path = os.path.join(job_dir, report_filename)
                        
                        with open(report_path, "w", encoding="utf-8") as f:
                            f.write(workflow_result.get('generated_report'))
                        
                        # Update status based on decision
                        status = f"LangGraph Assessment Complete - {workflow_result.get('decision')}"
                        update_candidate(job_id, candidate_id, status=status)
                        
                        print(f"LangGraph assessment completed for candidate {candidate_id}: {workflow_result.get('final_score')}/100, Decision: {workflow_result.get('decision')}")
                        return
                    else:
                        print(f"Failed to save LangGraph assessment results for candidate {candidate_id}")
                else:
                    print(f"LangGraph workflow incomplete for candidate {candidate_id}")
                    
            except Exception as e:
                print(f"LangGraph workflow failed for candidate {candidate_id}: {str(e)}")
                # Fall back to template-based generation
        
        # Fallback to template-based or default generation
        if report_template:
            # Use template-specific report generation
            prompt = template_based_report_prompt(
                job_title=job_title,
                job_description=job_description,
                job_aspects_str=job_aspects_str,
                resume_str=resume_str,
                aspects_str=aspects_str,
                transcript=transcript,
                candidate_name=candidate_name,
                candidate_id=candidate_id,
                job_id=job_id,
                template=report_template
            )
        else:
            # Use default report generation
            prompt = report_generation_prompt.format(
                job_title=job_title,
                job_description=job_description,
                job_aspects_str=job_aspects_str,
                resume_str=resume_str,
                aspects_str=aspects_str,
                transcript=transcript,
                candidate_name=candidate_name,
                candidate_id=candidate_id,
                job_id=job_id
            )
        
        # Call LLM To Generate Report
        response = await async_call_model(prompt, request)
        
        # Extract Content From Response
        report_content = None
        if hasattr(response, 'content'):
            report_content = response.content
        elif isinstance(response, dict) and 'content' in response:
            report_content = response['content']
        elif isinstance(response, str):
            report_content = response
        else:
            report_content = str(response)
        
        # Save Report To File
        report_filename = f"report_ai_{candidate_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        job_dir = os.path.join(JOBS_STORAGE_DIR, job_dir_name)
        os.makedirs(job_dir, exist_ok=True)
        report_path = os.path.join(job_dir, report_filename)
        
        # Write Report Content To File
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        # Update Candidate Status
        update_candidate(job_id, candidate_id, status="Generated Report")
        
        print(f"Report generated successfully for candidate {candidate_id}")
    except Exception as e:
        update_candidate(job_id, candidate_id, status="Error Generating Report")
        print(f"Error generating report for candidate {candidate_id}: {str(e)}")


# QUESTIONS - Submit Interview Transcript (By Job ID & Candidate ID)
@router.post("/transcript/{job_id}/{candidate_id}")
async def submit_interview_transcript(
    job_id: int, 
    candidate_id: int, 
    request: Request, 
    background_tasks: BackgroundTasks, 
    transcript_file: UploadFile = File(...),
    template_id: Optional[str] = Query(None, description="Report template ID for generating structured reports")
):
    try:
        # Check If File Uploaded
        if not transcript_file:
            return {"error": "No file uploaded"}
        
        # Get Job Details
        job = get_job_by_id(job_id)
        if not job:
            return {"error": "Job not found"}
    
        # Get Candidate Details
        candidate = get_candidate_by_id(job_id, candidate_id)
        if not candidate:
            return {"error": "Candidate not found"}

        # Read Transcript File Content
        transcript_content = await transcript_file.read()

        transcript_filename = f"transcript_{candidate_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{transcript_file.filename}"

        job_dir_name = get_job_directory_name(job_id, job)
        if not job_dir_name:
            return {"error": "Job directory not found"}

        # Save Transcript File In Job Directory
        abs_path = os.path.join(JOBS_STORAGE_DIR, job_dir_name, transcript_filename)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(transcript_content)

        # Update Candidate Status
        update_candidate(job_id, candidate_id, status="Generating Report")

        # Start report generation with optional template
        background_tasks.add_task(generate_report, job_id, candidate_id, request, template_id)

        return {
            "message": "Transcript uploaded successfully",
            "transcript_file": os.path.join(job_dir_name, transcript_filename),
            "candidate_id": candidate_id,
            "job_id": job_id,
            "template_id": template_id
        }
    except Exception as e:
        return {"error": str(e)}


# REPORTS - Compare Reports (Background Task)
async def compare_results(job_id: int, candidate_id: int, request: Request):
    """Background task to compare reports for a candidate."""
    try:
        # Update status to "Comparing Reports"
        update_candidate(job_id, candidate_id, status="Comparing Reports")
        
        # Get Job Details
        job = get_job_by_id(job_id)
        if not job:
            update_candidate(job_id, candidate_id, status="Error Comparing Reports")
            print(f"Job {job_id} not found for report comparison")
            return
        
        # Get Candidate Details
        candidate = get_candidate_by_id(job_id, candidate_id)
        if not candidate:
            update_candidate(job_id, candidate_id, status="Error Comparing Reports")
            print(f"Candidate {candidate_id} not found for report comparison")
            return
        
        # Prepare Data For Report Comparison
        job_title = job['name']
        job_description = job['description']
        job_aspects_str = aspects_to_str(job['aspects'])
        
        # Get User Report Data
        user_report_path = find_latest_candidate_file(job_id, candidate_id, "report_user", ".md")
        if not user_report_path:
            update_candidate(job_id, candidate_id, status="Error Comparing Reports")
            print(f"User report not found for candidate {candidate_id}")
            return
        
        with open(user_report_path, "r", encoding="utf-8") as f:
            user_report_content = f.read()
        
        # Get AI Report Data
        ai_report_path = find_latest_candidate_file(job_id, candidate_id, "report_ai", ".md")
        if not ai_report_path:
            update_candidate(job_id, candidate_id, status="Error Comparing Reports")
            print(f"AI report not found for candidate {candidate_id}")
            return
        
        with open(ai_report_path, "r", encoding="utf-8") as f:
            ai_report_content = f.read()
        
        # Generate Comparison Prompt
        prompt = report_comparison_prompt.format(
            job_title=job_title,
            job_description=job_description,
            job_aspects_str=job_aspects_str,
            user_report=user_report_content,
            ai_report=ai_report_content,
            candidate_id=candidate_id,
            job_id=job_id
        )
        
        # Call LLM To Compare Reports
        response = await async_call_model(prompt, request)
        
        # Extract Content From Response
        comparison_content = None
        if hasattr(response, 'content'):
            comparison_content = response.content
        elif isinstance(response, dict) and 'content' in response:
            comparison_content = response['content']
        elif isinstance(response, str):
            comparison_content = response
        else:
            comparison_content = str(response)
        
        # Save Comparison Report To File
        job_dir_name = get_job_directory_name(job_id, job)
        comparison_filename = f"report_comparison_{candidate_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        job_dir = os.path.join(JOBS_STORAGE_DIR, job_dir_name)
        os.makedirs(job_dir, exist_ok=True)
        comparison_path = os.path.join(job_dir, comparison_filename)
        
        # Write Comparison Content To File
        with open(comparison_path, "w", encoding="utf-8") as f:
            f.write(comparison_content)
        
        # Parse the last line to determine the final decision
        lines = comparison_content.strip().split('\n')
        last_line = lines[-1].strip() if lines else ""
        print("LastLine:", last_line)
        # Update Candidate Status based on the decision
        if last_line == "Approved":
            update_candidate(job_id, candidate_id, status="Accepted")
            print(f"Candidate {candidate_id} approved and accepted")
        elif last_line == "Rejected":
            update_candidate(job_id, candidate_id, status="Rejected")
            print(f"Candidate {candidate_id} rejected")
        elif last_line == "Supervisor Required":
            update_candidate(job_id, candidate_id, status="Awaiting Supervisor Decision")
            print(f"Candidate {candidate_id} requires supervisor decision")
        else:
            # Fallback: if decision is unclear, require supervisor review
            update_candidate(job_id, candidate_id, status="Awaiting Supervisor Decision")
            print(f"Unclear decision for candidate {candidate_id}, requiring supervisor review. Last line: '{last_line}'")
        
        print(f"Report comparison completed successfully for candidate {candidate_id}")
    except Exception as e:
        update_candidate(job_id, candidate_id, status="Error Comparing Reports")
        print(f"Error comparing reports for candidate {candidate_id}: {str(e)}")


# REPORTS - Submit User Report (By Job ID & Candidate ID)
@router.post("/reports/{job_id}/{candidate_id}")
async def submit_user_report(job_id: int, candidate_id: int, request: Request, background_tasks: BackgroundTasks, markdown_file: UploadFile = File(...)):
    try:
        # Check If File Uploaded
        if not markdown_file:
            return {"error": "No file uploaded"}
        
        # Get Job Details
        job = get_job_by_id(job_id)
        if not job:
            return {"error": "Job not found"}
    
        # Get Candidate Details
        candidate = get_candidate_by_id(job_id, candidate_id)
        if not candidate:
            return {"error": "Candidate not found"}

        # Read Markdown File Content
        markdown_content = await markdown_file.read()

        report_filename = f"report_user_{candidate_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{markdown_file.filename}"

        job_dir_name = get_job_directory_name(job_id, job)
        if not job_dir_name:
            return {"error": "Job directory not found"}

        # Save Markdown File In Job Directory
        abs_path = os.path.join(JOBS_STORAGE_DIR, job_dir_name, report_filename)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(markdown_content)

        # Update Candidate Status
        update_candidate(job_id, candidate_id, status="Comparing Reports")
        
        # Start Background Task For Report Comparison
        background_tasks.add_task(compare_results, job_id, candidate_id, request)

        return {
            "message": "User report uploaded successfully",
            "report_file": os.path.join(job_dir_name, report_filename),
            "candidate_id": candidate_id,
            "job_id": job_id
        }
    except Exception as e:
        return {"error": str(e)}

# REPORTS - Get AI Report (By Job ID & Candidate ID)
@router.get("/ai-report/{job_id}/{candidate_id}")
async def get_ai_report(job_id: int, candidate_id: int):
    try:
        # Get Job Details
        job = get_job_by_id(job_id)
        if not job:
            return {"error": "Job not found"}
        
        # Get Candidate Details
        candidate = get_candidate_by_id(job_id, candidate_id)
        if not candidate:
            return {"error": "Candidate not found"}
        
        # Check if AI report exists
        ai_report_path = find_latest_candidate_file(job_id, candidate_id, "report_ai", ".md")
        if not ai_report_path:
            return {"error": "AI report not found"}
        
        # Read AI report content
        try:
            with open(ai_report_path, "r", encoding="utf-8") as f:
                ai_report_content = f.read()
            
            return {
                "ai_report": ai_report_content,
                "candidate_id": candidate_id,
                "job_id": job_id
            }
        except Exception as e:
            return {"error": f"Error reading AI report: {str(e)}"}
            
    except Exception as e:
        return {"error": str(e)}

# REPORTS - Get Comparison Report (By Job ID & Candidate ID)
@router.get("/comparison-report/{job_id}/{candidate_id}")
async def get_comparison_report(job_id: int, candidate_id: int):
    try:
        # Get Job Details
        job = get_job_by_id(job_id)
        if not job:
            return {"error": "Job not found"}
        
        # Get Candidate Details
        candidate = get_candidate_by_id(job_id, candidate_id)
        if not candidate:
            return {"error": "Candidate not found"}
        
        # Check if comparison report exists
        comparison_report_path = find_latest_candidate_file(job_id, candidate_id, "report_comparison", ".md")
        if not comparison_report_path:
            return {"error": "Comparison report not found"}
        
        # Read comparison report content
        try:
            with open(comparison_report_path, "r", encoding="utf-8") as f:
                comparison_report_content = f.read()
            
            return {
                "comparison_report": comparison_report_content,
                "candidate_id": candidate_id,
                "job_id": job_id
            }
        except Exception as e:
            return {"error": f"Error reading comparison report: {str(e)}"}
            
    except Exception as e:
        return {"error": str(e)}