"""
Python client for OpenClaw skill execution.
"""

import httpx
from app.settings import settings
import logging

logger = logging.getLogger(__name__)

class OpenclawClient:
    def __init__(self):
        self.base_url = getattr(settings, 'OPENCLAW_API_URL', 'http://localhost:8080')
        self.api_key = getattr(settings, 'OPENCLAW_API_KEY', '')
        logger.info(f"OpenclawClient initialized linking to: {self.base_url}")
    
    async def execute_skill(self, skill_name: str, params: dict) -> dict:
        """Sends a POST request to execute a specific OpenClaw skill"""
        url = f"{self.base_url}/skills/{skill_name}/execute"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=params, timeout=30.0)
                response.raise_for_status()
                result = response.json()
                logger.info(f"OpenClaw skill '{skill_name}' executed successfully")
                return result
            except Exception as e:
                logger.error(f"OpenClaw skill execution failed: {e}")
                raise Exception(f"OpenClaw client execution error: {e}")
