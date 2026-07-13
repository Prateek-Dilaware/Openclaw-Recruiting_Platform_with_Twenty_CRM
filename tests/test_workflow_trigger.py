import asyncio
import httpx
import sys
from pathlib import Path

# Add scripts directory to path to allow importing modules
scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
sys.path.append(str(scripts_dir))

from create_objects import load_twenty_env, get_headers

async def test_workflow():
    print("==================================================")
    print("Testing Automated Workflow Webhook Trigger")
    print("==================================================")
    
    api_url, api_key = load_twenty_env()
    headers = get_headers(api_key)
    
    # 1. Fetch a real candidate to get dynamic variables
    print("\nFetching candidate list from Twenty CRM...")
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{api_url.rstrip('/')}/rest/candidates", headers=headers)
            res.raise_for_status()
            candidates = res.json().get("data", {}).get("candidates", [])
        except Exception as e:
            print(f"Error connecting to Twenty CRM: {e}")
            sys.exit(1)
            
        if not candidates:
            print("No candidates found in Twenty CRM! Run seed_demo_data.py first.")
            sys.exit(1)
            
        candidate = candidates[0]
        cand_id = candidate.get("id")
        cand_name = candidate.get("name")
        cand_phone_obj = candidate.get("phone", {})
        cand_phone = ""
        if isinstance(cand_phone_obj, dict):
            cand_phone = cand_phone_obj.get("primaryPhoneNumber") or ""
        elif isinstance(cand_phone_obj, str):
            cand_phone = cand_phone_obj
            
        if not cand_phone:
            cand_phone = "1234567890"  # fallback
            
        print(f"Matched test candidate: '{cand_name}' (ID: {cand_id}, Phone: {cand_phone})")
        
        # 2. Fire trigger payload at local FastAPI endpoint
        payload = {
            "candidate_id": cand_id,
            "phone": cand_phone,
            "name": cand_name
        }
        
        target_url = "http://localhost:8000/api/v1/webhooks/workflow-trigger"
        print(f"\nSending POST request to {target_url}...")
        
        try:
            trigger_res = await client.post(target_url, json=payload, timeout=25.0)
            print("Response Status Code:", trigger_res.status_code)
            print("Response Body:", trigger_res.json())
            
            if trigger_res.status_code == 200:
                print("\nSUCCESS: Outbound call triggered automatically, and status set to SCREENING!")
            else:
                print(f"\nFAILED: Webhook endpoint returned status {trigger_res.status_code}")
        except Exception as e:
            print(f"\nFAILED: Could not reach backend: {e}")

if __name__ == "__main__":
    asyncio.run(test_workflow())
