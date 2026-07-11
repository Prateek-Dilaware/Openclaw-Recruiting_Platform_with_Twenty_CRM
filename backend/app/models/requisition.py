from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RequisitionBase(BaseModel):
    name: str
    jobTitle: str
    department: str
    jobDescription: str
    requiredSkills: str
    experience: str
    location: str
    employmentType: Optional[str] = "FULL_TIME"  # Enum: FULL_TIME, PART_TIME, INTERNSHIP
    status: Optional[str] = "OPEN"  # Enum: DRAFT, OPEN, IN_REVIEW, CLOSED, ON_HOLD
    listingId: Optional[str] = None  # Candidate relation

class RequisitionCreate(RequisitionBase):
    pass

class RequisitionUpdate(BaseModel):
    name: Optional[str] = None
    jobTitle: Optional[str] = None
    department: Optional[str] = None
    jobDescription: Optional[str] = None
    requiredSkills: Optional[str] = None
    experience: Optional[str] = None
    location: Optional[str] = None
    employmentType: Optional[str] = None
    status: Optional[str] = None
    listingId: Optional[str] = None

class RequisitionResponse(BaseModel):
    id: str
    name: str
    jobTitle: str
    department: str
    jobDescription: str
    requiredSkills: str
    experience: str
    location: str
    employmentType: Optional[str] = None
    status: Optional[str] = None
    listingId: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True
