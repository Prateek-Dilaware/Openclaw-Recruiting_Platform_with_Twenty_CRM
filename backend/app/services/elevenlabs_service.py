import logging
import httpx
from pathlib import Path
from elevenlabs.client import ElevenLabs
from app.settings import settings

logger = logging.getLogger(__name__)

class ElevenLabsService:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.has_key = bool(self.api_key)
        
        if self.has_key:
            try:
                self.client = ElevenLabs(api_key=self.api_key)
                logger.info("ElevenLabsService initialized with valid API key.")
            except Exception as e:
                logger.error(f"Failed to initialize ElevenLabs client: {e}")
                self.has_key = False
        else:
            logger.warning("ElevenLabs API key is empty! Running in Mock Mode.")
            self.client = None

    def get_available_voices(self):
        """Fetches all available voices."""
        if not self.has_key:
            logger.info("Mock Mode: Fetching available voices...")
            return [
                {"id": "CwhRBWXzGAHq8TQ4Fs17", "name": "Roger", "category": "custom"},
                {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Sarah", "category": "premade"},
                {"id": "IKne3meq5aSn9XLyUdCD", "name": "Charlie", "category": "premade"}
            ]

        try:
            response = self.client.voices.get_all()
            voices = []
            for voice in response.voices:
                voices.append({
                    "id": voice.voice_id,
                    "name": voice.name,
                    "category": voice.category,
                })
            return voices
        except Exception as e:
            logger.error(f"ElevenLabs get_available_voices failed: {e}")
            return [{"id": "EXAVITQu4vr4xnSDxMaL", "name": "Sarah (Fallback)", "category": "premade"}]

    def text_to_speech(self, text: str, voice_id: str, model_id: str | None = None):
        """Converts text to speech audio stream."""
        if not self.has_key:
            logger.info(f"Mock Mode: TTS convert text '{text[:30]}...' with voice {voice_id}")
            # Return dummy bytes generator representing mock audio
            return [b"mock_audio_data_chunk"]

        if model_id is None:
            model_id = settings.ELEVENLABS_MODEL

        try:
            audio = self.client.text_to_speech.convert(
                voice_id=voice_id,
                model_id=model_id,
                text=text,
            )
            return audio
        except Exception as e:
            logger.error(f"ElevenLabs text_to_speech failed: {e}")
            return [b"fallback_audio_data"]

    def save_audio(self, audio, output_path: str) -> str:
        """Saves audio byte stream to file."""
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        logger.info(f"Successfully saved audio file to: {output_path}")
        return str(output)

    def speech_to_text(self, audio_path: str) -> str:
        """Transcribes audio file to text."""
        if not self.has_key:
            logger.info(f"Mock Mode: Transcribing audio file at {audio_path}")
            return "Hello, this is a mock candidate speech response for screening."

        try:
            with open(audio_path, "rb") as audio_file:
                transcript = self.client.speech_to_text.convert(
                    file=audio_file,
                    model_id="scribe_v2"
                )
            return transcript.text
        except Exception as e:
            logger.error(f"ElevenLabs speech_to_text failed: {e}")
            return "Transcription failed due to API connection error."

    # ==========================================================
    # Added / Expanded Methods
    # ==========================================================
    async def download_audio(self, audio_url: str, output_path: str) -> str:
        """Downloads audio file from a specific remote URL and saves it locally."""
        logger.info(f"Downloading audio from {audio_url} to {output_path}")
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        if not self.has_key or audio_url.startswith("mock://"):
            with open(output, "wb") as f:
                f.write(b"mock_downloaded_audio_content")
            return str(output)

        async with httpx.AsyncClient() as client:
            response = await client.get(audio_url)
            response.raise_for_status()
            with open(output, "wb") as f:
                f.write(response.content)
        return str(output)

    async def create_conversation(self, agent_id: str) -> Dict[str, Any]:
        """Creates a conversational session configuration."""
        logger.info(f"Creating conversational AI session for agent {agent_id}")
        if not self.has_key:
            return {
                "conversation_id": "conv_mock_123456",
                "agent_id": agent_id,
                "status": "initialized",
                "websocket_url": "wss://api.elevenlabs.io/v1/convai/conversation?agent_id=mock"
            }

        url = f"https://api.elevenlabs.io/v1/convai/conversations"
        headers = {"xi-api-key": self.api_key, "Content-Type": "application/json"}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json={"agent_id": agent_id})
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"ElevenLabs create_conversation failed: {e}")
                return {"error": str(e), "status": "failed"}

    async def get_first_phone_number_id(self) -> Optional[str]:
        """Fetches the first registered phone number ID from the ElevenLabs account."""
        if not self.has_key:
            return "mock_phone_number_id"
        
        url = "https://api.elevenlabs.io/v1/convai/phone-numbers"
        headers = {"xi-api-key": self.api_key}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                phone_numbers = data.get("phone_numbers", [])
                if phone_numbers:
                    # Select the first configured number
                    num_id = phone_numbers[0].get("phone_number_id")
                    logger.info(f"Automatically detected ElevenLabs phone number ID: {num_id}")
                    return num_id
            except Exception as e:
                logger.error(f"Failed to fetch ElevenLabs phone numbers: {e}")
        return None

    async def start_outbound_call(self, phone: str, agent_id: str, dynamic_variables: Dict[str, str] = None) -> Dict[str, Any]:
        """Initiates an outbound conversational phone call to a candidate using Twilio telephony."""
        logger.info(f"Starting outbound ElevenLabs call to {phone} for agent {agent_id}")
        if not self.has_key:
            return {
                "call_id": "call_mock_789012",
                "phone_number": phone,
                "agent_id": agent_id,
                "status": "ringing",
                "message": "Outbound call successfully simulated (Mock Mode)"
            }

        # Resolve phone number ID
        phone_number_id = settings.ELEVENLABS_PHONE_NUMBER_ID
        if not phone_number_id:
            phone_number_id = await self.get_first_phone_number_id()
            
        if not phone_number_id:
            logger.error("No ElevenLabs phone number ID found on account. Call cannot be placed.")
            return {
                "error": "No registered phone number was found on your ElevenLabs account. Please configure a Twilio number in your ElevenLabs console.",
                "status": "failed"
            }

        url = "https://api.elevenlabs.io/v1/convai/twilio/outbound-call"
        headers = {"xi-api-key": self.api_key, "Content-Type": "application/json"}
        
        # Build standard ElevenLabs Twilio Outbound call payload
        payload = {
            "agent_id": agent_id,
            "agent_phone_number_id": phone_number_id,
            "to_number": phone
        }
        
        if dynamic_variables:
            payload["conversation_initiation_client_data"] = {
                "dynamic_variables": dynamic_variables
            }
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload, timeout=20.0)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"ElevenLabs start_outbound_call failed: {e}")
                return {"error": str(e), "status": "failed"}

    async def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """Fetches status metrics and duration of a conversational call."""
        logger.info(f"Retrieving ElevenLabs call status for {call_id}")
        if not self.has_key or call_id.startswith("call_mock"):
            return {
                "call_id": call_id,
                "status": "completed",
                "duration_seconds": 45,
                "transcript": "Agent: Hello, welcome. Candidate: Thanks for calling. Agent: What is your FastAPI experience?",
                "cost": 0.0
            }

        url = f"https://api.elevenlabs.io/v1/convai/calls/{call_id}"
        headers = {"xi-api-key": self.api_key}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"ElevenLabs get_call_status failed: {e}")
                return {"error": str(e), "call_id": call_id, "status": "unknown"}

    async def list_history(self) -> List[Dict[str, Any]]:
        """Queries historical conversational logs."""
        logger.info("Listing ElevenLabs history logs...")
        if not self.has_key:
            return [
                {"call_id": "call_mock_1", "duration": 120, "date": "2026-07-08"},
                {"call_id": "call_mock_2", "duration": 85, "date": "2026-07-09"}
            ]

        url = "https://api.elevenlabs.io/v1/convai/conversations"
        headers = {"xi-api-key": self.api_key}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json().get("conversations", [])
            except Exception as e:
                logger.error(f"ElevenLabs list_history failed: {e}")
                return []

    async def get_latest_agent_conversation_id(self, agent_id: str) -> Optional[str]:
        """Retrieves the most recent conversation ID for a given agent."""
        if not self.has_key:
            return None
            
        url = "https://api.elevenlabs.io/v1/convai/conversations"
        headers = {"xi-api-key": self.api_key}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                conversations = response.json().get("conversations", [])
                
                agent_convs = [c for c in conversations if c.get("agent_id") == agent_id]
                if not agent_convs:
                    return None
                
                agent_convs.sort(key=lambda x: x.get("start_time_unix_secs", 0), reverse=True)
                return agent_convs[0].get("conversation_id")
            except Exception as e:
                logger.error(f"ElevenLabs get_latest_agent_conversation_id failed: {e}")
                return None

    async def get_conversation_transcript(self, conversation_id: str) -> str:
        """Fetches and formats the transcript of a specific conversation ID."""
        if not self.has_key or conversation_id.startswith("call_mock"):
            return "Interviewer: Hello. Candidate: Hi. Interviewer: Tell me about your experience."

        url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
        headers = {"xi-api-key": self.api_key}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                turns = data.get("transcript", [])
                formatted_turns = []
                for turn in turns:
                    role = "Candidate" if turn.get("role") == "user" else "Interviewer"
                    message = turn.get("message", "")
                    formatted_turns.append(f"{role}: {message}")
                
                return "\n".join(formatted_turns)
            except Exception as e:
                logger.error(f"ElevenLabs get_conversation_transcript failed: {e}")
                return ""