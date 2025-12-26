import os
from fastapi import UploadFile, Form, File, BackgroundTasks, Query, Request, APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime
import pandas as pd
from typing import Optional, List
import json
from pydantic import BaseModel
import io
import shutil
import re
from langchain_experimental.data_anonymizer import PresidioReversibleAnonymizer
from prompts.lab_review_prompts import report_generation_prompt, questionnare_prompt, cross_questionnaire_prompt
from io import StringIO
import asyncio
from routers.config import settings_service

from sql_ops import (
    check_lab_exists, create_domain, delete_domain_by_id, get_all_domains, get_domain_by_id, init_db, create_lab, get_all_labs, get_lab_by_id, get_lab_name, 
    get_lab_description, update_domain_by_id, update_lab_status, save_questionnaire, get_lab_metadata, delete_lab_by_id,
    save_cross_questionnaire, save_report, get_questionnaire, 
    get_cross_questionnaire, get_lab_reports, get_prompt,
    get_labs_by_domain_id, get_domain_name_by_id, get_prompt_for_current_provider,
)

router = APIRouter(
    prefix="/api/audit",
    tags=["Audit"]
)

# --- Configuration ---
STORAGE_DIR = 'storage/audit'
os.makedirs(STORAGE_DIR, exist_ok=True)

# --- Pydantic Models For API Data ---
class Lab(BaseModel):
    name: str
    description: str
    metadata: Optional[List[str]] = []
    domain_id: Optional[int] = None  # Add domain_id field

class FocusArea(BaseModel):
    name: str

class Aspect(BaseModel):
    name: str
    focusAreas: List[str]

class Domain(BaseModel):
    name: str
    description: str
    aspects: List[Aspect]

# --- Helper Functions ---
def sanitize_directory_name(name: str) -> str:
    """
    Sanitizes the name to create a valid directory name.
    Removes special characters and replaces spaces with underscores.
    """
    sanitized = re.sub(r'[^\w\s-]', '', name)
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    return sanitized.lower()

def create_domain_directory(domain_name: str) -> str:
    """Creates a directory for the domain using its name and returns the path."""
    safe_name = sanitize_directory_name(domain_name)
    domain_dir = os.path.join(STORAGE_DIR, safe_name)
    os.makedirs(domain_dir, exist_ok=True)
    return domain_dir

def create_lab_directory(domain_name: str, lab_name: str) -> str:
    """
    Creates a directory structure for the lab within its domain and returns the path.
    
    Args:
        domain_name: Name of the domain
        lab_name: Name of the lab
    
    Returns:
        str: Path to the lab directory
    """
    # First create domain directory
    domain_dir = create_domain_directory(domain_name)
    
    # Then create lab directory inside domain
    safe_lab_name = sanitize_directory_name(lab_name)
    lab_dir = os.path.join(domain_dir, safe_lab_name)
    os.makedirs(lab_dir, exist_ok=True)
    return lab_dir

def get_lab_path(domain_name: str, lab_name: str) -> str:
    """
    Gets the relative path to a lab directory.
    
    Args:
        domain_name: Name of the domain
        lab_name: Name of the lab
        
    Returns:
        str: Relative path to the lab directory
    """
    safe_domain = sanitize_directory_name(domain_name)
    safe_lab = sanitize_directory_name(lab_name)
    return os.path.join(safe_domain, safe_lab)

def save_file(file_content: bytes | str, domain_name: str, lab_name: str, filename: str) -> str:
    """
    Saves a file to the lab's directory within its domain and returns the relative path.
    
    Args:
        file_content: Either bytes or string content to save
        domain_name: Name of the domain
        lab_name: Name of the lab
        filename: Name of the file to save
    
    Returns:
        str: Relative path to the saved file
    """
    lab_dir = create_lab_directory(domain_name, lab_name)
    abs_path = os.path.join(lab_dir, filename)
    
    # Create the relative path including domain/lab structure
    rel_path = os.path.join(
        sanitize_directory_name(domain_name),
        sanitize_directory_name(lab_name), 
        filename
    )
    
    # Handle both string and bytes content
    mode = 'wb' if isinstance(file_content, bytes) else 'w'
    with open(abs_path, mode) as f:
        f.write(file_content)
    
    return rel_path

