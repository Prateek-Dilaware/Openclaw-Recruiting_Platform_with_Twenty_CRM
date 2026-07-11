import logging
from typing import Dict, Any
from pydantic import BaseModel
from app.services.llm_service import LLMService
from app.utils.prompt_loader import load_prompt

logger = logging.getLogger(__name__)

class JDStructure(BaseModel):
    name: str
    jobTitle: str
    department: str
    jobDescription: str
    requiredSkills: str
    experience: str
    location: str
    employmentType: str
    status: str

class JDAgent:
    def __init__(self):
        self.llm_service = LLMService()
        logger.info("JDAgent initialized.")

    async def generate_job_description(self, requirements: str) -> Dict[str, Any]:
        """
        Parses raw requirements text and extracts a structured job description.
        """
        logger.info("JDAgent: Generating structured job description...")
        
        # Load prompt and append hiring manager's raw input requirements
        base_prompt = load_prompt("jd_prompt.md")
        full_prompt = (
            f"{base_prompt}\n\n"
            f"Requirements to analyze:\n"
            f"{requirements}\n\n"
            f"Provide a name for the requisition (e.g. 'Software Engineer - Backend'), job title, "
            f"department, detailed description, required skills, required experience, location (default to Remote if unspecified), "
            f"employmentType (choose ONLY from: FULL_TIME, PART_TIME, INTERNSHIP), and status (default to OPEN)."
        )
        
        system_message = "You are an expert AI Recruiting agent that parses text and formats structured Job Descriptions."
        
        try:
            structured_jd = await self.llm_service.get_completion(
                prompt=full_prompt,
                system_message=system_message,
                response_format=JDStructure,
                mock_type="jd"
            )
            logger.info("JDAgent: Structured job description successfully generated.")
            return structured_jd.model_dump()
        except Exception as e:
            logger.error(f"JDAgent execution failed: {e}")
            # Safe default fallback
            return {
                "name": "Software Engineer (Generalist)",
                "jobTitle": "Software Engineer",
                "department": "Engineering",
                "jobDescription": requirements or "General software engineering role.",
                "requiredSkills": "Python, Javascript, Git",
                "experience": "2+ Years",
                "location": "Remote",
                "employmentType": "FULL_TIME",
                "status": "OPEN"
            }

    async def generate_description_from_requisition(self, requisition_id: str) -> str:
        """
        Reads an existing Requisition record from Twenty, uses its details as context
        to generate a highly detailed, professional JD, and writes it back using the Twenty Skill.
        """
        logger.info(f"JDAgent: Generating description from requisition {requisition_id}...")
        
        from app.services.crm_service import CRMService
        twenty_skill = CRMService()
        
        try:
            requisition = await twenty_skill.twenty_service.get_requisition(requisition_id)
        except Exception as err:
            logger.error(f"Failed to fetch requisition {requisition_id} from CRM: {err}")
            raise err

        job_title = requisition.get("jobTitle") or requisition.get("name") or "Software Engineer"
        department = requisition.get("department") or "Engineering"
        location = requisition.get("location") or "Remote"
        experience = requisition.get("experience") or "Mid-Senior"
        required_skills = requisition.get("requiredSkills") or ""
        current_description = requisition.get("jobDescription") or ""

        base_prompt = load_prompt("jd_prompt.md")
        full_prompt = (
            f"{base_prompt}\n\n"
            f"Generate a professional, fully-formatted job description for this role:\n"
            f"Title: {job_title}\n"
            f"Department: {department}\n"
            f"Location: {location}\n"
            f"Experience: {experience}\n"
            f"Required Skills: {required_skills}\n"
            f"Additional Context/Outline:\n{current_description}\n\n"
            f"Provide a beautifully formatted output detailing About the Role, Key Responsibilities, and Qualifications."
        )

        try:
            jd_text = await self.llm_service.get_completion(
                prompt=full_prompt,
                system_message="You are an expert executive recruiter writing high-performance job descriptions.",
                mock_type="jd_text"
            )
            
            # Write it back to the CRM Requisition via Twenty Skill write_field
            await twenty_skill.write_field("requisition", requisition_id, "jobDescription", jd_text)
            logger.info(f"JDAgent: Requisition {requisition_id} jobDescription successfully updated.")
            return jd_text
        except Exception as e:
            logger.error(f"JDAgent failed to generate and write detailed JD: {e}")
            fallback_jd = (
                f"Role: {job_title}\n"
                f"Department: {department}\n"
                f"Location: {location}\n\n"
                f"We are looking for a {job_title} to join our growing {department} team. "
                f"Key requirements: {required_skills}. Experience: {experience}.\n"
                f"Outline: {current_description}"
            )
            await twenty_skill.write_field("requisition", requisition_id, "jobDescription", fallback_jd)
            return fallback_jd
