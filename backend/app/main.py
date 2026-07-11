from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api.candidate import router as candidate_router
from app.api.requistion import router as requisition_router
from app.api.interview import router as interview_router
from app.api.voice import router as voice_router
from app.api.webhook import router as webhook_router
from app.api.health import router as health_router

app = FastAPI(
    title="OpenClaw Recruiting Platform",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local development sandbox
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static/audio directories exist for generated voice screen clips
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
os.makedirs(os.path.join(static_dir, "audio"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "uploads"), exist_ok=True)

# Mount static folder
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Register routes under v1 prefix
app.include_router(candidate_router, prefix="/api/v1/candidates", tags=["Candidates"])
app.include_router(requisition_router, prefix="/api/v1/requisitions", tags=["Requisitions"])
app.include_router(interview_router, prefix="/api/v1/interviews", tags=["Interviews"])
app.include_router(voice_router, prefix="/api/v1/voice", tags=["Voice"])
app.include_router(webhook_router, prefix="/api/v1/webhooks", tags=["Webhooks"])
app.include_router(health_router, prefix="/api/v1/health", tags=["Health"])

@app.get("/")
async def root():
    return {
        "message": "OpenClaw Recruiting Platform API is running.",
        "docs_url": "/docs"
    }