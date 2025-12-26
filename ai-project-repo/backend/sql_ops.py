import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from routers.config import settings_service

# Database file path
DB_FILE = "lab_reviews.db"

# Initial prompts to be inserted
INITIAL_PROMPTS = [("domain_prompt", "GROQ",
    """You are an expert audit consultant.

    Create a dataset of audit questions based on the following domain and aspects.

    For each focus area of each aspect, generate 5 clear and practical audit questions. Each question should be assigned one of these categories:
    - Technology Leadership Presence
    - Technical Competency
    - Collaboration
    - Architectural Practices

    Return the output as a CSV with these columns:
    - Focus Area (Aspect)
    - Question
    - Audit Category

    Domain: {domain_name}

    Aspects and Focus Areas:
    {aspects}

    Output only CSV. Do not include any introductory or explanatory text.
    """),
    ("domain_prompt", "Ollama",
    """You are an expert audit consultant.

    Create a dataset of audit questions based on the following domain and aspects.

    For each focus area of each aspect, generate 5 clear and practical audit questions. Each question should be assigned one of these categories:
    - Technology Leadership Presence
    - Technical Competency
    - Collaboration
    - Architectural Practices

    Return the output as a CSV with these columns:
    - Focus Area (Aspect)
    - Question
    - Audit Category

    Domain: {domain_name}

    Aspects and Focus Areas:
    {aspects}

    Output only CSV. Do not include any introductory or explanatory text.
    """),
    ("report_generation_prompt", "Ollama", """Act like a Principal Architect tasked to review a project for technology leadership and maturity. A questionnaire was sent to the project team, and they have responded. Thereafter, a discussion was done with them. Based on the responses and discussion's transcript, you need to provide your observations, scope of improvement, and recommendations.

    The questionnaire is divided into four sections:
    1. **Technology Leadership Presence**: Evaluate the leadership's involvement, decision-making process, and communication of the technical vision.
    2. **Technical Competency**: Assess the team's skills, expertise, and ability to handle the project's technical challenges.
    3. **Collaboration**: Analyze the relationship between the client and the team, including conflict resolution and communication.
    4. **Architecture Practice**: Review the architectural decisions, principles, and how they are communicated and adapted.

    For each section, provide:
    - Observations: Key findings based on the responses and transcripts.
    - Scope of Improvement: Areas where the team can improve.
    - Recommendations: Actionable suggestions to address the gaps.

    Additionally, for each question and response, **you must assign a maturity level**:
    - **High**: Perfect or near perfect.
    - **Medium**: Working fine but needs attention.
    - **Low**: Significant challenges exist.

    For each maturity level, provide a **reason** explaining why the level was assigned.

    Here is the questionnaire and response in markdown format: {responses}
    Here is the transcript of conversation: {transcripts}

    **Important**: Ensure that every question and response has a maturity level (High, Medium, or Low) and a reason for the assigned level.
    """),

    ("questionnare_prompt", "GROQ", """
    You are an expert audit assistant generating customized questionnaires.

Use the domain-specific question bank: {question_bank}

Generate 20 **lab-specific** questions based on:
- Lab description: {description}
- Additional inputs during lab creation: {lab_questions}

Organize the questions into the following 4 sections with 5 questions each:
1. Technology Leadership Presence
2. Technical Competency
3. Collaboration
4. Architectural Practices

Instructions:
- Use the provided inputs to **tailor and adapt** the questions from the question bank so they are **highly relevant to this specific lab**.
- If needed, **modify** the wording or scope of questions to better fit the context of this lab’s purpose, tools, technologies, and structure.
- Only use questions from the question bank, but you may **refactor them** for lab specificity.
- Ensure the final set covers diverse yet targeted angles based on the inputs.

Output:
- Format: CSV
- Headers: Section, Question
- Do not include any explanation or extra content. Only provide the CSV rows.


    """),

    ("cross_questionnaire_prompt", "GROQ", """
    You are provided with a CSV file containing questions and responses. Your task is to generate **cross questions** for each question-response pair.

Use the context:
- Lab-specific questions: {lab_questions}

For each row, output:
- Original Question
- Response
- Cross Question (explores the response further)

Output only CSV. Do not include any introductory or explanatory text.
Here is the CSV file: {questions_responses}
 """),

    ("report_generation_prompt", "GROQ", """Role
You're a technology project reviewer analyzing questionnaire responses and discussion transcripts.
Task: Create a structured project analysis with:

1. Brief observations for each section
2. Areas needing improvement
3. Practical recommendations

Analysis Sections:

Technology Leadership,
Technical Competency,
Collaboration,
Architecture Practice

Instructions-
For each question response:

1. Assign maturity level: HIGH, MEDIUM, or LOW
2. Provide a brief reason (1-2 sentences)
3. Use straightforward language
4. Focus on concrete observations

Format:
# TECHNOLOGY PROJECT REVIEW

## Technology Leadership
**Observations:**
- [2-3 key points]

**Improvement Areas:**
- [1-2 areas]

**Recommendations:**
- [1-2 specific suggestions]

## Technical Competency
[Same structure]

## Collaboration
[Same structure]

## Architecture Practice
[Same structure]

## Maturity Assessment
| Question | Maturity | Reason |
|----------|----------|--------|
| [Question 1] | [HIGH/MEDIUM/LOW] | [Brief reason] | [additional rows]
Input Data

Questionnaire responses: {responses}
Discussion transcript: {transcripts}
    """),

    ("questionnaire_prompt", "Ollama", """
    Select 20 questions from {question_bank} based on:
    - Domain context: {description}
    - User-defined lab questions: {lab_questions}

    Select:
    - 5 from Technology Leadership Presence
    - 5 from Technical Competency
    - 5 from Collaboration
    - 5 from Architectural Practices

    Only output the questions in CSV format with headers. Do not include any explanation or introductory text.

    """),

    ("cross_questionnaire_prompt", "Ollama", """
    I will share a CSV file with original questions and their responses.

Generate a cross question for each pair to explore it deeper, using context from:

- Lab questions: {lab_questions}

Return output in CSV with columns:
- Question
- Response
- Cross Question

Do not provide answers or extra content.
CSV input: {questions_responses}

    """)
]

