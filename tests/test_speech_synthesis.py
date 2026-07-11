import os
import sys
from pathlib import Path

# Add backend directory to sys.path so we can import app modules
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.append(str(backend_dir))

from app.services.elevenlabs_service import ElevenLabsService

def main():
    print("==================================================")
    print("    ElevenLabs Voice Synthesizer & Tester CLI     ")
    print("==================================================")
    
    print("Initializing ElevenLabs Service...")
    service = ElevenLabsService()
    
    if not service.has_key:
        print("WARNING: ElevenLabs API Key is not set or invalid! Running in Mock Mode.")
    
    print("Fetching available voices from ElevenLabs...")
    try:
        voices = service.get_available_voices()
    except Exception as e:
        print(f"Error fetching voices: {e}")
        return

    if not voices:
        print("No voices found!")
        return

    print("\nAvailable Voices:")
    print("--------------------------------------------------")
    for index, voice in enumerate(voices, 1):
        print(f"[{index}] {voice['name']} (ID: {voice['id']})")
    print("--------------------------------------------------")

    # Select Voice
    try:
        choice = input(f"Choose a voice number (1-{len(voices)}) [default: 1]: ").strip()
        if not choice:
            selected_voice = voices[0]
        else:
            idx = int(choice) - 1
            if 0 <= idx < len(voices):
                selected_voice = voices[idx]
            else:
                print(f"Invalid selection. Defaulting to first voice: {voices[0]['name']}")
                selected_voice = voices[0]
    except ValueError:
        print(f"Invalid input. Defaulting to first voice: {voices[0]['name']}")
        selected_voice = voices[0]

    print(f"Selected voice: {selected_voice['name']}")

    # Get Text input
    default_text = "Hello! This is a test of the ElevenLabs voice synthesizer. The system is working correctly."
    text = input(f"\nEnter the text to synthesize (press Enter for default):\n> ").strip()
    if not text:
        text = default_text

    print("\nSynthesizing speech...")
    try:
        audio = service.text_to_speech(text, selected_voice['id'])
        
        output_file = Path(__file__).resolve().parent / "test_output.mp3"
        print(f"Saving audio to: {output_file}")
        service.save_audio(audio, str(output_file))
        
        print("\nSUCCESS! Speech generated and saved.")
        
        # Try to play the file automatically
        print("Opening the audio file in the default media player...")
        if os.name == 'nt':
            os.system(f'start "" "{output_file}"')
        else:
            os.system(f'open "{output_file}"')
            
    except Exception as e:
        print(f"\nFailed to generate speech: {e}")

if __name__ == "__main__":
    main()
