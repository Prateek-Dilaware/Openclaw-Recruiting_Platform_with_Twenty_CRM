import logging
import re
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from typing import Dict, Any
from app.services.twenty_service import TwentyService
from app.services.crm_service import CRMService
from app.services.elevenlabs_service import ElevenLabsService
from backend.archieve.interview_agent import InterviewAgent
from app.agents.jd_agent import JDAgent
from app.agents.scheduling_agent import SchedulingAgent
from app.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

twenty = TwentyService()
twenty_skill = CRMService()
elevenlabs = ElevenLabsService()
interview_agent = InterviewAgent()
jd_agent = JDAgent()
scheduling_agent = SchedulingAgent()

def clean_phone(phone_str: str) -> str:
    """Normalize phone number to digits only for comparison."""
    if not phone_str:
        return ""
    return "".join(c for c in phone_str if c.isdigit())

async def run_requisition_pipeline(record_id: str):
    """Heavy background processing task for Requisition status update."""
    try:
        # Fetch requisition details
        requisition = await twenty.get_requisition(record_id)
        status = requisition.get("status")
        job_title = requisition.get("jobTitle") or requisition.get("name") or "Position"
        
        logger.info(f"[Background Task] Requisition {record_id} ({job_title}) is in status '{status}'")
        
        if status in ("OPEN", "READY", "ready", "open"):
            # Check if detailed JD is already generated to avoid loops
            desc = requisition.get("jobDescription") or ""
            if not desc.startswith("# Job Opportunity") and not desc.startswith("Role:"):
                logger.info(f"[Background Task] Requisition {record_id} ready. Running JD agent...")
                await jd_agent.generate_description_from_requisition(record_id)
            
            # Fetch candidates in APPLIED status and run scheduling agent
            candidates = await twenty.get_candidates()
            applied_candidates = [c for c in candidates if c.get("interviewStatus") == "APPLIED"]
            
            logger.info(f"[Background Task] Found {len(applied_candidates)} applied candidates. Triggering Scheduling Agent...")
            for cand in applied_candidates:
                cand_id = cand["id"]
                cand_name = cand.get("name", "Candidate")
                logger.info(f"[Background Task] Scheduling interview for {cand_name} (Candidate ID: {cand_id})...")
                
                # Execute scheduling agent (transitions candidate to INTERVIEW_SCHEDULED)
                await scheduling_agent.schedule_interview(
                    candidate_id=cand_id,
                    candidate_availability="Mondays 2 PM - 5 PM",
                    interviewer_slots="Monday July 20th 2 PM - 5 PM"
                )
    except Exception as e:
        logger.error(f"[Background Task] Error running requisition pipeline: {e}")