def init_db() -> sqlite3.Connection:
    """Initialize the database with required tables and initial data."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create domains table with questions column
    cursor.execute("""CREATE TABLE IF NOT EXISTS domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    aspects TEXT,
    created_at TEXT NOT NULL
    )""")
    
    # Create labs table
    cursor.execute("""CREATE TABLE IF NOT EXISTS labs (
        id INTEGER PRIMARY KEY,
        name TEXT,
        created_at TEXT,
        description TEXT,
        metadata TEXT,
        status TEXT,
        domain_id INTEGER,
        FOREIGN KEY (domain_id) REFERENCES domains (id)
    )""")
    
    # Create reports table
    cursor.execute("""CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY,
        lab_id INTEGER,
        report TEXT,
        csv_file TEXT,
        transcript_file TEXT,
        qustionnare_file TEXT,
        cross_questionnare_file TEXT,
        FOREIGN KEY(lab_id) REFERENCES labs(id)
    )""")
    
    # Create prompts table
    cursor.execute("""CREATE TABLE IF NOT EXISTS prompts (
        id INTEGER PRIMARY KEY,
        model TEXT,
        name TEXT,
        prompt TEXT,
        UNIQUE(name, model)
    )""")
    
    # Insert initial prompts
    cursor.executemany("""
    INSERT INTO prompts (name, model, prompt)
    VALUES (?, ?, ?)
    ON CONFLICT(name, model) DO NOTHING;
    """, INITIAL_PROMPTS)
    
    # # # JOBS

    # Create jobs description table
    cursor.execute("""CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    aspects TEXT,
    created_at TEXT NOT NULL
    )""")

    # Create candidates table with scoring fields
    cursor.execute("""CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        full_name TEXT NOT NULL,
        phone_number TEXT,
        email TEXT, 
        resume TEXT,
        aspects TEXT,
        status TEXT,
        score REAL,
        technical_score REAL,
        behavioral_score REAL,
        experience_score REAL,
        cultural_score REAL,
        final_score REAL,
        decision TEXT,
        assessment_report TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (job_id) REFERENCES jobs(id)
    )""")
    
    # Add new columns to existing tables if they don't exist
    try:
        cursor.execute("ALTER TABLE candidates ADD COLUMN technical_score REAL")
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        cursor.execute("ALTER TABLE candidates ADD COLUMN behavioral_score REAL")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE candidates ADD COLUMN experience_score REAL")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE candidates ADD COLUMN cultural_score REAL")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE candidates ADD COLUMN final_score REAL")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE candidates ADD COLUMN decision TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE candidates ADD COLUMN assessment_report TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    return conn

# Get all domains
def get_all_domains():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, aspects, created_at FROM domains")
    domains = cursor.fetchall()
    conn.close()
    
    result = []
    for domain in domains:
        # Parse the aspects JSON if it exists
        aspects = []
        if domain[3]:  # Check if aspects field is not None
            try:
                aspects = json.loads(domain[3])
            except json.JSONDecodeError:
                aspects = []  # Default to empty list if JSON parsing fails
        
        result.append({
            "id": domain[0],
            "name": domain[1],
            "description": domain[2],
            "aspects": aspects,  # Return as 'aspects' not 'questions'
            "created_at": domain[4]
        })
    return result

# Create new domain with questions
def create_domain(name, description, aspects=None):
    """Create a new domain with aspects and error handling"""
    print(f"SQL: Creating domain '{name}' in database")
    conn = None
    try:
        conn = init_db()
        cursor = conn.cursor()
        
        # Convert aspects to JSON string
        aspects_json = None
        if aspects:
            aspects_json = json.dumps([{
                "name": aspect.name,
                "focusAreas": aspect.focusAreas
            } for aspect in aspects])
        
        cursor.execute(
            "INSERT INTO domains (name, description, aspects, created_at) VALUES (?, ?, ?, ?)",
            (name, description, aspects_json, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        domain_id = cursor.lastrowid
        print(f"SQL: Domain inserted with ID {domain_id}, committing transaction")
        conn.commit()
        return domain_id
        
    except Exception as e:
        print(f"SQL Error in create_domain: {str(e)}")
        if conn:
            conn.rollback()
        # Re-raise so the API can handle it
        raise
    finally:
        if conn:
            conn.close()
            print("SQL: Connection closed")
            
# Get domain by ID with questions
def get_domain_by_id(domain_id):
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, aspects, created_at FROM domains WHERE id = ?", (domain_id,))
    domain = cursor.fetchone()
    conn.close()
    
    if domain:
        # Parse the aspects JSON if it exists
        aspects = []
        if domain[3]:  # Check if aspects field is not None
            try:
                aspects = json.loads(domain[3])
            except json.JSONDecodeError:
                aspects = []  # Default to empty list if JSON parsing fails
                
        return {
            "id": domain[0],
            "name": domain[1],
            "description": domain[2],
            "aspects": aspects,  # Return as 'aspects' not 'questions'
            "created_at": domain[4]
        }
    return None

# Update domain with questions
def update_domain_by_id(domain_id, name, description, aspects=None):
    conn = init_db()
    cursor = conn.cursor()
    
    # Convert aspects to JSON string
    aspects_json = None
    if aspects:
        aspects_json = json.dumps([{
            "name": aspect.name,
            "focusAreas": aspect.focusAreas
        } for aspect in aspects])
    
    cursor.execute(
        "UPDATE domains SET name = ?, description = ?, aspects = ? WHERE id = ?",
        (name, description, aspects_json, domain_id)
    )
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

# Delete domain (no change needed for this function as it's just deleting by ID)
def delete_domain_by_id(domain_id):
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM domains WHERE id = ?", (domain_id,))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

def create_lab(name: str, description: str, metadata: Optional[List[str]], domain_id: int) -> int:
    """
    Create a new lab entry in the database.
    
    Args:
        name: Name of the lab
        description: Description of the lab
        metadata: Additional metadata for the lab
        
    Returns:
        int: ID of the created lab
    """
    conn = init_db()
    cursor = conn.cursor()
    
    try:

        questions_json = None
        if metadata:
            questions_json = json.dumps(metadata)
        cursor.execute(
            "INSERT INTO labs (name, created_at, description, metadata, status, domain_id) VALUES (?, ?, ?, ?, ?, ?)",
            (name, datetime.now().isoformat(), description, questions_json, "Lab Created", domain_id)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_labs_by_domain_id(domain_id):
    """Retrieve all labs associated with a specific domain"""
    try:
        conn = init_db()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, name, description, status, created_at, metadata, domain_id
            FROM labs
            WHERE domain_id = ?
            ORDER BY created_at DESC
            """,
            (domain_id,)
        )
        
        labs = []
        for row in cursor.fetchall():
            lab = {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "status": row[3],
                "created_at": row[4],
                "metadata": row[5],
                "domain_id": row[6]
            }
            labs.append(lab)
        
        conn.close()
        return labs
    except Exception as e:
        print(f"Error fetching labs by domain: {e}")
        return []