def read_file(relative_path: str) -> str:
    """Reads content from a file given its relative path."""
    abs_path = os.path.join(STORAGE_DIR, relative_path)
    with open(abs_path, 'r') as f:
        return f.read()
    
def anonymize_text(tran: str, domain_name: str, lab_name: str) -> str:
    anonymizer = PresidioReversibleAnonymizer()
    transcript_content = read_file(tran)
    a = anonymizer.anonymize(transcript_content)
    
    # Update mapping file path to include domain structure
    lab_path = get_lab_path(domain_name, lab_name)
    mapping_filename = os.path.join(STORAGE_DIR, lab_path, f"{sanitize_directory_name(lab_name)}_deanonymizer_mapping.json")
    anonymizer.save_deanonymizer_mapping(mapping_filename)
    return a

def deanonymize_text(text: str, domain_name: str, lab_name: str) -> str:
    anonymizer = PresidioReversibleAnonymizer()
    transcript_content = text
    a = anonymizer.deanonymize(transcript_content)
    return a

def call_model(user_message):
    llm = settings_service.get_cached_llm()
    """Call the LLM model and get a response."""
    response = llm.invoke(user_message)
    return response

async def async_call_model(user_message, request: Request):
    """Asynchronous wrapper for calling the model."""
    # Run Model Call In Separate Thread To Avoid Blocking
    loop = asyncio.get_event_loop()
    executor = request.app.state.executor
    return await loop.run_in_executor(executor, call_model, user_message)

async def async_generate_report( lab_name, responses, transcripts, request: Request):
    """Asynchronous wrapper for generating a report."""
    prompt_template = get_prompt_for_current_provider("report_generation_prompt")
    if not prompt_template:
        prompt_template = report_generation_prompt
    
    # Format responses to make them more readable
    formatted_responses = json.dumps(responses, indent=2)
    
    prompt = prompt_template.format(responses=formatted_responses, transcripts=transcripts)
    
    # Get the response from the model
    response = await async_call_model(prompt, request)
    
    # Extract the text content from the AIMessage object
    if hasattr(response, 'content'):
        return response.content
    elif isinstance(response, dict) and 'content' in response:
        return response['content']
    elif isinstance(response, str):
        return response
    else:
        # If we can't extract content, convert the whole response to string
        return str(response)
    
async def generate_question_bank_task(domain_id: int, request: Request):
    """Background task for generating a question bank for a domain."""
    
    try:
        # Get domain info
        domain = get_domain_by_id(domain_id)
        if not domain:
            print(f"Error: Domain {domain_id} not found")
            return
        
        domain_name = domain["name"]
        aspects = domain["aspects"] if "aspects" in domain else []
        
        print(f"Starting question bank generation for domain '{domain_name}'")
        
        # Check if we have aspects to work with
        if not aspects:
            print(f"Warning: Domain '{domain_name}' has no aspects, cannot generate question bank")
            return
        
        # Format aspects for the prompt
        aspects_list_text = ""
        index = 1
        
        for aspect in aspects:
            aspect_name = aspect['name']
            for focus_area in aspect['focusAreas']:
                aspects_list_text += f"{index}. {focus_area} ({aspect_name})\n"
                index += 1
        
        # Get prompt template from database or use default
        prompt_template = get_prompt_for_current_provider("domain_prompt")
        
        # Format the prompt with domain information
        prompt = prompt_template.format(domain_name=domain_name, aspects=aspects_list_text)
        
        # Call the model asynchronously
        response = await async_call_model(prompt, request)
        
        # Extract the content from the response
        if hasattr(response, 'content'):
            content = response.content
        elif isinstance(response, dict) and 'content' in response:
            content = response['content']
        elif isinstance(response, str):
            content = response
        else:
            content = str(response)
        
        # Save question bank to file
        question_bank_filename = f"question_bank.csv"
        df = pd.read_csv(StringIO(content))
        
        question_bank_path = save_file(
            df.to_csv(index=False), 
            domain_name, 
            "", # No lab name for domain-level files
            question_bank_filename
        )
        
        print(f"Question bank for domain '{domain_name}' generated successfully and saved at {question_bank_path}")
        
    except Exception as e:
        # Log the error
        print(f"Error generating question bank for domain {domain_id}: {str(e)}")

