import json
import os
import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile

from backend.auth_router import get_current_user
from backend.database import ChatSession, SessionLocal
from backend.groq_utils import (ask_groq_image, ask_groq_text,
                                load_session_json, save_json_message)
from backend.user_models import User

router = APIRouter()

# --------- Text Chat ---------
@router.post("/text")
async def chat_text(
    message: str = Form(...),
    session_id: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    response = await ask_groq_text(message, session_id)

    save_json_message(session_id=session_id, message={
        "role": "user",
        "type": "text",
        "content": message
    })
    save_json_message(session_id=session_id, message={
        "role": "assistant",
        "type": "text",
        "content": response["response"]
    })

    db = SessionLocal()
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        db.add(ChatSession(session_id=session_id, title="Untitled", user_id=current_user.id))
        db.commit()
    db.close()

    return response

# --------- Image Chat ---------
@router.post("/image")
async def chat_image(
    message: str = Form(...),
    image: UploadFile = Form(...),
    session_id: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    image_bytes = await image.read()
    response = await ask_groq_image(message, image_bytes, session_id)
    content = response["response"]
    image_filename = response.get("image_filename")

    # ✅ Save messages to session history
    save_json_message(session_id=session_id, message={
        "role": "user",
        "type": "image_text",
        "content": message,
        "image_path": image_filename
    })
    save_json_message(session_id=session_id, message={
        "role": "assistant",
        "type": "text",
        "content": content
    })

    # ✅ Ensure DB session tracking
    db = SessionLocal()
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        db.add(ChatSession(session_id=session_id, title="Untitled", user_id=current_user.id))
        db.commit()
    db.close()

    return {
        "response": content,
        "image_filename": image_filename
    }


# --------- Chat History (JSON fallback) ---------
@router.get("/history")
async def get_history(
    session_id: str = Query(...),
    current_user: User = Depends(get_current_user)
):
    db = SessionLocal()
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    db.close()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    path = f"chat_sessions/{session_id}.json"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Session file not found")

    return load_session_json(session_id)["history"]

# --------- List All Sessions ---------
@router.get("/sessions")
async def get_all_sessions(current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    sessions = db.query(ChatSession.session_id, ChatSession.title).filter(
        ChatSession.user_id == current_user.id
    ).all()
    db.close()
    return [{"session_id": s.session_id, "title": s.title} for s in sessions]

# --------- Rename Session ---------
@router.post("/rename_session")
async def rename_session(
    session_id: str = Form(...),
    new_title: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    db = SessionLocal()
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        db.close()
        raise HTTPException(status_code=404, detail="Session not found")

    session.title = new_title
    db.commit()
    db.close()

    return {"status": "success"}

# --------- Delete Session ---------
@router.delete("/delete_session")
async def delete_session(
    session_id: str = Query(...),
    current_user: User = Depends(get_current_user)
):
    db = SessionLocal()
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        db.close()
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        json_path = f"chat_sessions/{session_id}.json"
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                history = json.load(f)["history"]
                for entry in history:
                    if entry.get("image_path"):
                        image_path = os.path.join("uploaded_images", entry["image_path"])
                        if os.path.exists(image_path):
                            os.remove(image_path)
            os.remove(json_path)
    except Exception:
        pass

    db.delete(session)
    db.commit()
    db.close()

    return {"status": "deleted"}