def get_all_labs() -> List[Dict[str, Any]]:
    """
    Get all labs from the database.
    
    Returns:
        List[Dict[str, Any]]: List of all labs with their details
    """
    conn = init_db()
    cursor = conn.cursor()
    
    try:
        labs = cursor.execute("SELECT * FROM labs").fetchall()
        return [
            {
                "id": lab[0], 
                "name": lab[1], 
                "created_at": lab[2], 
                "description": lab[3], 
                "metadata": lab[4], 
                "status": lab[5]
            } 
            for lab in labs
        ]
    finally:
        conn.close()

def get_domain_name_by_id(domain_id: int) -> str:
    """
    Get domain name by domain ID.
    
    Args:
        domain_id: The ID of the domain to retrieve
        
    Returns:
        str: The name of the domain, or None if not found
    """
    try:
        conn = init_db()
        cursor = conn.cursor()
        
        # Query to get domain name by ID
        query = "SELECT name FROM domains WHERE id = ?"
        cursor.execute(query, (domain_id,))
        
        result = cursor.fetchone()
        
        # Close connection
        cursor.close()
        conn.close()
        
        # Return domain name if found, otherwise None
        return result[0] if result else None
    except Exception as e:
        print(f"Error retrieving domain name: {str(e)}")
        return None

