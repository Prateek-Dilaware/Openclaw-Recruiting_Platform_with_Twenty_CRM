import logging
from typing import Dict, Any
from pydantic import BaseModel
from app.services.llm_service import LLMService
from app.services.twenty_service import TwentyService
from app.utils.prompt_loader import load_prompt

logger = logging.getLogger(__name__)

class RetroOutput(BaseModel):
    decision: str  # Hire / No Hire
    strengths: str
    concerns: str
    areas_to_probe: str
    summary: str

class RetrospectiveAgent:
    def __init__(self):
        self.llm_service = LLMService()
        self.twenty_service = TwentyService()
        logger.info("RetrospectiveAgent initialized.")

    async def generate_retrospective(self, candidate_id: str) -> Dict[str, Any]:
        """
        Gathers candidate's screening transcript and score, analyzes alignment,
        produces a definitive Hiring Recommendation, and writes the decision to CRM.
        """
        logger.info(f"RetrospectiveAgent: Analyzing candidate {candidate_id} profile...")

        # 1. Fetch candidate's transcript and details from CRM
        candidate = await self.twenty_service.get_candidate(candidate_id)
        candidate_name = candidate.get("name", "Candidate")
        transcript = candidate.get("transcript", "")
        score = candidate.get("overallScore", 0.0)

        if not transcript:
            logger.warning("No transcript found for candidate. Proceeding with basic profiling.")
            transcript = "No voice interview transcript available."

        # 2. Load prompt and structure query
        base_prompt = load_prompt("retrospective_prompt.md")
        full_prompt = (
            f"{base_prompt}\n\n"
            f"Candidate Name: {candidate_name}\n"
            f"Initial Score: {score}/5.0\n"
            f"Interview Transcript:\n\"{transcript}\"\n\n"
            f"Provide a definitive 'Hire' or 'No Hire' decision under decision field, "
            f"compile strengths, concerns, and details for probe areas."
        )

        try:
            # 3. Query LLM
            retro_data = await self.llm_service.get_completion(
                prompt=full_prompt,
                system_message="You are a senior recruitment manager compiling final hiring retrospectives.",
                response_format=RetroOutput,
                mock_type="retrospective"
            )

            # 4. Set candidate's CRM status based on decision
            crm_status = "SHORLISTED" if "hire" in retro_data.decision.lower() and "no" not in retro_data.decision.lower() else "REJECTED"
            await self.twenty_service.update_candidate(candidate_id, {
                "interviewStatus": crm_status
            })

            # 5. Link retrospective note to candidate
            note_content = (
                f"FINAL DECISION: {retro_data.decision}\n\n"
                f"Summary: {retro_data.summary}\n\n"
                f"Strengths:\n{retro_data.strengths}\n\n"
                f"Concerns/Risks:\n{retro_data.concerns}\n\n"
                f"Probe Areas for Onsite Rounds:\n{retro_data.areas_to_probe}"
            )
            await self.twenty_service.add_note_to_candidate(
                candidate_id=candidate_id,
                title=f"Retrospective & Decision: {retro_data.decision}",
                content=note_content
            )

            # 6. Log activity
            await self.twenty_service.add_timeline_activity_to_candidate(
                candidate_id=candidate_id,
                title=f"Retrospective Decision: {retro_data.decision}",
                content=f"Hiring manager recommendation generated. Actioned candidate status to {crm_status}."
            )

            return {
                "status": "success",
                "decision": retro_data.decision,
                "summary": retro_data.summary,
                "strengths": retro_data.strengths,
                "concerns": retro_data.concerns,
                "areas_to_probe": retro_data.areas_to_probe,
                "crm_status_applied": crm_status
            }

        except Exception as e:
            logger.error(f"RetrospectiveAgent failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
