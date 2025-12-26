import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# LangSmith configuration (set environment variables only)
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGSMITH_API_KEY"] = "YOUR_LANGSMITH_API_KEY"
os.environ["LANGCHAIN_PROJECT"] = "LangGraph-Question-Generation"

def initialize_langsmith():
    """Initialize LangSmith client (called only once during startup)"""
    try:
        from langsmith import Client
        langsmith_client = Client()
        print("✅ LangSmith integration enabled")
        print("🔗 Dashboard: https://smith.langchain.com/")
        print(f"📊 Project: LangGraph-Question-Generation")
        return langsmith_client
    except ImportError:
        print("⚠️  LangSmith not available - install with: pip install langsmith")
        return None
    except Exception as e:
        print(f"⚠️  LangSmith connection issue: {e}")
        return None

# -- Initialize Storage --
STORAGE_DIR = 'storage'
os.makedirs(STORAGE_DIR, exist_ok=True)

# -- Initialize API --
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup:
    app.state.executor = ThreadPoolExecutor()
    app.state.langsmith_client = initialize_langsmith()  # Initialize LangSmith once
    yield
    # Shutdown:
    app.state.executor.shutdown(wait=True)

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Initialize Router --
from routers import audit, config, jobs, policies, reports, transcripts

app.include_router(config.router)
app.include_router(audit.router)
app.include_router(jobs.router)
app.include_router(policies.router)
app.include_router(transcripts.router)
app.include_router(reports.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