def get_lab_by_id(lab_id: int) -> Optional[Dict[str, Any]]:
    """
    Get lab details by ID.
    
    Args:
        lab_id: ID of the lab to retrieve
        
    Returns:
        Optional[Dict[str, Any]]: Lab details or None if not found
    """
    conn = init_db()
    cursor = conn.cursor()
    
    try:
        lab = cursor.execute("SELECT * FROM labs WHERE id = ?", (int(lab_id),)).fetchone()
        if not lab:
            return None
        
        return {
            "id": lab[0], 
            "name": lab[1], 
            "created_at": lab[2], 
            "description": lab[3], 
            "metadata": lab[4], 
            "status": lab[5],
            "domain_id": lab[6]
        }
    finally:
        conn.close()

def get_lab_name(lab_id: int) -> Optional[str]:
    """Get the name of a lab by its ID."""
    conn = init_db()
    try:
        lab = conn.execute("SELECT name FROM labs WHERE id = ?", (lab_id,)).fetchone()
        return lab[0] if lab else None
    finally:
        conn.close()

def get_lab_description(lab_id: int) -> Optional[str]:
    """Get the description of a lab by its ID."""
    conn = init_db()
    try:
        description = conn.execute("SELECT description FROM labs WHERE id = ?", (lab_id,)).fetchone()
        return description[0] if description else None
    finally:
        conn.close()

def update_lab_status(lab_id: int, status: str) -> bool:
    """
    Update the status of a lab.
    
    Args:
        lab_id: ID of the lab to update
        status: New status for the lab
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    conn = init_db()
    try:
        conn.execute(
            "UPDATE labs SET status = ? WHERE id = ?",
            (status, lab_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()

def delete_lab_by_id(lab_id: int) -> bool:
    """
    Delete a lab from the database by its ID.
    Also deletes associated reports.
    """
    conn = init_db()
    cursor = conn.cursor()
    try:
        # Delete reports associated with the lab
        cursor.execute("DELETE FROM reports WHERE lab_id = ?", (lab_id,))
        # Delete the lab itself
        cursor.execute("DELETE FROM labs WHERE id = ?", (lab_id,))
        rows_affected = cursor.rowcount
        conn.commit()
        return rows_affected > 0
    finally:
        conn.close()

def save_questionnaire(lab_id: int, questionnaire_path: str) -> bool:
    """
    Save the path to a questionnaire file for a lab.
    
    Args:
        lab_id: ID of the lab
        questionnaire_path: Relative path to the questionnaire file
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    conn = init_db()
    try:
        conn.execute(
            "INSERT INTO reports (lab_id, qustionnare_file) VALUES (?, ?)",
            (lab_id, questionnaire_path)
        )
        conn.commit()
        return True
    finally:
        conn.close()