async def generate_questionnaire_task(lab_id: int, description, content, request: Request):
    """Background task for generating questionnaire."""
    # llm = initialize_groq_client()
    
    try:
        # Get lab and domain info first
        lab = get_lab_by_id(lab_id)
        if not lab:
            return
        
        lab_name = lab["name"]
        domain_id = lab["domain_id"]
        domain_name = get_domain_name_by_id(domain_id)
        
        # Update status to show work has started
        update_lab_status(lab_id, "Generating Questionnare")
        
        # Get prompt template from database
        prompt_template = get_prompt_for_current_provider("questionnare_prompt")
        if not prompt_template:
            prompt_template = questionnare_prompt
        
        lab_q= get_lab_metadata(lab_id)
        # print(domain_q, lab_q)
        
        # Generate questionnaire
        csv_string = await async_call_model(prompt_template.format(description=description, question_bank=content, lab_questions=lab_q), request)
        if hasattr(csv_string, 'content'):
            csv_string = csv_string.content
            
        df = pd.read_csv(StringIO(csv_string))
        output_csv_filename = f"questionnare_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_csv_path = save_file(df.to_csv(index=False), domain_name, lab_name, output_csv_filename)
        
        # Save questionnaire to database
        save_questionnaire(lab_id, output_csv_path)
        
        # Update lab status
        update_lab_status(lab_id, "Generated Questionnaire")
        
    except Exception as e:
        # Log the error
        print(f"Error generating questionnaire: {str(e)}")
        # Update status to show error
        update_lab_status(lab_id, "Questionnare Error")

async def generate_cross_questionnaire_task(lab_id: int, content, request: Request):
    """Background task for generating cross questionnaire."""
    # llm = initialize_groq_client()
    
    try:
        # Get lab and domain info first
        lab = get_lab_by_id(lab_id)
        if not lab:
            return
        
        lab_name = lab["name"]
        domain_id = lab["domain_id"]
        domain_name = get_domain_name_by_id(domain_id)
        
        # Update status
        update_lab_status(lab_id, "Generating Cross Questions")
        
        # Get prompt template from database
        prompt_template = get_prompt_for_current_provider("cross_questionnaire_prompt")
        if not prompt_template:
            prompt_template = cross_questionnaire_prompt
            
        lab_q= get_lab_metadata(lab_id)
        # print(domain_q, lab_q)
        
        # Generate cross questionnaire
        csv_string = await async_call_model(prompt_template.format(questions_responses=content, lab_questions=lab_q), request)
        if hasattr(csv_string, 'content'):
            csv_string = csv_string.content
            
        df = pd.read_csv(StringIO(csv_string))
        output_csv_filename = f"cross_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_csv_path = save_file(df.to_csv(index=False), domain_name, lab_name, output_csv_filename)
        
        # Save cross questionnaire to database
        save_cross_questionnaire(lab_id, output_csv_path) 
        
        # Update lab status
        update_lab_status(lab_id, "Generated Cross Questions")
        
    except Exception as e:
        # Log the error 
        print(f"Error generating cross questionnaire: {str(e)}")
        # Update status to show error
        update_lab_status(lab_id, "Cross Questions Error")

