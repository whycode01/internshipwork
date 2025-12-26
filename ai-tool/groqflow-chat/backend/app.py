import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import create_session_table
from backend.groq_router import router as groq_router

os.makedirs("uploaded_images", exist_ok=True)

# Mount the static directory
app.mount("/chat/images", StaticFiles(directory="uploaded_images"), name="uploaded_images")

app = FastAPI()

# CORS config (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(groq_router)

# Automatically create DB table on startup
@app.on_event("startup")
def on_startup():
    create_session_table()
