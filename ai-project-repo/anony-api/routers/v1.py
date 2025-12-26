import asyncio
import os
import aiosqlite
import json
import tempfile
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from typing import Dict
from langchain_experimental.data_anonymizer import PresidioReversibleAnonymizer
from langchain_experimental.data_anonymizer.deanonymizer_matching_strategies import (
    combined_exact_fuzzy_matching_strategy,
)
from presidio_anonymizer.entities import OperatorConfig

router = APIRouter(
    prefix="/api/v1",
    tags=["API v1"]
)

# --- Configuration ---
DB_PATH = "storage.db"
TABLE_NAME = "anonymization_api_v1"
DATA_EXPIRATION_DAYS = 30
CLEANUP_INTERVAL_HOURS = 6

# --- Database Setup ---
async def init_db():
    """Initializes the SQLite database and creates the table if it doesn't exist."""
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    token TEXT PRIMARY KEY,
                    deanonymizer_mapping TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            await conn.commit()
    except Exception as e:
        print(f"Database error during initialization: {e}")

# --- Pydantic Models for API Data ---
class AnonymizeRequest(BaseModel):
    text: str
    language: str = "en" # Default: English

class AnonymizeResponse(BaseModel):
    anonymized_text: str
    token: str

class DeanonymizeRequest(BaseModel):
    anonymized_text: str
    token: str

class DeanonymizeResponse(BaseModel):
    deanonymized_text: str

# --- Anonymizer Service Logic ---
def anonymize(text: str, language: str) -> (str, Dict):
    """
    Anonymizes the text and returns the anonymized text and the mapping.
    Resets the internal mapping for each new request to ensure thread safety.
    """
    anonymizer_instance = PresidioReversibleAnonymizer(
    add_default_faker_operators=True,
    operators={
            "DATE_TIME": OperatorConfig("keep"),
        }
    )
    anonymized_text = anonymizer_instance.anonymize(text, language=language)
    mapping = anonymizer_instance.deanonymizer_mapping
    return anonymized_text, mapping

def denonymize(text: str, mapping_json: str) -> str:
    """
    Deanonymizes the text using a provided mapping JSON.
    The library requires loading the mapping from a file, so we use a temporary file.
    """
    tmpfile = tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json")
    try:
        # Write Mapping To Temp File
        tmpfile.write(mapping_json)
        tmpfile.close()

        temp_anonymizer = PresidioReversibleAnonymizer()
        temp_anonymizer.load_deanonymizer_mapping(tmpfile.name)
        
        deanonymized_text = temp_anonymizer.deanonymize(
            text,
            deanonymizer_matching_strategy=combined_exact_fuzzy_matching_strategy,
        )
        return deanonymized_text
    finally:
        # Delete Temporary File
        os.unlink(tmpfile.name)

# --- Background Task for Cleanup ---
async def cleanup_expired_data():
    """Periodically deletes old records from the database."""
    while True:
        try:
            async with aiosqlite.connect(DB_PATH) as conn:
                threshold = (datetime.now() - timedelta(days=DATA_EXPIRATION_DAYS)).isoformat()
                await conn.execute(f"DELETE FROM {TABLE_NAME} WHERE timestamp < ?", (threshold,))
                await conn.commit()
                print(f"[{datetime.now()}] Cleanup task ran. Deleted records older than {DATA_EXPIRATION_DAYS} days.")
        except Exception as e:
            print(f"Error in cleanup_expired_data: {e}")
        await asyncio.sleep(CLEANUP_INTERVAL_HOURS * 3600)

@router.on_event("startup")
async def on_startup():
    """Initializes the database and starts the background cleanup task."""
    await init_db()
    asyncio.create_task(cleanup_expired_data())

# --- API Endpoints ---

@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return {"status": "ok"}

@router.post("/anonymize", response_model=AnonymizeResponse)
async def anonymize_endpoint(data: AnonymizeRequest):
    """
    Anonymizes the input text.
    
    - Replaces PII with fake data.
    - Generates a unique token for deanonymization.
    - Stores the mapping required to reverse the process.
    """
    if not data.text or not data.text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    try:
        anonymized_text, mapping = anonymize(data.text, data.language)
        token = str(uuid4())
        timestamp = datetime.now().isoformat()
        mapping_json = json.dumps(mapping)

        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute(
                f"INSERT INTO {TABLE_NAME} (token, deanonymizer_mapping, timestamp) VALUES (?, ?, ?)",
                (token, mapping_json, timestamp)
            )
            await conn.commit()

        return {"anonymized_text": anonymized_text, "token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anonymization failed: {str(e)}")

@router.get("/{token}", response_model=Dict)
async def mapping_endpoint(token: str):
    """
    Retrieves the mapping for a given token.
    
    - Used to fetch the mapping required for deanonymization.
    """
    if not token or not token.strip():
        raise HTTPException(status_code=400, detail="Token must be provided.")

    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            async with conn.execute(f"SELECT deanonymizer_mapping FROM {TABLE_NAME} WHERE token = ?", (token,)) as cursor:
                row = await cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Invalid token or data has expired.")

        mapping_json = row[0]
        return json.loads(mapping_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve mapping: {str(e)}")

@router.delete("/{token}")
async def delete_mapping(token: str):
    """
    Deletes the mapping for a given token.
    
    - Used to remove the mapping after deanonymization or when no longer needed.
    """
    if not token or not token.strip():
        raise HTTPException(status_code=400, detail="Token must be provided.")

    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute(f"DELETE FROM {TABLE_NAME} WHERE token = ?", (token,))
            await conn.commit()

        return {"detail": "Mapping deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete mapping: {str(e)}")

@router.post("/denonymize", response_model=DeanonymizeResponse)
async def denonymize_endpoint(data: DeanonymizeRequest):
    """
    Deanonymizes text using the provided token.

    - Retrieves the original PII mapping using the token.
    - Restores the original text.
    """
    if not data.anonymized_text or not data.anonymized_text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")
    if not data.token:
        raise HTTPException(status_code=400, detail="Token must be provided.")

    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            async with conn.execute(f"SELECT deanonymizer_mapping FROM {TABLE_NAME} WHERE token = ?", (data.token,)) as cursor:
                row = await cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Invalid token or data has expired.")

        mapping_json = row[0]
        deanonymized_text = denonymize(data.anonymized_text, mapping_json)
        
        return {"deanonymized_text": deanonymized_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deanonymization failed: {str(e)}")