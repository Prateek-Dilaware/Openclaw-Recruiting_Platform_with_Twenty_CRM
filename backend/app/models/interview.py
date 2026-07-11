from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class InterviewBase(BaseModel):
    name: str
    candidateId: str

class InterviewCreate(InterviewBase):
    pass

class InterviewResponse(BaseModel):
    id: str
    name: str
    candidateId: str
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True
