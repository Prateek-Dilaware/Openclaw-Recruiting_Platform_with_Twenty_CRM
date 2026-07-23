import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.append(str(backend_dir))

from app.services.elevenlabs_service import ElevenLabsService

def test_elevenlabs():
    print("Initializing ElevenLabsService...")
    service = ElevenLabsService()
    
    print("Fetching available voices...")
    voices = service.get_available_voices()
    
    print("\nAVAILABLE VOICES:")
    print("---------------------------")
    for voice in voices[:10]:  # Show first 10 voices
        print(f"{voice['name']} - {voice['id']}")
    print(f"... and {len(voices) - 10} more voices.")

if __name__ == "__main__":
    test_elevenlabs()