async def generate_lab_report_task(lab_id: int, csv_content, transcript_rel_path, request: Request):
    """Background task for generating lab report."""
    # llm = initialize_ollama_client() 
    
    try:
        # Get lab and domain info first
        lab = get_lab_by_id(lab_id)
        if not lab:
            return
        
        lab_name = lab["name"]
        domain_id = lab["domain_id"]
        domain_name = get_domain_name_by_id(domain_id)
        
        # Update status
        update_lab_status(lab_id, "Generating Report")
        
        # Process the CSV
        if isinstance(csv_content, bytes):
            if csv_content.endswith(b'.csv'):
                df = pd.read_csv(io.BytesIO(csv_content))
            elif csv_content.endswith(b'.xlsx'):
                df = pd.read_excel(io.BytesIO(csv_content))
                df = df.fillna("")
            else:
                # Handle as csv.
                df = pd.read_csv(io.BytesIO(csv_content))
        else:
            df = pd.read_csv(StringIO(csv_content))
        
        responses = df.to_dict('records')
        
        # Process transcript if provided
        if transcript_rel_path:
            anonymized_transcript = anonymize_text(transcript_rel_path, domain_name, lab_name)
            anony_report_content = await async_generate_report(lab_name, responses, anonymized_transcript, request)
            report_content = deanonymize_text(anony_report_content, domain_name, lab_name)
        else:
            report_content = await async_generate_report( lab_name, responses, "No transcript provided", request)
        
        # Save report to file
        report_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_rel_path = save_file(report_content, domain_name, lab_name, report_filename)
        
        # Save CSV file path
        csv_filename = f"responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        csv_rel_path = save_file(df.to_csv(index=False), domain_name, lab_name, csv_filename)
        
        # Save report to database
        save_report(lab_id, report_rel_path, csv_rel_path, transcript_rel_path)
        
        # Update lab status
        update_lab_status(lab_id, "Generated Report")
        
    except Exception as e:
        # Log the error
        print(f"Error generating lab report: {str(e)}")
        # Update status to show error
        update_lab_status(lab_id, "Report Error")

# --- API Endpoints ---

# DOMAINS - Get All Domains
@router.get("/domains")
async def get_domains():
    try:
        domains = get_all_domains()
        return domains
    except Exception as e:
        return {"error": str(e)}

# DOMAINS - Create New Domain
@router.post("/domains")
async def create_new_domain(domain: Domain,
    request: Request,
    background_tasks: BackgroundTasks):
    try:
        # Create the domain in the database
        domain_id = create_domain(domain.name, domain.description, domain.aspects)
        
        # Create directory for the new domain
        domain_dir = create_domain_directory(domain.name)
        
        background_tasks.add_task(generate_question_bank_task, domain_id, request)
        
        return {"message": "Domain created successfully", "id": domain_id}
    except Exception as e:
        return {"error": str(e)}

# DOMAINS - Get Domain (By Domain ID)
@router.get("/domains/{domain_id}")
async def get_domain(domain_id: int):
    try:
        domain = get_domain_by_id(domain_id)
        if not domain:
            return {"error": "Domain not found"}
        return domain
    except Exception as e:
        return {"error": str(e)}

# DOMAINS - Update Domain (By Domain ID)
@router.put("/domains/{domain_id}")
async def update_domain(domain_id: int, domain: Domain, request: Request, background_tasks: BackgroundTasks):
    try:
        # Get current domain name for old directory reference
        old_domain = get_domain_by_id(domain_id)
        old_domain_name = old_domain["name"] if old_domain else None
        
        # Update the domain in the database
        success = update_domain_by_id(domain_id, domain.name, domain.description, domain.aspects)
        if not success:
            return {"error": "Domain not found"}
        
        # Handle directory operations
        old_path = None
        if old_domain_name:
            old_path = os.path.join(STORAGE_DIR, sanitize_directory_name(old_domain_name))
        
        new_path = os.path.join(STORAGE_DIR, sanitize_directory_name(domain.name))
        
        # If domain name has changed, handle directory renaming
        if old_domain_name and old_domain_name != domain.name and os.path.exists(old_path):
            os.rename(old_path, new_path)
        else:
            # Create new directory if old doesn't exist
            os.makedirs(new_path, exist_ok=True)
        
        # Update the question bank based on new aspects and focus areas
        # question_bank = generate_question_bank(domain.aspects)
        # question_bank_path = os.path.join(domain_id, "question_bank.csv")
        
        # # Save the updated question bank
        # with open(question_bank_path, 'w') as f:
        #     f.write(question_bank)
        background_tasks.add_task(generate_question_bank_task, domain_id, request)
        
        return {"message": "Domain updated successfully"}
    except Exception as e:
        return {"error": str(e)}