@router.post("")
async def receive_crm_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Listens to Twenty CRM webhook notifications.
    Uses BackgroundTasks to process heavy agent operations asynchronously to avoid timeouts.
    """
    try:
        payload = await request.json()
        logger.info(f"Received Twenty CRM Webhook Event: {payload.get('type') or 'Generic Update'}")
        
        action = payload.get("action")
        object_name = payload.get("objectName")
        record_id = payload.get("recordId")
        
        logger.info(f"Webhook Activity Details -> Action: {action}, Object: {object_name}, Record ID: {record_id}")
        
        # 1. Handle Requisition Update to OPEN
        if object_name in ("requistion", "requisition") and action == "updated":
            # Queue to background
            background_tasks.add_task(run_requisition_pipeline, record_id)
            return {
                "status": "enqueued_requisition_pipeline",
                "requisition_id": record_id
            }

        # 2. Log Candidate status updates (Call is triggered manually from frontend, not auto-called)
        elif object_name == "candidate" and action == "updated":
            candidate = await twenty.get_candidate(record_id)
            status = candidate.get("interviewStatus")
            logger.info(f"Candidate {record_id} transitioned to stage: {status}")
            return {
                "status": "logged_candidate_update",
                "candidate_id": record_id,
                "stage": status
            }
            
        return {
            "status": "received",
            "action": action,
            "object": object_name,
            "recordId": record_id
        }
    except Exception as e:
        logger.error(f"Error processing CRM webhook: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/elevenlabs")
async def receive_elevenlabs_webhook(request: Request):
    """
    Listens to ElevenLabs post-call webhook events.
    Parses conversational results and writes them back into Twenty CRM using the Twenty Skill.
    """
    try:
        payload = await request.json()
        logger.info(f"Received ElevenLabs Webhook event: {payload.get('event') or 'Call Update'}")
        
        # ElevenLabs Conversational AI completed event fields
        conversation = payload.get("conversation", {})
        call_id = conversation.get("call_id") or payload.get("call_id")
        raw_phone = conversation.get("phone_number") or payload.get("phone_number") or ""
        
        # Extract transcript
        transcript_data = conversation.get("transcript") or payload.get("transcript") or ""
        transcript_text = ""
        if isinstance(transcript_data, list):
            # Parse list of dialogue messages
            dialogue = []
            for msg in transcript_data:
                role = msg.get("role", "unknown").capitalize()
                message = msg.get("message", "")
                dialogue.append(f"{role}: {message}")
            transcript_text = "\n".join(dialogue)
        else:
            transcript_text = str(transcript_data)
            
        analysis = conversation.get("analysis") or payload.get("analysis") or {}
        data_collection = analysis.get("data_collection_results") or {}
        
        # Overall score
        score = None
        for key in ("overallScore", "overall_score", "score", "rating"):
            if key in data_collection:
                score = float(data_collection[key])
                break
        
        # Sentiment
        sentiment = analysis.get("sentiment") or "NEUTRAL"
        sentiment = sentiment.upper().replace(" ", "_")
        if sentiment not in ("VERY_POSITIVE", "POSITIVE", "NEUTRAL", "NEGATIVE", "VERY_NEGATIVE"):
            sentiment = "NEUTRAL"
            
        summary = analysis.get("transcript_summary") or "Voice screening call completed."
        
        logger.info(f"ElevenLabs Webhook Parsed Details -> Call ID: {call_id}, Phone: {raw_phone}, Score: {score}, Sentiment: {sentiment}")
        
        if not raw_phone:
            logger.error("No phone number returned in webhook. Cannot resolve candidate.")
            raise HTTPException(status_code=400, detail="Missing phone number in webhook payload.")
            
        # Match candidate by phone number normalization
        candidates = await twenty.get_candidates()
        target_candidate = None
        webhook_phone_digits = clean_phone(raw_phone)
        
        for cand in candidates:
            cand_phone_obj = cand.get("phone", {})
            cand_phone = ""
            if isinstance(cand_phone_obj, dict):
                cand_phone = cand_phone_obj.get("primaryPhoneNumber") or ""
            elif isinstance(cand_phone_obj, str):
                cand_phone = cand_phone_obj
                
            if clean_phone(cand_phone) == webhook_phone_digits:
                target_candidate = cand
                break
                
        if not target_candidate:
            # Try matching last 10 digits as fallback
            for cand in candidates:
                cand_phone_obj = cand.get("phone", {})
                cand_phone = ""
                if isinstance(cand_phone_obj, dict):
                    cand_phone = cand_phone_obj.get("primaryPhoneNumber") or ""
                elif isinstance(cand_phone_obj, str):
                    cand_phone = cand_phone_obj
                    
                cand_digits = clean_phone(cand_phone)
                if cand_digits and webhook_phone_digits and cand_digits[-10:] == webhook_phone_digits[-10:]:
                    target_candidate = cand
                    break
                    
        if not target_candidate:
            logger.error(f"Could not map phone {raw_phone} to any candidate in CRM.")
            return {"status": "ignored", "reason": "Candidate not found"}
            
        candidate_id = target_candidate["id"]
        logger.info(f"Matched Call ID {call_id} to Candidate {target_candidate.get('name')} (ID: {candidate_id})")
        
        # If the transcript is present but the score is not set by ElevenLabs, use InterviewAgent to evaluate
        if transcript_text and score is None:
            logger.info("ElevenLabs did not return a score. Invoking InterviewAgent LLM evaluator on transcript...")
            eval_result = await interview_agent.evaluate_transcript(candidate_id, transcript_text)
            return {
                "status": "processed_via_agent",
                "candidate_id": candidate_id,
                "evaluation": eval_result
            }
        
        # Else directly write fields back via CRM Skill
        await twenty_skill.write_field("candidate", candidate_id, "transcript", transcript_text)
        if score is not None:
            await twenty_skill.write_field("candidate", candidate_id, "overallScore", score)
        await twenty_skill.write_field("candidate", candidate_id, "sentiment", sentiment)
        
        # Write notes and logs
        note_content = (
            f"Voice Call Summary: {summary}\n\n"
            f"Sentiment: {sentiment}\n"
            f"Overall Score: {score if score is not None else 'N/A'}/5.0\n\n"
            f"Call Transcript:\n{transcript_text}"
        )
        await twenty_skill.write_field("candidate", candidate_id, "note", {
            "title": f"ElevenLabs Post-Call Screening Report (Call ID: {call_id})",
            "content": note_content
        })
        
        await twenty.add_timeline_activity_to_candidate(
            candidate_id=candidate_id,
            title="Screening Call Analysis Completed",
            content=f"Analysis of outbound call ID {call_id} saved to candidate profile."
        )

        # Transition candidate status via workflow
        target_status = "SHORLISTED" if (score is not None and score >= 4.0) else "INTERVIEW_COMPLETED"
        await twenty_skill.trigger_workflow(
            workflow_name_or_id="Candidate Status Change",
            record_id=candidate_id,
            target_status=target_status,
            object_name="candidate"
        )
        
        return {
            "status": "processed_directly",
            "candidate_id": candidate_id,
            "overallScore": score,
            "sentiment": sentiment,
            "status_applied": target_status
        }
    except Exception as e:
        logger.error(f"Error processing ElevenLabs webhook: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/workflow-trigger")
async def receive_workflow_trigger(request: Request):
    """
    Receives trigger from Twenty CRM workflow automation
    and initiates outbound interview call via ElevenLabs.
    """
    try:
        payload = await request.json()
        candidate_id = payload.get("candidate_id")
        phone = payload.get("phone")
        candidate_name = payload.get("name")
        
        logger.info(f"Workflow trigger received for candidate {candidate_id} ({candidate_name})")
        
        if not candidate_id or not phone:
            raise HTTPException(status_code=400, detail="Missing candidate_id or phone")
        
        # Get ElevenLabs agent ID from settings
        agent_id = getattr(settings, 'ELEVENLABS_AGENT_ID', '')
        
        if not agent_id:
            raise HTTPException(status_code=500, detail="ELEVENLABS_AGENT_ID not configured")
        
        # Get candidate's linked requisition for job context
        candidate = await twenty.get_candidate(candidate_id)
        job_title = "Senior Developer"
        job_description = "Senior developer role"
        
        try:
            requisitions = await twenty.get_requisitions()
            linked_reqs = [r for r in requisitions if (r.get("listingId") or r.get("candidateId")) == candidate_id]
            if linked_reqs:
                req = linked_reqs[0]
                job_title = req.get("jobTitle", job_title)
                job_description = req.get("jobDescription", job_description)
        except Exception as e:
            logger.warning(f"Could not fetch requisition details: {e}")
        
        # Prepare dynamic variables for ElevenLabs
        dynamic_vars = {
            "job_description": job_description[:1000],
            "job_title": job_title,
            "candidate_name": candidate_name or "Candidate"
        }
        
        # Trigger outbound call via ElevenLabs
        call_result = await elevenlabs.start_outbound_call(phone, agent_id, dynamic_variables=dynamic_vars)
        
        if "error" in call_result:
            raise HTTPException(status_code=400, detail=call_result.get("error"))
        
        call_id = call_result.get("call_id")
        
        # Log timeline activity
        await twenty.add_timeline_activity_to_candidate(
            candidate_id=candidate_id,
            title="Automated Outbound Call Triggered",
            content=f"Call ID: {call_id} initiated via workflow automation"
        )
        
        # Update candidate status to SCREENING
        await twenty_skill.trigger_workflow(
            workflow_name_or_id="Candidate Status Change",
            record_id=candidate_id,
            target_status="SCREENING",
            object_name="candidate"
        )
        
        return {
            "status": "success",
            "call_id": call_id,
            "candidate_id": candidate_id,
            "message": "Outbound call triggered via workflow automation"
        }
        
    except Exception as e:
        logger.error(f"Error processing workflow trigger: {e}")
        raise HTTPException(status_code=500, detail=str(e))

