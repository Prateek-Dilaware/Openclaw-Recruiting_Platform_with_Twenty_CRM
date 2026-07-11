from fastapi import APIRouter, HTTPException, Query, Form
from typing import List, Dict, Any, Optional
from fastapi.responses import FileResponse
from app.services.elevenlabs_service import ElevenLabsService
from app.settings import settings
import os
import uuid

router = APIRouter()
elevenlabs = ElevenLabsService()

@router.get("/config")
async def get_voice_config():
    return {
        "agent_id": settings.ELEVENLABS_AGENT_ID or "",
        "voice_id": settings.ELEVENLABS_VOICE_ID or ""
    }

@router.get("/voices")
async def get_voices():
    try:
        return elevenlabs.get_available_voices()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tts")
async def generate_speech(
    text: str = Form(...),
    voice_id: str = Form("EXAVITQu4vr4xnSDxMaL"),
    candidate_id: Optional[str] = Form(None)
):
    """Generates an invitation/reminder audio clip and returns the file path."""
    try:
        audio = elevenlabs.text_to_speech(text, voice_id)
        
        static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "static")
        os.makedirs(os.path.join(static_dir, "audio"), exist_ok=True)
        file_name = f"tts_{candidate_id or uuid.uuid4().hex}.mp3"
        audio_path = os.path.join(static_dir, "audio", file_name)
        
        elevenlabs.save_audio(audio, audio_path)
        
        return {
            "status": "success",
            "audio_url": f"/static/audio/{file_name}",
            "text": text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/outbound-call")
async def trigger_outbound_call(
    phone: str = Form(...),
    agent_id: str = Form(...)
):
    """Triggers an outbound ElevenLabs AI voice call to the candidate's phone."""
    try:
        result = await elevenlabs.start_outbound_call(phone, agent_id)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result.get("error"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/call-status/{call_id}")
async def get_call_status(call_id: str):
    try:
        return await elevenlabs.get_call_status(call_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_history():
    try:
        return await elevenlabs.list_history()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
