import re
import os
import logging
from typing import List, Dict, Any
from app.services.twenty_service import TwentyService
from app.services.llm_service import LLMService
from app.settings import settings

logger = logging.getLogger(__name__)

class RetrospectiveJob:
    def __init__(self):
        self.twenty = TwentyService()
        self.llm = LLMService()

    async def run_weekly_audit(self) -> Dict[str, Any]:
        """
        Scans all candidates, correlates notes to find original agent decisions,
        identifies overrides by humans, uses LLM to propose adjustments,
        and logs proposals to a markdown file.
        """
        logger.info("Running Weekly Retrospective Audit Job...")
        
        try:
            # 1. Fetch candidates, notes, and targets
            candidates = await self.twenty.get_candidates()
            notes_response = await self.twenty._request("GET", "notes")
            notes = notes_response.get("data", {}).get("notes", [])
            
            targets_response = await self.twenty._request("GET", "noteTargets")
            targets = targets_response.get("data", {}).get("noteTargets", [])
        except Exception as err:
            logger.error(f"Failed to fetch CRM records for audit: {err}")
            raise err
        
        # Map note ID to note content/title
        notes_map = {n["id"]: n for n in notes}
        
        # Map candidate ID to notes list
        candidate_notes: Dict[str, List[Dict[str, Any]]] = {}
        for t in targets:
            c_id = t.get("targetCandidateId")
            n_id = t.get("noteId")
            if c_id and n_id and n_id in notes_map:
                if c_id not in candidate_notes:
                    candidate_notes[c_id] = []
                candidate_notes[c_id].append(notes_map[n_id])
                
        overrides = []
        
        # 2. Analyze each candidate for overrides
        for cand in candidates:
            cand_id = cand["id"]
            cand_name = cand.get("name", "Unknown Candidate")
            current_score = cand.get("overallScore")
            current_status = cand.get("interviewStatus")
            
            # Find AI screening evaluation note
            cand_notes = candidate_notes.get(cand_id, [])
            ai_note = None
            for n in cand_notes:
                title = n.get("title") or ""
                if "AI Screening Evaluation Report" in title or "Screening Report" in title:
                    ai_note = n
                    break
                    
            if not ai_note:
                continue
                
            # Parse original agent score from note body
            body_v2 = ai_note.get("bodyV2", {})
            markdown_content = ""
            if isinstance(body_v2, dict):
                markdown_content = body_v2.get("markdown") or ""
            
            score_match = re.search(r"Overall Score:\s*([\d\.]+)", markdown_content)
            original_score = None
            if score_match:
                try:
                    original_score = float(score_match.group(1))
                except ValueError:
                    pass
                    
            if original_score is None:
                continue
                
            # Check for score discrepancy
            score_override = False
            if current_score is not None and abs(current_score - original_score) > 0.01:
                score_override = True
                
            # Check for status threshold discrepancy (Expected: Shortlisted if score >= 4.0)
            expected_status = "SHORLISTED" if original_score >= 4.0 else "REJECTED"
            status_override = False
            
            if expected_status == "SHORLISTED" and current_status in ("REJECTED", "OPTION_8"):
                status_override = True
            elif expected_status == "REJECTED" and current_status in ("SHORLISTED", "HIRED"):
                status_override = True
                
            if score_override or status_override:
                overrides.append({
                    "candidate_id": cand_id,
                    "name": cand_name,
                    "original_score": original_score,
                    "current_score": current_score,
                    "original_recommendation": expected_status,
                    "current_status": current_status,
                    "transcript": cand.get("transcript", "No transcript available."),
                    "override_type": "Score & Status" if (score_override and status_override) else ("Score" if score_override else "Status")
                })
                
        # 3. Use LLM to analyze patterns and propose adjustments
        if not overrides:
            logger.info("No human overrides detected. Pipeline aligned.")
            proposal_text = (
                "# Weekly Retrospective Proposals\n\n"
                "No human overrides or corrections were detected in this audit window. "
                "The AI recruitment pipeline remains fully aligned with hiring manager decisions."
            )
        else:
            logger.info(f"Detected {len(overrides)} human overrides. Querying LLM analysis...")
            cases_str = ""
            for idx, c in enumerate(overrides, 1):
                cases_str += (
                    f"### Case {idx}: {c['name']}\n"
                    f"- Override Type: {c['override_type']}\n"
                    f"- Agent Original Score: {c['original_score']} (Expected: {c['original_recommendation']})\n"
                    f"- Human Final Score: {c['current_score']} | Final Status: {c['current_status']}\n"
                    f"- Candidate Transcript:\n\"{c['transcript']}\"\n\n"
                )
                
            prompt = (
                "Review the following human override/correction cases where recruiting managers modified the AI agent's scores or pipeline statuses. "
                "Synthesize feedback patterns and propose adjustments (such as screening question prompt modifications or score threshold shifts) to align "
                "the autonomous recruitment agents with human hiring criteria.\n\n"
                "YOUR PROPOSALS ARE FOR HUMAN REVIEW ONLY AND WILL NOT BE AUTO-APPLIED.\n\n"
                f"{cases_str}\n"
                "Format your proposals as a clean markdown report containing: Executive Summary, Observed Discrepancies, and Recommended Agent Prompt/Threshold Adjustments."
            )
            
            try:
                proposal_text = await self.llm.get_completion(
                    prompt=prompt,
                    system_message="You are a senior principal recruitment auditor compiling pipeline tuning proposals.",
                    mock_type="retrospective_audit"
                )
            except Exception as llm_err:
                logger.error(f"LLM critique failed: {llm_err}")
                proposal_text = f"# Weekly Retrospective Proposals\n\nDetected {len(overrides)} overrides. Failed to run LLM critique."

        # 4. Save proposals to local file in the conversation artifacts directory
        artifact_path = r"C:\Users\Dice\.gemini\antigravity-ide\brain\a5c8389f-aa52-4820-9639-8cd86cf2f098\weekly_retrospective_proposals.md"
        
        try:
            os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
            with open(artifact_path, "w", encoding="utf-8") as f:
                f.write(proposal_text)
            logger.info(f"Retrospective proposals saved to: {artifact_path}")
        except Exception as io_err:
            logger.error(f"Failed to write proposals file: {io_err}")

        # 5. Log the proposal run as a generic Note in Twenty CRM for audit trail
        try:
            await self.twenty.create_note(
                "Weekly Retrospective Audit Run Complete",
                f"Retrospective audit job completed. Identified {len(overrides)} overrides. Detailed proposals saved locally."
            )
        except Exception as note_err:
            logger.error(f"Failed to save retrospective note in CRM: {note_err}")
            
        return {
            "status": "completed",
            "overrides_detected": len(overrides),
            "proposal_filepath": artifact_path,
            "proposals": proposal_text
        }
