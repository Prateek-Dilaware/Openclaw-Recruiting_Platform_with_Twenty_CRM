import os
from pathlib import Path
from dotenv import load_dotenv

env_file_path = os.path.join(Path(__file__).resolve().parent.parent, ".env")
load_dotenv(dotenv_path=env_file_path, override=False)

from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    ELEVENLABS_API_KEY: str = ""

    ELEVENLABS_VOICE_ID: str = ""

    ELEVENLABS_AGENT_ID: str = ""

    ELEVENLABS_PHONE_NUMBER_ID: str = ""

    ELEVENLABS_MODEL: str = "eleven_multilingual_v2"

    GEMINI_API_KEY: str = ""

    OPENAI_API_KEY: str = ""

    TWENTY_API_URL: str = "http://localhost:3000"

    TWENTY_API_KEY: str = ""

    # Used only by the OpenClaw LLM provider path in llm_service.py
    # (LLM_PROVIDER=openclaw). Not related to CRM execution routing.
    OPENCLAW_URL: str = ""

    LLM_PROVIDER: str = "gemini"

    class Config:
        import os
        from pathlib import Path
        env_file = os.path.join(Path(__file__).resolve().parent.parent, ".env")
        extra = "ignore"


settings = Settings()