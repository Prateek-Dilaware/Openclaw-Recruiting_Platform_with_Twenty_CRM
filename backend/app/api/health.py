from fastapi import APIRouter, HTTPException
from app.services.retrospective_job import RetrospectiveJob

router = APIRouter()
retrospective_job = RetrospectiveJob()

@router.get("")
async def health_check():
    return {"status": "healthy"}

@router.post("/run-retrospective")
async def trigger_retrospective_audit():
    """Triggers the weekly retrospective job to audit pipeline overrides and generate suggestions."""
    try:
        result = await retrospective_job.run_weekly_audit()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
