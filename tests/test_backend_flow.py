import sys
import os
import json
import asyncio
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.append(str(backend_dir))

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx

API_BASE = "http://localhost:8000/api/v1"

async def test_full_pipeline():
    print("==================================================")
    print("Starting OpenClaw Recruiting Platform Test Suite")
    print("==================================================")
    
    async with httpx.AsyncClient() as client:
        # 1. Health check
        print("\n[1/6] Checking API Health...")
        try:
            res = await client.get(f"{API_BASE}/health")
            print("Status:", res.status_code)
            print("Content:", res.json())
        except Exception as e:
            print("FASTAPI SERVER IS NOT RUNNING. Start it first with 'uvicorn app.main:app --reload'")
            return

        # 2. Requisition Parse JD
        print("\n[2/6] Testing JDAgent (Parse JD and Create Requisition)...")
        jd_text = (
            "We are seeking a Senior Backend Engineer. "
            "Must have 5 years experience in FastAPI and PostgreSQL. "
            "Location: Remote. Status: Open."
        )
        res = await client.post(f"{API_BASE}/requisitions/parse-jd", data={"requirements": jd_text})
        print("Status:", res.status_code)
        parsed_data = res.json()
        print("Parsed Requisition:", json.dumps(parsed_data, indent=2))
        
        # 3. Create Candidate
        print("\n[3/6] Testing Candidate Registration...")
        candidate_data = {
            "name": "Integration Tester",
            "email": "tester@example.com",
            "phone": "+1999999999",
            "resumeUrl": "https://example.com/tester_resume.pdf"
        }
        res = await client.post(f"{API_BASE}/candidates", json=candidate_data)
        print("Status:", res.status_code)
        candidate = res.json()
        print("Created Candidate:", json.dumps(candidate, indent=2))
        candidate_id = candidate.get("id")

        # 4. Schedule Outreach
        print("\n[4/6] Testing Scheduling Agent (Schedule & Outreach Audio)...")
        schedule_payload = {
            "candidate_availability": "Mondays 3pm",
            "interviewer_slots": "Monday July 12th 3pm-4pm",
            "voice_id": "EXAVITQu4vr4xnSDxMaL"
        }
        res = await client.post(f"{API_BASE}/candidates/{candidate_id}/schedule", data=schedule_payload)
        print("Status:", res.status_code)
        schedule_result = res.json()
        print("Schedule Result:", json.dumps(schedule_result, indent=2))

        # 5. Evaluate Voice Screening
        print("\n[5/6] Testing Interview Agent (Voice Evaluation)...")
        # Create a dummy text audio payload
        dummy_wav_content = b"RIFF\x24\x00\x00\x00WAVEfmt "
        files = {"file": ("response.wav", dummy_wav_content, "audio/wav")}
        res = await client.post(f"{API_BASE}/candidates/{candidate_id}/evaluate-screening", files=files)
        print("Status:", res.status_code)
        eval_result = res.json()
        print("Evaluation Result:", json.dumps(eval_result, indent=2))

        # 6. Retrospective Decision
        print("\n[6/6] Testing Retrospective Agent (Final Recommendation)...")
        res = await client.post(f"{API_BASE}/candidates/{candidate_id}/retrospective")
        print("Status:", res.status_code)
        retro_result = res.json()
        print("Retrospective Decision Result:", json.dumps(retro_result, indent=2))

        print("\n==================================================")
        print("OpenClaw Recruiting Platform Test Suite Completed")
        print("==================================================")

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
