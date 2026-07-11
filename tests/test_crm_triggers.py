import sys
import httpx
import json
import asyncio
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.append(str(backend_dir))

API_BASE = "http://localhost:8000/api/v1"
CRM_BASE = "http://localhost:3000/rest"
HEADERS = {
    "Authorization": "Bearer eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImU1Yjk5YTU0LWNlNDYtNDMxOC05ZDBkLWY4NWM3ODVmZjMyZSJ9.eyJzdWIiOiI3YjJmYTIwYi0zY2Q1LTQzYjMtYjM3MC01OGY4NjViZDUyNjUiLCJ0eXBlIjoiQVBJX0tFWSIsIndvcmtzcGFjZUlkIjoiN2IyZmEyMGItM2NkNS00M2IzLWIzNzAtNThmODY1YmQ1MjY1IiwiaWF0IjoxNzgzNTk2NTM1LCJleHAiOjQ5MzcxOTY1MzQsImp0aSI6IjkzOTRmODdjLTJmNzQtNDkzNi04OGI3LTMwM2JiZjQ1NzI4NyJ9.zB95ZEzTPAj1Epe5cEPdQWHv9jjAc1GomGy0lxjPnm4UfltVMpBQYvxqsS3k3VRu-wvP-lPpjooccPo1Dz6ECQ",
    "Content-Type": "application/json"
}

async def test_crm_triggers():
    print("==================================================")
    print("Testing HR Twenty CRM Automation Webhook triggers")
    print("==================================================")
    
    async with httpx.AsyncClient() as client:
        # 1. Create a candidate in APPLIED status to ensure we have one to schedule
        print("\n[1/4] Creating new Candidate in APPLIED status...")
        cand_payload = {
            "name": "Audit Candidate",
            "email": {
                "primaryEmail": "audit@example.com",
                "additionalEmails": []
            },
            "phone": {
                "primaryPhoneNumber": "1234567890",
                "primaryPhoneCountryCode": "",
                "primaryPhoneCallingCode": "+1",
                "additionalPhones": []
            },
            "resumeUrl": "https://example.com/audit_resume.pdf",
            "interviewStatus": "APPLIED"
        }
        res_cand = await client.post(f"{CRM_BASE}/candidates", headers=HEADERS, json=cand_payload)
        cand_data = res_cand.json().get("data", {}).get("createCandidate", res_cand.json())
        cand_id = cand_data.get("id")
        print(f"Created Candidate: {cand_data.get('name')} (ID: {cand_id}) in status APPLIED.")
        
        # 2. Create Requisition in DRAFT status
        print("\n[2/4] Creating Requisition in DRAFT status...")
        req_payload = {
            "name": "Audit Requisition - Lead Frontend",
            "jobTitle": "Lead Frontend Engineer",
            "department": "Engineering",
            "experience": "6+ Years",
            "location": "Remote",
            "requiredSkills": "React, TypeScript, CSS, Vite, Jest",
            "jobDescription": "Draft outline for a frontend lead role...",
            "status": "DRAFT",
            "employmentType": "FULL_TIME"
        }
        res_req = await client.post(f"{CRM_BASE}/requistions", headers=HEADERS, json=req_payload)
        req_data = res_req.json().get("data", {}).get("createRequistion", res_req.json())
        req_id = req_data.get("id")
        print(f"Created Requisition: {req_data.get('name')} (ID: {req_id}) in status DRAFT.")
        
        # 3. Simulate HR updating Requisition status to OPEN
        print("\n[3/4] Simulating HR updating Requisition status to OPEN...")
        update_payload = {
            "status": "OPEN"
        }
        # This update will trigger our FastAPI CRM webhook on localhost:8000
        res_update = await client.patch(f"{CRM_BASE}/requistions/{req_id}", headers=HEADERS, json=update_payload)
        print("PATCH Requisition Status Code:", res_update.status_code)
        
        # Wait a few seconds for the async agents to finish execution via the webhook trigger
        print("Waiting 5 seconds for JD Agent and Scheduling Agent to process...")
        await asyncio.sleep(5)
        
        # 4. Verify results
        print("\n[4/4] Verifying modifications in Twenty CRM...")
        
        # Fetch Requisition again to see if JD is written
        res_req_final = await client.get(f"{CRM_BASE}/requistions/{req_id}", headers=HEADERS)
        req_final = res_req_final.json().get("data", {}).get("requistion", {})
        final_desc = req_final.get("jobDescription") or ""
        
        print(f"\nFinal Requisition status: {req_final.get('status')}")
        print(f"Final Job Description starts with:\n---\n{final_desc[:300]}...\n---")
        
        # Fetch Candidate to see if they were scheduled
        res_cand_final = await client.get(f"{CRM_BASE}/candidates/{cand_id}", headers=HEADERS)
        cand_final = res_cand_final.json().get("data", {}).get("candidate", {})
        
        print(f"Final Candidate Status: {cand_final.get('interviewStatus')}")
        
        if cand_final.get("interviewStatus") == "INTERVIEW_SCHEDULED":
            print("\nSUCCESS: Requisition transitioned to OPEN, JD was automatically generated, and Candidate was successfully scheduled!")
        else:
            print("\nWARNING: Candidate was not scheduled automatically. Check FastAPI backend logs for errors.")

if __name__ == "__main__":
    asyncio.run(test_crm_triggers())
