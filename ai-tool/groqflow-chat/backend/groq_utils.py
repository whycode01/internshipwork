import base64
import hashlib
import json
import os

from groq import Groq

from backend.config import GROQ_API_KEY, IMAGE_MODEL, TEXT_MODEL

client = Groq(api_key=GROQ_API_KEY)

# Directory setup
CHAT_JSON_DIR = "chat_sessions"
UPLOAD_DIR = "uploaded_images"
os.makedirs(CHAT_JSON_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_json_path(session_id: str) -> str:
    return os.path.join(CHAT_JSON_DIR, f"{session_id}.json")

def load_session_json(session_id: str) -> dict:
    path = get_json_path(session_id)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"history": []}

def save_json_message(session_id: str, message: dict):
    path = get_json_path(session_id)
    session_data = load_session_json(session_id)
    session_data["history"].append(message)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2)

async def ask_groq_text(message: str, session_id: str):
    history = load_session_json(session_id)["history"]
    messages = []

    # Custom logic: detect question about uploaded images
    if "what" in message.lower() and "image" in message.lower() and "you" in message.lower():
        uploaded_images = [
            entry["image_path"] for entry in history
            if entry["type"] == "image_text" and entry.get("image_path")
        ]
        if uploaded_images:
            reply = "You've uploaded the following images:\n" + "\n".join(f"- {img}" for img in uploaded_images)
        else:
            reply = "You haven’t uploaded any images yet in this session."
        return {"response": reply}

    # Construct message history for Groq
    for record in history:
        if record["type"] == "image_text":
            content = record["content"] + f"\n[User uploaded image: {record.get('image_path')}]"
        else:
            content = record["content"]
        messages.append({"role": record["role"], "content": content})

    messages.append({"role": "user", "content": message})

    res = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=messages
    )

    assistant_reply = res.choices[0].message.content

    return {"response": assistant_reply}

def compute_image_hash(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()

async def ask_groq_image(message: str, image_bytes: bytes, session_id: str):
    image_hash = compute_image_hash(image_bytes)
    filename = f"{session_id}_{image_hash}.jpg"
    image_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(image_path):
        with open(image_path, "wb") as f:
            f.write(image_bytes)

    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": message},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{b64_image}"
                    }
                }
            ]
        }
    ]

    res = client.chat.completions.create(
        model=IMAGE_MODEL,
        messages=messages
    )

    assistant_reply = res.choices[0].message.content

    return {
        "response": assistant_reply,
        "image_filename": filename
    }
