import logging
from typing import Dict, Any
from pydantic import BaseModel
from app.services.llm_service import LLMService
from app.services.crm_service import CRMService
from app.utils.prompt_loader import load_prompt

logger = logging.getLogger(__name__)

class SchedulingOutput(BaseModel):
    date: str
    start_time: str
    end_time: str
    reason: str
    outreach_script: str

class SchedulingAgent:
    def __init__(self):
        self.llm_service = LLMService()
        self.twenty_skill = CRMService()
        logger.info("SchedulingAgent initialized.")

    async def schedule_interview(
        self,
        candidate_id: str,
        candidate_availability: str,
        interviewer_slots: str,
        voice_id: str = "EXAVITQu4vr4xnSDxMaL"
    ) -> Dict[str, Any]:
        """
        Proposes an interview slot, creates the interview record,
        and transitions the status to INTERVIEW_SCHEDULED via a Twenty workflow.
        Does NOT call ElevenLabs directly (it is fully decoupled).
        """
        logger.info(f"SchedulingAgent: Scheduling interview for candidate {candidate_id}...")
        
        # Load candidate details
        candidate = await self.twenty_skill.twenty_service.get_candidate(candidate_id)
        candidate_name = candidate.get("name", "Candidate")

        # Load prompt and analyze optimal slots
        base_prompt = load_prompt("scheduling_prompt.md")
        full_prompt = (
            f"{base_prompt}\n\n"
            f"Candidate Name: {candidate_name}\n"
            f"Candidate Availability:\n{candidate_availability}\n\n"
            f"Interviewer Calendar Slots:\n{interviewer_slots}\n\n"
            f"Propose a matching slot and write an outreach script."
        )

        try:
            # Query LLM to match slots
            schedule_data = await self.llm_service.get_completion(
                prompt=full_prompt,
                system_message="You are an expert AI scheduling assistant.",
                response_format=SchedulingOutput,
                mock_type="scheduling"
            )
            
            # 1. Create Interview record in Twenty CRM
            interview_name = f"Voice Screening - {candidate_name} ({schedule_data.date})"
            interview_record = await self.twenty_skill.twenty_service.create_interview({
                "name": interview_name,
                "candidateId": candidate_id
            })
            interview_id = interview_record.get("id")

            # 2. Write proposed slots and script to candidate's notes using Twenty Skill
            note_content = (
                f"Proposed Slot: {schedule_data.date} at {schedule_data.start_time} - {schedule_data.end_time}.\n"
                f"Reasoning: {schedule_data.reason}\n\n"
                f"Generated Outreach Script:\n{schedule_data.outreach_script}"
            )
            await self.twenty_skill.write_field(
                object_name="candidate",
                record_id=candidate_id,
                field_name="note",
                value={
                    "title": f"Scheduling Outreach Details for {schedule_data.date}",
                    "content": note_content
                }
            )

            # 3. Transition candidate status to INTERVIEW_SCHEDULED via Twenty workflow
            # This triggers the outbound calling webhook automation.
            await self.twenty_skill.trigger_workflow(
                workflow_name_or_id="Candidate Status Change",
                record_id=candidate_id,
                target_status="INTERVIEW_SCHEDULED",
                object_name="candidate"
            )

            return {
                "status": "success",
                "interview_id": interview_id,
                "date": schedule_data.date,
                "start_time": schedule_data.start_time,
                "end_time": schedule_data.end_time,
                "reason": schedule_data.reason,
                "outreach_script": schedule_data.outreach_script,
                "workflow_triggered": True
            }

        except Exception as e:
            logger.error(f"SchedulingAgent failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