# DOMAINS - Delete Domain (By Domain ID)
@router.delete("/domains/{domain_id}")
async def delete_domain(domain_id: int):
    try:
        # Get domain name for directory deletion
        domain = get_domain_by_id(domain_id)
        if not domain:
            return {"error": "Domain not found"}
        
        domain_name = domain["name"]
        domain_dir = os.path.join(STORAGE_DIR, sanitize_directory_name(domain_name))
        
        # Delete domain from database
        success = delete_domain_by_id(domain_id)
        if not success:
            return {"error": "Domain not found or couldn't be deleted"}
        
        # Delete domain directory if it exists
        if os.path.exists(domain_dir):
            shutil.rmtree(domain_dir)
        
        return {"message": "Domain deleted successfully"}
    except Exception as e:
        return {"error": str(e)}

# LABS - Create
@router.post("/labs")
async def api_create_lab(lab: Lab):
    try:
        # Check if a lab with the same name already exists
        if check_lab_exists(lab.name, lab.domain_id):
            return JSONResponse(
                status_code=400,
                content={"detail": "A lab with this name already exists. Please choose a different name."}
            )
        
        # Create lab in database with domain_id
        lab_id = create_lab(lab.name, lab.description, lab.metadata, lab.domain_id)
        
        # Get domain name for directory creation
        domain_name = get_domain_name_by_id(lab.domain_id)
        
        # Create directory structure for the new lab
        create_lab_directory(domain_name, lab.name)
        
        return {"message": "Lab Created successfully", "id": lab_id}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

# LABS - Get All Labs (Optional: By Domain ID)
@router.get("/labs")
async def api_get_labs(domainId: Optional[int] = Query(None)):
    try:
        if domainId:
            # Get labs filtered by domain ID
            labs = get_labs_by_domain_id(domainId)
        else:
            # Get all labs
            labs = get_all_labs()
        return labs
    except Exception as e:
        return {"error": str(e)}

# LABS - Get Lab (By Domain ID & Lab ID)
@router.get("/labs/{domainId}/{labId}")
async def api_get_lab(domainId: int, labId: int):
    try:
        lab = get_lab_by_id(labId)
        if not lab or lab.get("domain_id") != domainId:
            return {"error": "Lab not found"}
        return lab
    except Exception as e:
        return {"error": str(e)}

# LABS - Delete Lab (By Domain ID & Lab ID)
@router.delete("/labs/{domainId}/{labId}")
async def api_delete_lab(domainId: int, labId: int):
    try:
        # Check if lab exists
        lab = get_lab_by_id(labId)
        if not lab or lab.get("domain_id") != domainId:
            return {"error": "Lab not found"}
        
        success = delete_lab_by_id(labId)
        if not success:
            return {"error": "Lab could not be deleted from database"}
        
        # Delete lab directory and all files
        domain_name = get_domain_name_by_id(domainId)
        lab_name = lab["name"]
        lab_dir = os.path.join(STORAGE_DIR, sanitize_directory_name(domain_name), sanitize_directory_name(lab_name))
        if os.path.exists(lab_dir):
            shutil.rmtree(lab_dir)
        
        return {"message": "Lab deleted successfully"}
    except Exception as e:
        return {"error": str(e)}

# QUESTIONS - Generate (By Domain ID & Lab ID)
@router.post("/questions/{domain_id}/{lab_id}")
async def generate_questions(
    domain_id: int,
    lab_id: int,
    request: Request,
    background_tasks: BackgroundTasks
):
    # Read dummy content from file
    # Get the lab details to determine the domain
    lab = get_lab_by_id(lab_id)
    if not lab:
        raise Exception("Lab not found")
    
    domain = get_domain_by_id(domain_id)
    if not domain:
        raise Exception("Domain not found")
    
    domain_name = domain["name"]
    
    # Construct the path to the question bank file in the domain directory
    question_bank_path = os.path.join(STORAGE_DIR, sanitize_directory_name(domain_name), "question_bank.csv")
    
    if not os.path.exists(question_bank_path):
        raise Exception("Question bank file not found in the domain directory")
    
    # Read the question bank file
    with open(question_bank_path, "r") as f:
        content = f.read()
    
    try:
        # Get lab description
        lab_description = get_lab_description(lab_id)
        if not lab_description:
            return {"error": "Lab not found"}
        
        # Update status immediately to show work has started
        update_lab_status(lab_id, "Generating Questionnare")
        
        # Start the background task
        background_tasks.add_task(generate_questionnaire_task, lab_id, lab_description, content, request)
        
        return {
            "message": "Questionnaire generation started",
            "status": "Generating Questionnaire"
        }
    except Exception as e:
        return {"error": str(e)}

