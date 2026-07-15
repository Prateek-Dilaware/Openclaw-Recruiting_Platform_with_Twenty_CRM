import sys
import httpx
from pathlib import Path

# Add scripts directory to path to allow importing modules
scripts_dir = Path(__file__).resolve().parent
sys.path.append(str(scripts_dir))

try:
    from .create_objects import load_twenty_env, get_headers
except ImportError:  # Supports direct historical execution from this folder.
    from create_objects import load_twenty_env, get_headers

def seed_data():
    print("==================================================")
    print("Seeding Demo Data in Twenty CRM")
    print("==================================================")
    
    api_url, api_key = load_twenty_env()
    headers = get_headers(api_key)
    
    base_rest_url = f"{api_url.rstrip('/')}/rest"
    
    # 1. Create a candidate
    cand_payloads = [
        {
            "name": "John Doe",
            "email": {
                "primaryEmail": "john.doe@example.com",
                "additionalEmails": []
            },
            "phone": {
                "primaryPhoneNumber": "1234567890",
                "primaryPhoneCountryCode": "",
                "primaryPhoneCallingCode": "+1",
                "additionalPhones": []
            },
            "resumeUrl": "https://example.com/john_doe_resume.pdf",
            "interviewStatus": "APPLIED",
            "overallScore": 0,
            "transcript": "",
            "sentiment": "NEUTRAL"
        },
        {
            "name": "Jane Smith",
            "email": {
                "primaryEmail": "jane.smith@example.com",
                "additionalEmails": []
            },
            "phone": {
                "primaryPhoneNumber": "9876543210",
                "primaryPhoneCountryCode": "",
                "primaryPhoneCallingCode": "+1",
                "additionalPhones": []
            },
            "resumeUrl": "https://example.com/jane_smith_resume.pdf",
            "interviewStatus": "APPLIED",
            "overallScore": 0,
            "transcript": "",
            "sentiment": "NEUTRAL"
        }
    ]
    
    created_cand_ids = []
    
    print("\nSeeding Candidates...")
    for cand in cand_payloads:
        try:
            res = httpx.post(f"{base_rest_url}/candidates", headers=headers, json=cand, timeout=10.0)
            if res.status_code in (200, 201):
                data = res.json().get("data", {}).get("createCandidate", {}) or res.json()
                cand_id = data.get("id")
                created_cand_ids.append(cand_id)
                print(f"  [OK] Created Candidate: '{cand['name']}' (ID: {cand_id})")
            else:
                print(f"  [FAILED] Failed to create Candidate '{cand['name']}': {res.status_code} - {res.text}")
        except Exception as e:
            print(f"  Error creating Candidate '{cand['name']}': {e}")
            
    # 2. Create Requisitions and link them
    req_payloads = [
        {
            "name": "Senior Python Developer Requisition",
            "jobTitle": "Senior Python Developer",
            "department": "Engineering",
            "jobDescription": "Looking for a Python dev experienced in FastAPI, Docker, and PostgreSQL...",
            "requiredSkills": "Python, FastAPI, Docker, PostgreSQL",
            "experience": "5+ Years",
            "location": "Remote",
            "employmentType": "FULL_TIME",
            "status": "OPEN",
            "listingId": created_cand_ids[0] if len(created_cand_ids) > 0 else None
        },
        {
            "name": "React Developer Requisition",
            "jobTitle": "React Developer",
            "department": "Engineering",
            "jobDescription": "Looking for a frontend developer strong in React, Vite, and CSS...",
            "requiredSkills": "React, Vite, CSS, JavaScript",
            "experience": "2+ Years",
            "location": "Pune",
            "employmentType": "FULL_TIME",
            "status": "DRAFT",
            "listingId": created_cand_ids[1] if len(created_cand_ids) > 1 else None
        }
    ]
    
    print("\nSeeding Requisitions...")
    for req in req_payloads:
        try:
            res = httpx.post(f"{base_rest_url}/requistions", headers=headers, json=req, timeout=10.0)
            if res.status_code in (200, 201):
                data = res.json().get("data", {}).get("createRequistion", {}) or res.json()
                req_id = data.get("id")
                print(f"  [OK] Created Requisition: '{req['jobTitle']}' (ID: {req_id}) linked to Candidate ID: {req['listingId']}")
            else:
                print(f"  [FAILED] Failed to create Requisition '{req['jobTitle']}': {res.status_code} - {res.text}")
        except Exception as e:
            print(f"  Error creating Requisition '{req['jobTitle']}': {e}")
            
    print("\n==================================================")
    print("Database seeding completed!")
    print("==================================================")

if __name__ == "__main__":
    seed_data()
