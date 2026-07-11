import json
import logging
import httpx
from typing import Dict, Any, Optional, List, Type
from pydantic import BaseModel
from app.settings import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        logger.info(f"Initialized LLMService with provider: {self.provider}")

    async def get_completion(
        self,
        prompt: str,
        system_message: str = "You are an expert recruitment assistant.",
        response_format: Optional[Type[BaseModel]] = None,
        mock_type: Optional[str] = None
    ) -> Any:
        """
        Retrieves text or structured completion from the configured LLM provider.
        Supports automatic fallback to high-quality mock data if API key is not present.
        """
        # Detect if we should use Mock Mode
        is_mock = self.provider == "mock"
        if self.provider == "gemini" and not settings.GEMINI_API_KEY:
            logger.warning("Gemini API key is empty! Falling back to Mock Mode.")
            is_mock = True
        elif self.provider == "openai" and not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key is empty! Falling back to Mock Mode.")
            is_mock = True

        if is_mock:
            return self._generate_mock_response(prompt, response_format, mock_type)

        # Prepare endpoint config
        url = ""
        headers = {}
        model_name = ""

        if self.provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/openai/chat/completions?key={settings.GEMINI_API_KEY}"
            headers = {}
            model_name = "gemini-1.5-flash"
        elif self.provider == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
            model_name = "gpt-4o-mini"
        elif self.provider == "openrouter":
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"}
            model_name = "google/gemini-flash-1.5"
        elif self.provider == "openclaw":
            url = f"{settings.OPENCLAW_URL.rstrip('/')}/chat/completions"
            headers = {}
            model_name = "default"
        else:
            logger.warning(f"Unknown provider '{self.provider}'. Falling back to Mock Mode.")
            return self._generate_mock_response(prompt, response_format, mock_type)

        headers["Content-Type"] = "application/json"

        # Prepare messages
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]

        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.2
        }

        # If structured format is requested, configure response_format or hint the output
        if response_format:
            # Note: Not all providers support standard response_format. We will inject JSON constraint.
            payload["response_format"] = {"type": "json_object"}
            schema_description = response_format.model_json_schema()
            messages[0]["content"] += f"\n\nYou MUST reply with a JSON object that strictly conforms to this schema: {json.dumps(schema_description)}"

        logger.info(f"LLM request to provider: {self.provider} / model: {model_name}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload, timeout=25.0)
                response.raise_for_status()
                res_data = response.json()
                content = res_data["choices"][0]["message"]["content"]
                logger.info("Successfully received response from LLM provider.")

                if response_format:
                    # Clean up triple backticks markdown syntax if model includes it in JSON response
                    cleaned_content = content.strip()
                    if cleaned_content.startswith("```json"):
                        cleaned_content = cleaned_content[7:]
                    if cleaned_content.endswith("```"):
                        cleaned_content = cleaned_content[:-3]
                    cleaned_content = cleaned_content.strip()
                    
                    parsed_json = json.loads(cleaned_content)
                    return response_format.model_validate(parsed_json)
                
                return content
            except Exception as e:
                logger.error(f"LLM request failed: {e}. Falling back to Mock Mode.")
                return self._generate_mock_response(prompt, response_format, mock_type)

    def _generate_mock_response(
        self,
        prompt: str,
        response_format: Optional[Type[BaseModel]],
        mock_type: Optional[str]
    ) -> Any:
        """Generates realistic mock data for all agents to enable direct sandbox testing."""
        logger.info(f"Generating mock response of type: {mock_type or 'generic'}")
        
        # 1. Job Description parser mock
        if mock_type == "jd":
            data = {
                "name": "Senior Software Engineer (Backend)",
                "jobTitle": "Senior Software Engineer",
                "department": "Engineering",
                "jobDescription": "We are seeking a seasoned Software Engineer to lead backend architecture using FastAPI, PostgreSQL, and multi-agent platforms.",
                "requiredSkills": "FastAPI, PostgreSQL, Docker, AsyncIO, Python, LLMs",
                "experience": "5+ Years",
                "location": "San Francisco, CA (Hybrid)",
                "employmentType": "FULL_TIME",
                "status": "OPEN"
            }
            if response_format:
                return response_format.model_validate(data)
            return json.dumps(data)

        elif mock_type == "jd_text":
            return (
                "# Job Opportunity: Senior Backend Engineer\n\n"
                "## About the Role\n"
                "We are looking for a Senior Backend Engineer to join our high-performing Engineering team. "
                "You will take ownership of backend services, API designs, and orchestrations, developing reliable "
                "and scalable server-side systems.\n\n"
                "## Key Responsibilities\n"
                "- Design, build, and maintain FastAPI service architectures.\n"
                "- Integrate ElevenLabs conversational systems and maintain real-time webhooks.\n"
                "- Manage database interactions and state consistency using PostgreSQL and Twenty CRM.\n\n"
                "## Qualifications\n"
                "- 5+ years of experience in Python engineering (FastAPI, AsyncIO preferred).\n"
                "- Strong understanding of data schemas, webhook engineering, and relational integrations.\n"
                "- Excellent communication skills and soft skills."
            )

        elif mock_type == "transcript":
            return (
                "Interviewer: Hello. Thank you for joining our automated screening call. Let's start with the first question: Can you tell me about your background?\n"
                "Candidate: Sure! I have over 4 years of experience in backend development, building APIs and working with databases. I'm excited about this opportunity.\n"
                "Interviewer: Great. How do you handle API performance and scaling?\n"
                "Candidate: I focus on clean database querying, using Redis for caching, and writing asynchronous handlers to handle high load.\n"
                "Interviewer: Perfect. Thank you for your time today."
            )

        # 2. Interview Evaluation mock
        elif mock_type == "interview":
            data = {
                "overallScore": 4.5,
                "summary": "Candidate demonstrated solid competence and clear communication.",
                "sentiment": "POSITIVE",
                "strengths": "- Excellent knowledge of async Python and backend design.\n- Clear communication of architectural trade-offs.",
                "weaknesses": "- Relatively new to ElevenLabs voice platforms, but demonstrates high eagerness to learn."
            }
            if response_format:
                return response_format.model_validate(data)
            return json.dumps(data)

        # 3. Candidate Retrospective mock
        elif mock_type == "retrospective":
            data = {
                "decision": "Hire",
                "strengths": "- Excellent knowledge of async Python and backend design.\n- Clear communication of architectural trade-offs.",
                "concerns": "- Relatively new to ElevenLabs voice platforms, but demonstrates high eagerness to learn.",
                "areas_to_probe": "- Probe about production scale challenges with WebSockets and audio streaming.",
                "summary": "Overall highly qualified candidate who fits the senior software engineer role well."
            }
            if response_format:
                return response_format.model_validate(data)
            return json.dumps(data)

        elif mock_type == "retrospective_audit":
            return (
                "# Weekly Retrospective & Pipeline Tuning Proposals\n\n"
                "## Executive Summary\n"
                "This audit evaluated human overrides across the autonomous candidate screening pipeline. "
                "Hiring managers manually adjusted candidate records in 2 instances where they felt "
                "the AI grading criteria was misaligned with role requirements.\n\n"
                "## Observed Discrepancies\n"
                "1. **Technical Depth Over-Penalization**: In Case 1, the candidate was graded 2.5/5.0 by the AI "
                "due to hesitation on database lock mechanics, but was manually short-listed by the team. "
                "Hiring managers valued the candidate's strong backend design systems communication over textbook lock definitions.\n"
                "2. **Communication Bias**: In Case 2, a candidate was graded lower due to an accent, but managers "
                "manually short-listed them because the technical competence was exceptionally high.\n\n"
                "## Recommended Adjustments\n"
                "### Prompt Modifications\n"
                "- **Interview Agent Prompt**: Adjust technical grading guidelines to value architectural design patterns "
                "and conceptual problem-solving over exact definitions. Reduce penalties for standard response hesitations.\n"
                "### Threshold Adjustments\n"
                "- Propose lowering the shortlisting score threshold from `4.0` to `3.5` for roles requiring niche backend design expertise."
            )

        # 3. Scheduling Assistant mock
        elif mock_type == "scheduling":
            data = {
                "date": "2026-07-15",
                "start_time": "14:00",
                "end_time": "14:45",
                "reason": "This matches both the candidate's preferred afternoon slot and the interviewer's open calendar block.",
                "outreach_script": "Hi, this is Antigravity's autonomous recruiter. We'd love to schedule your voice screening on July 15th at 2:00 PM. Please let us know if that works!"
            }
            if response_format:
                return response_format.model_validate(data)
            return json.dumps(data)

        # Generic response fallback
        if response_format:
            schema_keys = response_format.model_fields.keys()
            generic_data = {k: "Mocked value" for k in schema_keys}
            return response_format.model_validate(generic_data)
            
        return "This is a mock LLM output demonstrating autonomous execution."
