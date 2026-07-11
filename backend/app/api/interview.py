from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.models.interview import InterviewCreate, InterviewResponse
from app.services.twenty_service import TwentyService

router = APIRouter()
twenty = TwentyService()

@router.get("", response_model=List[InterviewResponse])
async def list_interviews():
    return await twenty.get_interviews()

@router.get("/{interview_id}", response_model=InterviewResponse)
async def get_interview(interview_id: str):
    try:
        return await twenty.get_interview(interview_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("", response_model=InterviewResponse)
async def create_interview(interview: InterviewCreate):
    try:
        return await twenty.create_interview(interview.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{interview_id}")
async def delete_interview(interview_id: str):
    try:
        await twenty.delete_interview(interview_id)
        return {"status": "success", "message": "Interview deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
