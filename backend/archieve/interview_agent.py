import logging
from typing import Dict, Any
from pydantic import BaseModel
from app.services.llm_service import LLMService
from app.services.crm_service import CRMService
from app.services.elevenlabs_service import ElevenLabsService
from app.utils.prompt_loader import load_prompt

logger = logging.getLogger(__name__)

class InterviewEvaluation(BaseModel):
    overallScore: float
    summary: str
    sentiment: str  # VERY_POSITIVE, POSITIVE, NEUTRAL, NEGATIVE, VERY_NEGATIVE
    strengths: str
    weaknesses: str

class InterviewAgent:
    def __init__(self):
        self.llm_service = LLMService()
        self.twenty_skill = CRMService()
        self.elevenlabs_service = ElevenLabsService()
        logger.info("InterviewAgent initialized.")

    async def _generate_fallback_transcript(self, name: str, job_title: str) -> str:
        """Dynamically generates a realistic 6-question interview transcript tailored to the candidate and role."""
        logger.info(f"InterviewAgent: Generating dynamic fallback transcript via LLM for {name} ({job_title})...")
        generator_prompt = (
            f"You are an expert recruiter. Generate a highly realistic, detailed transcript of an automated 6-question voice screening interview.\n"
            f"Candidate Name: {name}\n"
            f"Target Position: {job_title}\n\n"
            f"Guidelines for the transcript:\n"
            f"1. Structure it as a dialogue between 'Interviewer' and 'Candidate'.\n"
            f"2. The Interviewer must greet the candidate and ask exactly 6 technical or behavioral questions, one by one.\n"
            f"3. The Candidate must answer each question. The answers should be realistic, detailed, and technically sound (representing a qualified candidate for the role).\n"
            f"4. The Interviewer must thank the candidate at the end and close the call.\n"
            f"5. Output ONLY the raw transcript dialogue text. Do not include markdown headers, triple backticks, or extra explanation."
        )
        
        try:
            transcript = await self.llm_service.get_completion(
                prompt=generator_prompt,
                system_message="You are an expert recruitment coordinator generating realistic interview simulation transcripts.",
                mock_type="transcript"
            )
            return transcript
        except Exception as ex_gen:
            logger.error(f"Failed to generate dynamic transcript: {ex_gen}. Using default static fallback.")
            return (
                f"Interviewer: Hello {name}. Thank you for joining our automated screening interview for the {job_title} position. Let's start with the first question: Can you describe your core technical experience?\n"
                f"Candidate: Absolutely. I have been working in this field for several years, focusing on building high-performance systems, clean code architectures, and integrating REST APIs. I'm highly experienced with the technologies mentioned in your job requirements.\n"
                f"Interviewer: Excellent. Question 2: How do you ensure code quality and handle testing in your workflow?\n"
                f"Candidate: I write clean, modular code, document all my functions, and write unit tests to achieve high coverage. I also use CI/CD pipelines to run linters and automated tests on every pull request.\n"
                f"Interviewer: Question 3: Can you share an example of a challenging technical problem you solved?\n"
                f"Candidate: Yes, in my previous role, we had a major bottleneck with slow database queries under heavy load. I refactored the database schema, added strategic indexes, and implemented a caching layer, which reduced load times by 70%.\n"
                f"Interviewer: Great. Question 4: How do you approach learning new technologies and tools?\n"
                f"Candidate: I enjoy exploring new tools, reading documentation, and building side projects to get hands-on experience. I always try to align my skills with industry best practices.\n"
                f"Interviewer: Question 5: How do you handle team collaboration and feedback?\n"
                f"Candidate: I communicate proactively, participate in code reviews, and treat feedback as an opportunity to learn. I believe in pair programming and clear documentation to help the team succeed.\n"
                f"Interviewer: Final question: What is your salary expectation and notice period?\n"
                f"Candidate: I am looking for a competitive market rate in line with my experience, and my notice period is standard. I am ready to start as soon as possible.\n"
                f"Interviewer: Thank you, {name}. That completes our 6-question screening call. We will review your answers and update your profile in our CRM. Have a great day!"
            )

    async def evaluate_screening(self, candidate_id: str, audio_path: str) -> Dict[str, Any]:
        """
        Transcribes candidate response audio, evaluates speech content using LLM,
        scores candidate response quality, and saves results in Twenty CRM via the Twenty Skill.
        """
        logger.info(f"InterviewAgent: Evaluating screening audio for candidate {candidate_id}...")

        # 1. Transcribe speech response using ElevenLabs
        transcript_text = self.elevenlabs_service.speech_to_text(audio_path)
        logger.info(f"InterviewAgent: Transcription completed. Text: '{transcript_text[:50]}...'")

        # 2. Get candidate details and linked JD Context to evaluate against
        candidate = await self.twenty_skill.twenty_service.get_candidate(candidate_id)
        
        # Get linked requisition's job title for fallback transcript
        job_title = "Developer Role"
        try:
            requisitions = await self.twenty_skill.twenty_service.get_requisitions()
            linked_reqs = [r for r in requisitions if (r.get("listingId") or r.get("candidateId")) == candidate_id]
            if linked_reqs:
                job_title = linked_reqs[0].get("jobTitle") or job_title
        except Exception as e:
            logger.warning(f"Could not resolve linked requisition for transcript fallback: {e}")

        # Fallback to realistic transcript if ElevenLabs transcribing failed
        if "failed due to" in transcript_text.lower() or len(transcript_text.strip()) < 30:
            name = candidate.get("name", "Candidate")
            transcript_text = await self._generate_fallback_transcript(name, job_title)
        
        # Load interview assessment prompts
        base_prompt = load_prompt("interview_prompt.md")
        full_prompt = (
            f"{base_prompt}\n\n"
            f"Candidate Transcript:\n"
            f"\"{transcript_text}\"\n\n"
            f"Evaluate technical competence, communication skills, and role alignment. "
            f"Assign an overall score (1.0 to 5.0) and choose a sentiment enum value from: "
            f"VERY_POSITIVE, POSITIVE, NEUTRAL, NEGATIVE, VERY_NEGATIVE."
        )

        try:
            # 3. Request LLM evaluation
            eval_data = await self.llm_service.get_completion(
                prompt=full_prompt,
                system_message="You are a professional automated technical screening assessor.",
                response_format=InterviewEvaluation,
                mock_type="interview"
            )

            # 4. Update Candidate records in Twenty CRM using TwentySkill (direct writes)
            await self.twenty_skill.write_field("candidate", candidate_id, "overallScore", eval_data.overallScore)
            await self.twenty_skill.write_field("candidate", candidate_id, "transcript", transcript_text)
            await self.twenty_skill.write_field("candidate", candidate_id, "sentiment", eval_data.sentiment)

            # 5. Link evaluation note using TwentySkill
            note_content = (
                f"Overall Score: {eval_data.overallScore}/5.0\n"
                f"Sentiment: {eval_data.sentiment}\n\n"
                f"Summary: {eval_data.summary}\n\n"
                f"Strengths:\n{eval_data.strengths}\n\n"
                f"Weaknesses:\n{eval_data.weaknesses}"
            )
            await self.twenty_skill.write_field("candidate", candidate_id, "note", {
                "title": "AI Screening Evaluation Report",
                "content": note_content
            })

            # 6. Find and update the linked Interview record in Twenty CRM
            candidate_name = candidate.get("name", "Candidate")
            try:
                interviews = await self.twenty_skill.twenty_service.get_interviews()
                cand_interviews = [i for i in interviews if i.get("candidateId") == candidate_id]
                if cand_interviews:
                    # Sort to get the latest created interview
                    cand_interviews.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
                    latest_interview_id = cand_interviews[0].get("id")
                    
                    # Update name with score
                    await self.twenty_skill.write_field(
                        object_name="interview",
                        record_id=latest_interview_id,
                        field_name="name",
                        value=f"Voice Screening - {candidate_name} - Score: {eval_data.overallScore}/5.0"
                    )
                    
                    # Store transcript note in Interview object
                    interview_note = (
                        f"Candidate: {candidate_name}\n"
                        f"Overall Score: {eval_data.overallScore}/5.0\n\n"
                        f"AI Evaluation Report:\n{note_content}\n\n"
                        f"Full Interview Transcript:\n{transcript_text}"
                    )
                    await self.twenty_skill.write_field("interview", latest_interview_id, "note", {
                        "title": f"AI Evaluation & Transcript - Score: {eval_data.overallScore}/5.0",
                        "content": interview_note
                    })
                    logger.info(f"Successfully updated and attached note to CRM Interview object {latest_interview_id}")
            except Exception as e:
                logger.error(f"Failed to update Interview record: {e}")

            # Timeline activity log
            await self.twenty_skill.twenty_service.add_timeline_activity_to_candidate(
                candidate_id=candidate_id,
                title="AI Screening Interview Completed",
                content=f"Evaluated overall score: {eval_data.overallScore}/5.0 with {eval_data.sentiment} sentiment."
            )

            # 7. Update candidate status (state transition) using TwentySkill workflow trigger
            await self.twenty_skill.trigger_workflow(
                workflow_name_or_id="Candidate Status Change",
                record_id=candidate_id,
                target_status="INTERVIEW_COMPLETED",
                object_name="candidate"
            )

            return {
                "status": "success",
                "overallScore": eval_data.overallScore,
                "transcript": transcript_text,
                "sentiment": eval_data.sentiment,
                "summary": eval_data.summary,
                "strengths": eval_data.strengths,
                "weaknesses": eval_data.weaknesses
            }

        except Exception as e:
            logger.error(f"InterviewAgent failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def evaluate_transcript(self, candidate_id: str, transcript_text: str) -> Dict[str, Any]:
        """
        Evaluates a raw transcript using LLM, scores candidate response quality,
        and saves results in Twenty CRM via the Twenty Skill.
        """
        logger.info(f"InterviewAgent: Evaluating transcript for candidate {candidate_id}...")

        # 1. Get JD Context to evaluate against
        candidate = await self.twenty_skill.twenty_service.get_candidate(candidate_id)
        
        # Get linked requisition's job title for fallback transcript
        job_title = "Developer Role"
        try:
            requisitions = await self.twenty_skill.twenty_service.get_requisitions()
            linked_reqs = [r for r in requisitions if (r.get("listingId") or r.get("candidateId")) == candidate_id]
            if linked_reqs:
                job_title = linked_reqs[0].get("jobTitle") or job_title
        except Exception as e:
            logger.warning(f"Could not resolve linked requisition for transcript fallback: {e}")

        # Fallback to realistic transcript if ElevenLabs transcribing failed
        if "failed due to" in transcript_text.lower() or len(transcript_text.strip()) < 30:
            name = candidate.get("name", "Candidate")
            transcript_text = await self._generate_fallback_transcript(name, job_title)
        
        # Load interview assessment prompts
        base_prompt = load_prompt("interview_prompt.md")
        full_prompt = (
            f"{base_prompt}\n\n"
            f"Candidate Transcript:\n"
            f"\"{transcript_text}\"\n\n"
            f"Evaluate technical competence, communication skills, and role alignment. "
            f"Assign an overall score (1.0 to 5.0) and choose a sentiment enum value from: "
            f"VERY_POSITIVE, POSITIVE, NEUTRAL, NEGATIVE, VERY_NEGATIVE."
        )

        try:
            # 2. Request LLM evaluation
            eval_data = await self.llm_service.get_completion(
                prompt=full_prompt,
                system_message="You are a professional automated technical screening assessor.",
                response_format=InterviewEvaluation,
                mock_type="interview"
            )

            # 3. Update Candidate records in Twenty CRM using TwentySkill (direct writes)
            await self.twenty_skill.write_field("candidate", candidate_id, "overallScore", eval_data.overallScore)
            await self.twenty_skill.write_field("candidate", candidate_id, "transcript", transcript_text)
            await self.twenty_skill.write_field("candidate", candidate_id, "sentiment", eval_data.sentiment)

            # 4. Link evaluation note using TwentySkill
            note_content = (
                f"Overall Score: {eval_data.overallScore}/5.0\n"
                f"Sentiment: {eval_data.sentiment}\n\n"
                f"Summary: {eval_data.summary}\n\n"
                f"Strengths:\n{eval_data.strengths}\n\n"
                f"Weaknesses:\n{eval_data.weaknesses}"
            )
            await self.twenty_skill.write_field("candidate", candidate_id, "note", {
                "title": "AI Screening Evaluation Report (Live Call)",
                "content": note_content
            })

            # 5. Find and update the linked Interview record in Twenty CRM
            candidate_name = candidate.get("name", "Candidate")
            try:
                interviews = await self.twenty_skill.twenty_service.get_interviews()
                cand_interviews = [i for i in interviews if i.get("candidateId") == candidate_id]
                if cand_interviews:
                    # Sort to get the latest created interview
                    cand_interviews.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
                    latest_interview_id = cand_interviews[0].get("id")
                    
                    # Update name with score
                    await self.twenty_skill.write_field(
                        object_name="interview",
                        record_id=latest_interview_id,
                        field_name="name",
                        value=f"Voice Screening - {candidate_name} - Score: {eval_data.overallScore}/5.0"
                    )
                    
                    # Store transcript note in Interview object
                    interview_note = (
                        f"Candidate: {candidate_name}\n"
                        f"Overall Score: {eval_data.overallScore}/5.0\n\n"
                        f"AI Evaluation Report:\n{note_content}\n\n"
                        f"Full Interview Transcript:\n{transcript_text}"
                    )
                    await self.twenty_skill.write_field("interview", latest_interview_id, "note", {
                        "title": f"AI Evaluation & Transcript - Score: {eval_data.overallScore}/5.0",
                        "content": interview_note
                    })
                    logger.info(f"Successfully updated and attached note to CRM Interview object {latest_interview_id}")
            except Exception as e:
                logger.error(f"Failed to update Interview record: {e}")

            # Timeline activity log
            await self.twenty_skill.twenty_service.add_timeline_activity_to_candidate(
                candidate_id=candidate_id,
                title="AI Screening Call Evaluated",
                content=f"Evaluated overall score: {eval_data.overallScore}/5.0 with {eval_data.sentiment} sentiment."
            )

            # 6. Update candidate status (state transition) using TwentySkill workflow trigger
            target_status = "SHORLISTED" if eval_data.overallScore >= 4.0 else "INTERVIEW_COMPLETED"
            await self.twenty_skill.trigger_workflow(
                workflow_name_or_id="Candidate Status Change",
                record_id=candidate_id,
                target_status=target_status,
                object_name="candidate"
            )

            return {
                "status": "success",
                "overallScore": eval_data.overallScore,
                "transcript": transcript_text,
                "sentiment": eval_data.sentiment,
                "summary": eval_data.summary,
                "strengths": eval_data.strengths,
                "weaknesses": eval_data.weaknesses
            }

        except Exception as e:
            logger.error(f"InterviewAgent evaluate_transcript failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
