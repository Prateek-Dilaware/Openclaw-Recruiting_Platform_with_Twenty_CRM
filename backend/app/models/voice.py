from pydantic import BaseModel


class SpeechRequest(BaseModel):

    text: str

    voice_id: str | None = None

    model: str | None = None