import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.auth_router import router as auth_router
from backend.database import create_session_table
from backend.groq_router import router as groq_router
from backend.user_database import create_user_table

# Ensure upload folder exists
os.makedirs("uploaded_images", exist_ok=True)

app = FastAPI()

# CORS settings (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize both databases
@app.on_event("startup")
def startup():
    create_session_table()
    create_user_table()

# Register routers
app.include_router(groq_router, prefix="/chat")   # chat-related routes (text, image, etc.)
app.include_router(auth_router)                   # auth routes: /signup, /login

# Serve uploaded images
app.mount("/images", StaticFiles(directory="uploaded_images"), name="images")
app.mount("/chat/images", StaticFiles(directory="uploaded_images"), name="uploaded_images")