def save_cross_questionnaire(lab_id: int, cross_questionnaire_path: str) -> bool:
    """
    Save the path to a cross questionnaire file for a lab.
    
    Args:
        lab_id: ID of the lab
        cross_questionnaire_path: Relative path to the cross questionnaire file
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    conn = init_db()
    try:
        conn.execute(
            """
            UPDATE reports
            SET cross_questionnare_file = ?
            WHERE lab_id = ?
            """,
            (cross_questionnaire_path, lab_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()

def save_report(lab_id: int, report_path: str, csv_path: str, transcript_path: Optional[str]) -> bool:
    """
    Save paths to report files for a lab.
    
    Args:
        lab_id: ID of the lab
        report_path: Relative path to the report file
        csv_path: Relative path to the CSV file
        transcript_path: Relative path to the transcript file, if any
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    conn = init_db()
    try:
        conn.execute(
            """UPDATE reports
            SET report = ?, csv_file = ?, transcript_file = ?
            WHERE lab_id = ?
            """,
            (report_path, csv_path, transcript_path, lab_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()

def get_questionnaire(lab_id: int) -> Optional[str]:
    """
    Get the path to the questionnaire file for a lab.
    
    Args:
        lab_id: ID of the lab
        
    Returns:
        Optional[str]: Path to the questionnaire file or None if not found
    """
    conn = init_db()
    try:
        report_data = conn.execute(
            "SELECT qustionnare_file FROM reports WHERE lab_id = ? ORDER BY id DESC LIMIT 1", 
            (lab_id,)
        ).fetchone()
        
        return report_data[0] if report_data else None
    finally:
        conn.close()

def get_cross_questionnaire(lab_id: int) -> Optional[str]:
    """
    Get the path to the cross questionnaire file for a lab.
    
    Args:
        lab_id: ID of the lab
        
    Returns:
        Optional[str]: Path to the cross questionnaire file or None if not found
    """
    conn = init_db()
    try:
        report_data = conn.execute(
            "SELECT cross_questionnare_file FROM reports WHERE lab_id = ? ORDER BY id DESC LIMIT 1", 
            (lab_id,)
        ).fetchone()
        
        return report_data[0] if report_data else None
    finally:
        conn.close()

def get_lab_reports(lab_id: int) -> List[Dict[str, Any]]:
    """
    Get all reports for a lab.
    
    Args:
        lab_id: ID of the lab
        
    Returns:
        List[Dict[str, Any]]: List of all reports with their details
    """
    conn = init_db()
    try:
        reports = conn.execute(
            "SELECT report, csv_file, transcript_file FROM reports WHERE lab_id = ?", 
            (lab_id,)
        ).fetchall()
        
        return [
            {
                "report": report[0],
                "csv_file": report[1],
                "transcript_file": report[2]
            } 
            for report in reports
        ]
    finally:
        conn.close()

def get_prompt(prompt_name: str, model: str) -> Optional[str]:
    """
    Get a prompt by name and model.
    
    Args:
        prompt_name: Name of the prompt to retrieve
        model: Model associated with the prompt
        
    Returns:
        Optional[str]: Prompt text or None if not found
    """
    conn = init_db()
    try:
        prompt = conn.execute(
            "SELECT prompt FROM prompts WHERE name = ? AND model = ?", 
            (prompt_name, model)
        ).fetchone()
        
        return prompt[0] if prompt else None
    finally:
        conn.close()
        
def get_prompt_for_current_provider(prompt_name: str) -> str:
    """
    Get a prompt from the database matching the current provider.
    
    Args:
        prompt_name: Name of the prompt to retrieve (e.g., "report_generation_prompt")
        
    Returns:
        str: The prompt text for the current provider, or a default if not found
    """
    
    # Get the currently selected provider
    selected_config = settings_service.get_selected_config()
    current_provider = selected_config.provider
    
    # Try to get the specific prompt for this provider
    conn = init_db()
    try:
        # First try exact match by name and provider
        cursor = conn.cursor()
        cursor.execute(
            "SELECT prompt FROM prompts WHERE name = ? AND model = ?", 
            (prompt_name, current_provider)
        )
        prompt = cursor.fetchone()
        
        if prompt:
            return prompt[0]
        
        # If no match, try with Ollama as fallback provider
        cursor.execute(
            "SELECT prompt FROM prompts WHERE name = ? AND model = ?", 
            (prompt_name, "Ollama")
        )
        default_prompt = cursor.fetchone()
        
        if default_prompt:
            return default_prompt[0]
        
        # If still no match, try any prompt with this name
        cursor.execute(
            "SELECT prompt FROM prompts WHERE name = ? LIMIT 1", 
            (prompt_name,)
        )
        any_prompt = cursor.fetchone()
        
        if any_prompt:
            return any_prompt[0]
            
        # Last resort: hardcoded fallbacks
        from prompts.lab_review_prompts import (cross_questionnaire_prompt,
                                                questionnare_prompt,
                                                report_generation_prompt)
        
        fallbacks = {
            "report_generation_prompt": report_generation_prompt,
            "questionnare_prompt": questionnare_prompt,
            "cross_questionnaire_prompt": cross_questionnaire_prompt
        }
        return fallbacks.get(prompt_name, "")
    finally:
        conn.close()

def get_lab_metadata(lab_id: int) -> Optional[List[str]]:
    """
    Get metadata for a specific lab.
    
    Args:
        lab_id: ID of the lab
        
    Returns:
        Optional[List[str]]: List of metadata for the lab or None if not found
    """
    conn = init_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT metadata FROM labs WHERE id = ?", (lab_id,))
    metadata_json = cursor.fetchone()
    
    if metadata_json and metadata_json[0]:
        try:
            return json.loads(metadata_json[0])
        except json.JSONDecodeError:
            return []
    
    return None

def check_lab_exists(lab_name: str, domainId: int) -> bool:
    """
    Check if a lab exists by its name.
    
    Args:
        lab_name (str): Name of the lab
        
    Returns:
        bool: True if the lab exists, False otherwise
    """
    conn = init_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM labs WHERE name = ? AND domain_id = ?", (lab_name,domainId))
    count = cursor.fetchone()[0]
    
    conn.close()
    return count > 0

# # #
# # # JOBS
# # #

# # /DESCRIPTIONS

def get_all_jobs():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, aspects, created_at FROM jobs")
    jobs = cursor.fetchall()
    conn.close()
    
    result = []
    for job in jobs:
        # Parse the aspects JSON if it exists
        aspects = []
        if job[3]:  # Check if aspects field is not None
            try:
                aspects = json.loads(job[3])
            except json.JSONDecodeError:
                aspects = []  # Default to empty list if JSON parsing fails
        
        result.append({
            "id": job[0],
            "name": job[1],
            "description": job[2],
            "aspects": aspects,  # Return as 'aspects'
            "created_at": job[4]
        })
    
    return result

def get_job_by_id(job_id):
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, aspects, created_at FROM jobs WHERE id = ?", (job_id,))
    job = cursor.fetchone()
    conn.close()
    
    if job:
        # Parse the aspects JSON if it exists
        aspects = []
        if job[3]:  # Check if aspects field is not None
            try:
                aspects = json.loads(job[3])
            except json.JSONDecodeError:
                aspects = []  # Default to empty list if JSON parsing fails
                
        return {
            "id": job[0],
            "name": job[1],
            "description": job[2],
            "aspects": aspects,  # Return as 'aspects' not 'questions'
            "created_at": job[4]
        }
    return None

def create_job(name, description, aspects=None):
    """Create a new job with aspects and error handling"""
    print(f"SQL: Creating job '{name}' in database")
    conn = None
    try:
        conn = init_db()
        cursor = conn.cursor()
        
        # Convert aspects to JSON string
        aspects_json = None
        if aspects:
            aspects_json = json.dumps([{
                "name": aspect.name,
                "focusAreas": aspect.focusAreas
            } for aspect in aspects])
        
        cursor.execute(
            "INSERT INTO jobs (name, description, aspects, created_at) VALUES (?, ?, ?, ?)",
            (name, description, aspects_json, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        job_id = cursor.lastrowid
        print(f"SQL: Job inserted with ID {job_id}, committing transaction")
        conn.commit()
        return job_id
    except Exception as e:
        print(f"SQL Error in create_job: {str(e)}")
        if conn:
            conn.rollback()
        # Re-raise so the API can handle it
        raise
    finally:
        if conn:
            conn.close()
            print("SQL: Connection closed")

def update_job_by_id(job_id, name, description, aspects=None):
    conn = init_db()
    cursor = conn.cursor()
    
    # Convert aspects to JSON string
    aspects_json = None
    if aspects:
        aspects_json = json.dumps([{
            "name": aspect.name,
            "focusAreas": aspect.focusAreas
        } for aspect in aspects])
    
    cursor.execute(
        "UPDATE jobs SET name = ?, description = ?, aspects = ? WHERE id = ?",
        (name, description, aspects_json, job_id)
    )
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

def delete_job_by_id(job_id):
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

# # /CANDIDATES

def get_candidates_by_job_id(job_id):
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, job_id, full_name, phone_number, email, resume, aspects, status, score, 
               technical_score, behavioral_score, experience_score, cultural_score, 
               final_score, decision, assessment_report, created_at 
        FROM candidates WHERE job_id = ?
    """, (job_id,))
    candidates = cursor.fetchall()
    conn.close()
    
    results = []
    if candidates:
        for candidate in candidates:
            aspects = []
            if candidate[6]:
                try:
                    aspects = json.loads(candidate[6])
                except json.JSONDecodeError:
                    aspects = []
            results.append({
                "id": candidate[0],
                "job_id": candidate[1],
                "full_name": candidate[2],
                "phone_number": candidate[3],
                "email": candidate[4],
                "resume": candidate[5],
                "aspects": aspects,
                "status": candidate[7],
                "score": candidate[8],
                "technical_score": candidate[9],
                "behavioral_score": candidate[10],
                "experience_score": candidate[11],
                "cultural_score": candidate[12],
                "final_score": candidate[13],
                "decision": candidate[14],
                "assessment_report": candidate[15],
                "created_at": candidate[16]
            })
    return results

def create_candidate(job_id, full_name, phone_number, email, resume_path, aspects, status, score=None):
    """Create a new candidate record in the database."""
    conn = init_db()
    cursor = conn.cursor()
    
    if aspects is None or isinstance(aspects, str):
        aspects_json = aspects
    else:
        aspects_json = json.dumps(aspects)

    cursor.execute("""
        INSERT INTO candidates (job_id, full_name, phone_number, email, resume, aspects, status, score, 
                              technical_score, behavioral_score, experience_score, cultural_score, 
                              final_score, decision, assessment_report, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_id, 
        full_name, 
        phone_number, 
        email, 
        resume_path, 
        aspects_json, 
        status, 
        score,
        None,  # technical_score
        None,  # behavioral_score
        None,  # experience_score
        None,  # cultural_score
        None,  # final_score
        None,  # decision
        None,  # assessment_report
        datetime.now().isoformat()
    ))
    
    candidate_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return candidate_id

def get_candidate_by_id(job_id, candidate_id):
    try:
        conn = init_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, job_id, full_name, phone_number, email, resume, aspects, status, score,
                   technical_score, behavioral_score, experience_score, cultural_score,
                   final_score, decision, assessment_report, created_at
            FROM candidates WHERE job_id = ? AND id = ?
        """, (job_id, candidate_id))
        candidate = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if candidate:
            aspects = []
            if candidate[6]:
                try:
                    aspects = json.loads(candidate[6])
                except json.JSONDecodeError:
                    aspects = []
            return {
                "id": candidate[0],
                "job_id": candidate[1],
                "full_name": candidate[2],
                "phone_number": candidate[3],
                "email": candidate[4],
                "resume": candidate[5],
                "aspects": aspects,
                "status": candidate[7],
                "score": candidate[8],
                "technical_score": candidate[9],
                "behavioral_score": candidate[10],
                "experience_score": candidate[11],
                "cultural_score": candidate[12],
                "final_score": candidate[13],
                "decision": candidate[14],
                "assessment_report": candidate[15],
                "created_at": candidate[16]
            }
        return None
    except Exception as e:
        print(f"Error in get_candidate_by_id: {str(e)}")
        return None

def update_candidate(job_id, candidate_id, full_name=None, phone_number=None, email=None, resume=None, aspects=None, status=None, score=None, technical_score=None, behavioral_score=None, experience_score=None, cultural_score=None, final_score=None, decision=None, assessment_report=None, deleted=False):
    conn = init_db()
    cursor = conn.cursor()
    
    if deleted:
        try:
            cursor.execute("DELETE FROM candidates WHERE job_id = ? AND id = ?", (job_id, candidate_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting candidate: {str(e)}")
            return False
        finally:
            conn.close()

    try:
        fields = []
        values = []

        if full_name is not None:
            fields.append("full_name = ?")
            values.append(full_name)
        if phone_number is not None:
            fields.append("phone_number = ?")
            values.append(phone_number)
        if email is not None:
            fields.append("email = ?")
            values.append(email)
        if resume is not None:
            fields.append("resume = ?")
            values.append(resume)
        if aspects is not None:
            if not isinstance(aspects, str):
                aspects = json.dumps(aspects)
            fields.append("aspects = ?")
            values.append(aspects)
        if status is not None:
            fields.append("status = ?")
            values.append(status)
        if score is not None:
            fields.append("score = ?")
            values.append(score)
        if technical_score is not None:
            fields.append("technical_score = ?")
            values.append(technical_score)
        if behavioral_score is not None:
            fields.append("behavioral_score = ?")
            values.append(behavioral_score)
        if experience_score is not None:
            fields.append("experience_score = ?")
            values.append(experience_score)
        if cultural_score is not None:
            fields.append("cultural_score = ?")
            values.append(cultural_score)
        if final_score is not None:
            fields.append("final_score = ?")
            values.append(final_score)
        if decision is not None:
            fields.append("decision = ?")
            values.append(decision)
        if assessment_report is not None:
            fields.append("assessment_report = ?")
            values.append(assessment_report)

        if not fields:
            return False

        values.extend([job_id, candidate_id])
        sql = f"UPDATE candidates SET {', '.join(fields)} WHERE job_id = ? AND id = ?"
        cursor.execute(sql, values)
        rows_affected = cursor.rowcount
        conn.commit()
        return rows_affected > 0
    except Exception as e:
        print(f"Error in update_candidate: {str(e)}")
# Additional helper functions for LangGraph workflow

def update_candidate_assessment_scores(candidate_id: int, technical_score: float, behavioral_score: float, 
                                     experience_score: float, cultural_score: float, final_score: float, 
                                     decision: str, assessment_report: str) -> bool:
    """Update candidate with assessment scores and report from LangGraph workflow."""
    conn = init_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE candidates 
            SET technical_score = ?, behavioral_score = ?, experience_score = ?, 
                cultural_score = ?, final_score = ?, decision = ?, assessment_report = ?
            WHERE id = ?
        """, (technical_score, behavioral_score, experience_score, cultural_score, 
              final_score, decision, assessment_report, candidate_id))
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating candidate assessment scores: {str(e)}")
        return False
    finally:
        conn.close()

def get_candidate_for_assessment(candidate_id: int) -> Optional[Dict[str, Any]]:
    """Get candidate data needed for LangGraph assessment."""
    conn = init_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.full_name, c.resume, j.name, j.description, j.aspects
            FROM candidates c
            JOIN jobs j ON c.job_id = j.id
            WHERE c.id = ?
        """, (candidate_id,))
        
        result = cursor.fetchone()
        if result:
            # Parse aspects
            aspects = []
            if result[5]:
                try:
                    aspects = json.loads(result[5])
                except json.JSONDecodeError:
                    aspects = []
            
            return {
                "candidate_id": result[0],
                "candidate_name": result[1],
                "resume_text": result[2],
                "job_name": result[3],
                "job_description": result[4],
                "job_aspects": aspects
            }
        return None
    except Exception as e:
        print(f"Error getting candidate for assessment: {str(e)}")
        return None
    finally:
        conn.close()

# External function for LLM calls (used by agents)
async def async_call_model(prompt: str, request) -> str:
    """Async wrapper for calling the LLM model from agents."""
    from routers.jobs import \
        async_call_model as jobs_async_call_model  # Import from correct module
    return await jobs_async_call_model(prompt, request)