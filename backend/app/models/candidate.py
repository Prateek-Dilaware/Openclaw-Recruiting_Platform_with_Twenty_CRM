from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class CandidateBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    resumeUrl: Optional[str] = None
    interviewStatus: Optional[str] = "APPLIED"  # Enum: APPLIED, SCREENING, INTERVIEW_SCHEDULED, INTERVIEW_COMPLETED, SHORLISTED, REJECTED, HIRED

class CandidateCreate(CandidateBase):
    pass

class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    resumeUrl: Optional[str] = None
    overallScore: Optional[float] = None
    transcript: Optional[str] = None
    sentiment: Optional[str] = None
    interviewStatus: Optional[str] = None

class CandidateResponse(BaseModel):
    id: str
    name: str
    email: Optional[Dict[str, Any]] = None
    phone: Optional[Dict[str, Any]] = None
    resumeUrl: Optional[str] = None
    overallScore: Optional[float] = None
    transcript: Optional[str] = None
    sentiment: Optional[str] = None
    interviewStatus: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    requisitions: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True
