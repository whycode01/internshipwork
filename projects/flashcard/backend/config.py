import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLAMA_MODEL = os.getenv("GROQ_MODEL")

# ✅ Correct base URL (OpenAI-compatible root)
LLAMA_BASE_URL = "https://api.groq.com/openai/v1/"

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY missing — check .env")
