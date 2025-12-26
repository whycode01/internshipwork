import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- Router Setup ---
from routers import v1

# --- Configuration ---
HOST = "0.0.0.0"
PORT = 8001

# --- FastAPI Application ---
app = FastAPI(
    title="Text Anonymization API",
    description="An API to anonymize and deanonymize text.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1.router)

# --- Health Check Endpoint ---
@app.get("/api/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return {"status": "ok"}

# --- Start ---
if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)