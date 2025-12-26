import os

from dotenv import load_dotenv

load_dotenv()

# Groq & model config
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TEXT_MODEL = os.getenv("TEXT_MODEL", "llama3-70b-8192")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
MAX_IMAGE_WIDTH = int(os.getenv("MAX_IMAGE_WIDTH", 512))

# JWT auth
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # no fallback for production
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
