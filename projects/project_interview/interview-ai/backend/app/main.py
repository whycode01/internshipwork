from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import websockets
import asyncio
import uuid
import os
from .utils import get_deepgram_api_key, extract_transcript

app = FastAPI()

# CORS middleware (allow all origins for testing; restrict for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants - replace with real values or env configured in your production environment
GROQ_API_KEY = "YOUR_GROQ_API_KEY"
GROQ_LLAMA_URL = "https://api.groq.com/openai/v1/chat/completions"
AUDIO_ROOT = "data/audio"
TRANSCRIPT_ROOT = "data/transcripts"

def ensure_user_dirs(user_id):
    os.makedirs(os.path.join(AUDIO_ROOT, user_id), exist_ok=True)
    os.makedirs(os.path.join(TRANSCRIPT_ROOT, user_id), exist_ok=True)

@app.websocket("/ws/audio")
async def audio_stream_endpoint(websocket: WebSocket):
    await websocket.accept()
    user_id = websocket.query_params.get("user_id") or "anonymous"
    session_id = uuid.uuid4().hex
    ensure_user_dirs(user_id)

    audio_file_path = os.path.join(AUDIO_ROOT, user_id, f"{session_id}.webm")
    transcript_file_path = os.path.join(TRANSCRIPT_ROOT, user_id, f"{session_id}.txt")
    audio_file = open(audio_file_path, "wb")

    dg_socket = None
    try:
        dg_uri = "wss://api.deepgram.com/v1/listen?punctuate=true&interim_results=true"
        # IMPORTANT: Pass additional_headers as list of tuples
        headers = [("Authorization", f"Token {get_deepgram_api_key()}")]
        dg_socket = await websockets.connect(dg_uri, additional_headers=headers)

        async def forward_audio():
            try:
                while True:
                    chunk = await websocket.receive_bytes()
                    await dg_socket.send(chunk)
                    audio_file.write(chunk)
            except WebSocketDisconnect:
                await dg_socket.close()
            except Exception as e:
                print("[Error] Forward audio:", e)
                await dg_socket.close()
            finally:
                audio_file.close()

        async def receive_transcript():
            try:
                async for message in dg_socket:
                    text = extract_transcript(message)
                    if text:
                        await websocket.send_text(text)
                        with open(transcript_file_path, "a", encoding="utf-8") as f:
                            f.write(text.strip() + "\n")
            except Exception as e:
                print("[Error] Receive transcript:", e)

        await asyncio.gather(forward_audio(), receive_transcript())

    except Exception as e:
        print("[Error] WebSocket error:", e)
        await websocket.close()
    finally:
        if dg_socket:
            await dg_socket.close()
        if not audio_file.closed:
            audio_file.close()


@app.post("/api/llm")
async def llm_conversation(request: Request):
    body = await request.json()
    user_id = body.get("user_id", "anonymous")
    messages = body.get("messages")

    if not messages or not isinstance(messages, list):
        return JSONResponse({"reply": "❌ No valid message list provided."}, status_code=400)

    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {
                "role": "system",
                "content": "You are an intelligent interview assistant. Answer user queries helpfully, clearly, and concisely."
            },
            *messages
        ],
        "max_tokens": 300,
        "temperature": 0.5,
    }

    async with httpx.AsyncClient() as client:
        try:
            groq_response = await client.post(
                GROQ_LLAMA_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30
            )
            if groq_response.status_code == 200:
                result = groq_response.json()
                reply = result["choices"][0]["message"]["content"].strip()
                return JSONResponse({"reply": reply})
            else:
                print(f"[Groq Error]: {groq_response.text}")
                return JSONResponse({"reply": "⚠ AI failed."}, status_code=500)
        except Exception as e:
            print("[LLM Error] Exception:", e)
            return JSONResponse({"reply": "⚠ Could not reach Groq API."}, status_code=500)
