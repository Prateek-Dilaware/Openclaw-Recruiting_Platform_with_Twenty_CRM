from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Dict, Any, Optional
from app.models.candidate import CandidateCreate, CandidateUpdate, CandidateResponse
from app.services.twenty_service import TwentyService
from app.services.twenty_skill import TwentySkill
from app.services.elevenlabs_service import ElevenLabsService
from app.agents.scheduling_agent import SchedulingAgent
from app.agents.interview_agent import InterviewAgent
from app.agents.retrospective_agent import RetrospectiveAgent
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
twenty = TwentyService()
twenty_skill = TwentySkill()
elevenlabs = ElevenLabsService()
scheduling_agent = SchedulingAgent()
interview_agent = InterviewAgent()
retrospective_agent = RetrospectiveAgent()

@router.get("", response_model=List[CandidateResponse])
async def list_candidates():
    # Service call
    candidates = await twenty.get_candidates()
    try:
        requisitions = await twenty.get_requisitions()
        req_map = {}
        for r in requisitions:
            cid = r.get("listingId") or r.get("candidateId")
            if cid:
                if cid not in req_map:
                    req_map[cid] = []
                req_map[cid].append(r)
        for c in candidates:
            c["requisitions"] = req_map.get(c["id"], [])
    except Exception as e:
        logger.error(f"Failed to fetch linked requisitions for candidate list: {e}")
    return candidates