# QUESTIONS - Get (By Lab ID)
@router.get("/questions/{domain_id}/{lab_id}")
async def get_questions_by_lab_id(lab_id: int):
    try:
        # First check if the lab exists
        lab = get_lab_by_id(lab_id)
        if not lab:
            return JSONResponse(
                status_code=404,
                content={"error": "Lab not found"}
            )
        
        status = lab["status"]
        
        # Return appropriate message based on status    
        if status == "Lab Created":
            return {"message": "Generate your questionnare now."}
        elif status == "Generating Questionnare":
            return {"message": "Questionnaire is being generated, please check back later."}
        elif status == "Questionnare Error":
            return {"message": "There was an error generating the questionnaire. Please try again."}
        
        # Get the questionnaire file path
        questionnaire_file = get_questionnaire(lab_id)
        
        if not questionnaire_file:
            return JSONResponse(
                status_code=404,
                content={"error": "Questionnaire not found for this lab"}
            )
        
        # Get file path
        questionnaire_path = os.path.join(STORAGE_DIR, questionnaire_file)
        
        # Read the CSV file
        lab_name = lab["name"]
        full_path = os.path.join(os.getcwd(), questionnaire_path)
        
        if not os.path.exists(full_path):
            return JSONResponse(
                status_code=404,
                content={"error": "Questionnaire file not found"}
            )
            
        with open(full_path, 'r') as f:
            csv_string = f.read()
        
        return {
            "message": "Questionnaire fetched successfully",
            "report": csv_string,
            "lab_id": lab_id,
            "lab_name": lab_name
        }
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# CROSS Qs - Generate (By Domain ID & Lab ID)
@router.get("/cross-questions/{domain_id}/{lab_id}")
async def get_cross_questionnare_by_lab_id(domain_id: int, lab_id: int):
    try:
        # Check If Lab Exists
        lab = get_lab_by_id(lab_id)
        if not lab or lab.get("domain_id") != domain_id:
            return {"error": "Lab not found"}
        status = lab["status"]
        
        # Return appropriate message based on status
        if status == "Followup Initiated":
            return {"message": "Generate your cross questionnare now."}
        elif status == "Generating Cross Questions":
            return {"message": "Cross questionnaire is being generated, please check back later."}
        elif status == "Cross Questions Error":
            return {"message": "There was an error generating the cross questionnaire. Please try again."}
        
        # Get the cross questionnaire file path
        cross_questionnaire_file = get_cross_questionnaire(lab_id)
        
        if not cross_questionnaire_file:
            return JSONResponse(
                status_code=404,
                content={"error": "Cross Questionnaire not found for this lab"}
            )
        
        # Get file path
        questionnaire_path = os.path.join(STORAGE_DIR, cross_questionnaire_file)
        
        # Read the CSV file
        lab_name = lab["name"]
        full_path = os.path.join(os.getcwd(), questionnaire_path)
        
        if not os.path.exists(full_path):
            return JSONResponse(
                status_code=404,
                content={"error": "Cross Questionnaire file not found"}
            )
            
        with open(full_path, 'r') as f:
            csv_string = f.read()
        
        return {
            "message": "Cross Questionnaire fetched successfully",
            "report": csv_string,
            "lab_id": lab_id,
            "lab_name": lab_name
        }
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# CROSS Qs - Generate (By Domain ID & Lab ID)
@router.post("/cross-questions/{domain_id}/{lab_id}")
async def generate_cross_questionnare(
    domain_id: int, 
    lab_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    csv_file: UploadFile = File(...),
):
    try:
        if not csv_file:
            return {"error": "No file uploaded"}
        
        # Get Lab Details
        lab = get_lab_by_id(lab_id)
        if not lab or lab.get("domain_id") != domain_id:
            return {"error": "Lab not found"}
        lab_name = lab["name"]
        
        # Get Domain Name
        domain_name = get_domain_name_by_id(domain_id)
        print(domain_id, domain_name)
        
        # Read file content
        content = await csv_file.read()
        
        # Update status to indicate work has started
        update_lab_status(lab_id, "Generating Cross Questions")
        
        # Save file for background processing
        csv_filename = csv_file.filename
        csv_rel_path = save_file(content, domain_name, lab_name, csv_filename)

        # Save a copy as cross_questions_answers_{timestamp}.csv for later report use
        cross_answers_filename = f"cross_questions_answers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        save_file(content, domain_name, lab_name, cross_answers_filename)
        
        # Start background task
        background_tasks.add_task(generate_cross_questionnaire_task, lab_id, content, request)
        
        return {
            "message": "Cross questionnaire generation started",
            "status": "Generating Cross Questions"
        }
    except Exception as e:
        return {"error": str(e)}

