import os
import json
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from rag_engine import generate_flashcards, match_answer
from pdf_parser import parse_pdf
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FLASHCARD_STORE = "generated_flashcards.json"
PDF_STORE = "last_uploaded_text.txt"

def load_existing_flashcards():
    if os.path.exists(FLASHCARD_STORE):
        with open(FLASHCARD_STORE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_flashcards(flashcards):
    with open(FLASHCARD_STORE, "w", encoding="utf-8") as f:
        json.dump(flashcards, f, indent=2)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    pdf_text = parse_pdf(contents)

    with open(PDF_STORE, "w", encoding="utf-8") as f:
        f.write(pdf_text)

    flashcards = generate_flashcards(pdf_text, existing_questions=[])
    save_flashcards(flashcards)

    return JSONResponse(content={"flashcards": flashcards})

@app.get("/generate_more_flashcards/")
def generate_more_flashcards():
    if not os.path.exists(PDF_STORE):
        return JSONResponse(content={"error": "No uploaded PDF content found."}, status_code=400)

    with open(PDF_STORE, "r", encoding="utf-8") as f:
        pdf_text = f.read()

    existing_flashcards = load_existing_flashcards()
    existing_questions = [fc["question"] for fc in existing_flashcards]

    new_flashcards = generate_flashcards(pdf_text, existing_questions=existing_questions)

    all_flashcards = existing_flashcards + new_flashcards
    save_flashcards(all_flashcards)

    return JSONResponse(content={"flashcards": new_flashcards})

@app.post("/check-answer/")
async def check_answer(question: str = Form(...), answer: str = Form(...)):
    flashcards = load_existing_flashcards()

    correct_answer = None
    for fc in flashcards:
        if fc["question"].strip().lower() == question.strip().lower():
            correct_answer = fc["answer"]
            break

    if not correct_answer:
        return JSONResponse(content={"error": "Question not found."}, status_code=404)

    is_correct = match_answer(question, answer, correct_answer)
    return JSONResponse(content={"correct": is_correct})