@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(candidate_id: str):
    try:
        candidate = await twenty.get_candidate(candidate_id)
        try:
            requisitions = await twenty.get_requisitions()
            candidate["requisitions"] = [r for r in requisitions if (r.get("listingId") or r.get("candidateId")) == candidate_id]
        except Exception as e:
            logger.error(f"Failed to fetch linked requisitions for candidate: {e}")
        return candidate
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("", response_model=CandidateResponse)
async def create_candidate(candidate: CandidateCreate):
    try:
        return await twenty.create_candidate(candidate.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(candidate_id: str, candidate: CandidateUpdate):
    try:
        return await twenty.update_candidate(candidate_id, candidate.model_dump(exclude_unset=True))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{candidate_id}")
async def delete_candidate(candidate_id: str):
    try:
        await twenty.delete_candidate(candidate_id)
        return {"status": "success", "message": "Candidate deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==========================================================
# Agent Integrations
# ==========================================================

@router.post("/{candidate_id}/schedule")
async def schedule_candidate_interview(
    candidate_id: str,
    candidate_availability: str = Form(...),
    interviewer_slots: str = Form(...),
    voice_id: Optional[str] = Form("EXAVITQu4vr4xnSDxMaL")
):
    """Triggers the Scheduling Agent to propose a slot and generate audio invite."""
    try:
        result = await scheduling_agent.schedule_interview(
            candidate_id=candidate_id,
            candidate_availability=candidate_availability,
            interviewer_slots=interviewer_slots,
            voice_id=voice_id
        )
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{candidate_id}/evaluate-screening")
async def evaluate_screening(
    candidate_id: str,
    file: UploadFile = File(...)
):
    """Triggers the Interview Agent to transcribe audio file and score response."""
    try:
        # Save uploaded file temporarily
        temp_dir = os.path.join(os.path.dirname(__file__), "..", "..", "static", "uploads")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"audio_{candidate_id}_{file.filename}")
        
        with open(temp_path, "wb") as f:
            f.write(await file.read())
            
        result = await interview_agent.evaluate_screening(
            candidate_id=candidate_id,
            audio_path=temp_path
        )
        
        # Clean up temp file
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass

        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{candidate_id}/retrospective")
async def run_candidate_retrospective(candidate_id: str):
    """Triggers the Retrospective Agent to generate hiring recommendation."""
    try:
        result = await retrospective_agent.generate_retrospective(
            candidate_id=candidate_id
        )
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{candidate_id}/trigger-outbound-call")
async def trigger_candidate_outbound_call(
    candidate_id: str,
    phone: str = Form(...),
    agent_id: str = Form(...)
):
    """Triggers an outbound ElevenLabs call to the candidate's phone."""
    try:
        # Fetch candidate details to check for associated requisition
        candidate = await twenty.get_candidate(candidate_id)
        
        # Look for target JD details in candidate's linked requisitions
        # Twenty's relation is represented as list in python objects
        cand_reqs = candidate.get("requisitions", [])
        job_desc = "Senior Developer Role with expertise in backend services, APIs, and databases."
        job_title = "Senior Developer"
        
        if cand_reqs and isinstance(cand_reqs, list) and len(cand_reqs) > 0:
            req_id = cand_reqs[0].get("id")
            if req_id:
                try:
                    req_details = await twenty.get_requisition(req_id)
                    job_desc = req_details.get("jobDescription") or job_desc
                    job_title = req_details.get("jobTitle") or job_title
                except Exception:
                    pass
                    
        # Truncate description slightly to keep payload compact
        job_desc_clean = job_desc.strip()[:1000]
        
        dynamic_vars = {
            "job_description": job_desc_clean,
            "job_title": job_title,
            "candidate_name": candidate.get("name", "Candidate")
        }
        
        logger.info(f"Outbound call candidate {candidate_id} with variables: {dynamic_vars}")
        
        result = await elevenlabs.start_outbound_call(phone, agent_id, dynamic_variables=dynamic_vars)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        call_id = result.get("call_id")
        
        # Log timeline activity to candidate in Twenty CRM
        await twenty.add_timeline_activity_to_candidate(
            candidate_id=candidate_id,
            title="Outbound Voice Screening Started",
            content=f"ElevenLabs Call ID: {call_id} initiated to {phone}."
        )
        
        # Update candidate status to SCREENING using Skill
        await twenty_skill.trigger_workflow(
            workflow_name_or_id="Candidate Status Change",
            record_id=candidate_id,
            target_status="SCREENING",
            object_name="candidate"
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{candidate_id}/fetch-latest-web-transcript")
async def fetch_latest_web_transcript(
    candidate_id: str,
    agent_id: str = Form(...)
):
    """Retrieves the most recent conversation transcript for the agent from ElevenLabs, evaluates and saves it."""
    try:
        conv_id = await elevenlabs.get_latest_agent_conversation_id(agent_id)
        if not conv_id:
            raise HTTPException(
                status_code=400,
                detail=f"No conversations found for Agent ID: '{agent_id}' on ElevenLabs."
            )
            
        transcript = await elevenlabs.get_conversation_transcript(conv_id)
        if not transcript or len(transcript.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail=f"Conversation found ({conv_id}) but it contains no dialogue turns yet."
            )
            
        logger.info(f"Retrieved web mic transcript for {candidate_id} (Conv ID: {conv_id})")
        
        result = await interview_agent.evaluate_transcript(candidate_id, transcript)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
            
        return {**result, "conversation_id": conv_id}
    except Exception as e:
        logger.error(f"Failed to fetch web transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{candidate_id}/fetch-call-evaluation")
async def fetch_and_evaluate_call(
    candidate_id: str,
    call_id: str = Form(...)
):
    """Retrieves call details and transcript from ElevenLabs, evaluates and saves to Twenty CRM."""
    try:
        # Fetch call status and transcript
        call_status = await elevenlabs.get_call_status(call_id)
        if "error" in call_status:
            raise HTTPException(status_code=400, detail=call_status.get("error"))
        
        transcript = call_status.get("transcript", "")
        if not transcript:
            status = call_status.get("status", "unknown")
            if status != "completed":
                raise HTTPException(
                    status_code=400, 
                    detail=f"Call is still in status: '{status}'. Please wait until the call is completed."
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Call was completed but no transcript was returned by ElevenLabs."
                )
        
        # Run transcript evaluation
        result = await interview_agent.evaluate_transcript(candidate_id, transcript)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