# REPORTS - Generate (By Domain ID & Lab ID)
@router.post("/reports/{domain_id}/{lab_id}")
async def generate_lab_report_with_domain(
    domain_id: int,
    lab_id: int,
    background_tasks: BackgroundTasks,
    request: Request,
    transcript_file: UploadFile = File(...)
):
    try:
        # Check If Lab Exists
        lab = get_lab_by_id(lab_id)
        if not lab or lab.get("domain_id") != domain_id:
            return {"error": "Lab not found"}
        
        lab_name = lab["name"]
        domain_name = get_domain_name_by_id(domain_id)

        # Find the latest questionnaire answers file in the lab directory
        lab_dir = os.path.join(STORAGE_DIR, sanitize_directory_name(domain_name), sanitize_directory_name(lab_name))
        if not os.path.exists(lab_dir):
            return {"error": "Lab directory not found"}
        # Find latest responses_*.csv file
        answer_files = [
            f for f in os.listdir(lab_dir)
            if (f.startswith("responses_") or f.startswith("cross_questions_answers_")) and f.endswith(".csv")
        ]
        if not answer_files:
            return {"error": "No questionnaire answers file found for this lab"}
        latest_answers_file = max(answer_files, key=lambda x: x)
        answers_path = os.path.join(lab_dir, latest_answers_file)
        with open(answers_path, "r", encoding="utf-8") as f:
            answers_content = f.read()

        # Save transcript file
        transcript_rel_path = None
        if transcript_file:
            transcript_content = await transcript_file.read()
            transcript_filename = f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{transcript_file.filename}"
            transcript_rel_path = save_file(transcript_content, domain_name, lab_name, transcript_filename)
        
        # Update status to indicate work has started
        update_lab_status(lab_id, "Generating Report")
        
        # Start background task (pass answers_content as csv_content)
        background_tasks.add_task(generate_lab_report_task, lab_id, answers_content, transcript_rel_path, request)
        
        return {
            "message": "Report generation started",
            "status": "Generating Report",
            "csv_file": latest_answers_file,
            "transcript_file": transcript_rel_path
        }
    except Exception as e:
        return {"error": str(e)}

# REPORTS - Get (By Lab ID)
@router.get("/reports/{domain_id}/{lab_id}")
async def api_get_lab_reports(domain_id: int, lab_id: int):
    try:
        # Check If Lab Exists
        lab = get_lab_by_id(lab_id)
        if not lab or lab.get("domain_id") != domain_id:
            return {"error": "Lab not found"}
            
        lab_status = lab["status"]
        
        # If status indicates work in progress, return this information
        if lab_status == "Generating Report":
            return {"status": lab_status, "message": "Report is being generated, please check back later."}
        elif lab_status == "Report Error":
            return {"status": lab_status, "message": "There was an error generating the report. Please try again."}
        elif lab_status != "Generated Report":
            return {"status": lab_status, "reports": []}
        
        # Otherwise fetch reports as normal
        reports = get_lab_reports(lab_id)
        
        if not reports:
            return {"status": lab_status, "reports": []}
        
        # Process reports to include content
        processed_reports = []
        for report in reports:
            processed_report = {
                "report": read_file(report["report"]) if report["report"] else None,
                "csv_file": report["csv_file"],
                "transcript_file": report["transcript_file"]
            }
            processed_reports.append(processed_report)
        
        return {
            "status": lab_status,
            "reports": processed_reports
        }
    except Exception as e:
        return {"error": str(e)}
