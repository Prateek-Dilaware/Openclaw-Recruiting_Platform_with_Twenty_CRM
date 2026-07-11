from fastapi import APIRouter, HTTPException, Form
from typing import List, Dict, Any
from app.models.requisition import RequisitionCreate, RequisitionUpdate, RequisitionResponse
from app.services.twenty_service import TwentyService
from app.agents.jd_agent import JDAgent

router = APIRouter()
twenty = TwentyService()
jd_agent = JDAgent()

@router.get("", response_model=List[RequisitionResponse])
async def list_requisitions():
    return await twenty.get_requisitions()

@router.get("/{requisition_id}", response_model=RequisitionResponse)
async def get_requisition(requisition_id: str):
    try:
        return await twenty.get_requisition(requisition_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("", response_model=RequisitionResponse)
async def create_requisition(req: RequisitionCreate):
    try:
        return await twenty.create_requisition(req.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{requisition_id}", response_model=RequisitionResponse)
async def update_requisition(requisition_id: str, req: RequisitionUpdate):
    try:
        return await twenty.update_requisition(requisition_id, req.model_dump(exclude_unset=True))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{requisition_id}")
async def delete_requisition(requisition_id: str):
    try:
        await twenty.delete_requisition(requisition_id)
        return {"status": "success", "message": "Requisition deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/parse-jd")
async def parse_job_description(
    requirements: str = Form(...)
):
    """Triggers the JD Agent to structure manager requirements and auto-create Requisition in CRM."""
    try:
        # Run agent task to parse and structure raw JD text
        structured_data = await jd_agent.generate_job_description(
            requirements=requirements
        )
        
        # Create requisition record in CRM using parsed structure
        created_requisition = await twenty.create_requisition(structured_data)
        return {
            "status": "success",
            "parsed_structure": structured_data,
            "requisition": created_requisition
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{requisition_id}/generate-jd")
async def generate_requisition_job_description(requisition_id: str):
    """Triggers the JD agent to generate and write back a detailed job description from an existing Requisition."""
    try:
        jd_text = await jd_agent.generate_description_from_requisition(requisition_id)
        return {
            "status": "success",
            "requisition_id": requisition_id,
            "jobDescription": jd_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
