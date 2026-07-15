import os
import sys
import httpx
from pathlib import Path
try:
    from .create_objects import load_twenty_env, get_headers
except ImportError:  # Supports direct historical execution from this folder.
    from create_objects import load_twenty_env, get_headers

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def create_fields():
    api_url, api_key = load_twenty_env()
    headers = get_headers(api_key)
    
    # 1. Fetch metadata objects to resolve singular name to ID and see existing fields
    metadata_url = f"{api_url.rstrip('/')}/rest/metadata/objects"
    try:
        response = httpx.get(metadata_url, headers=headers, timeout=10.0)
        response.raise_for_status()
        objects = response.json().get("data", [])
    except Exception as e:
        print(f"Failed to query objects metadata: {e}")
        sys.exit(1)
        
    obj_map = {obj["nameSingular"]: obj for obj in objects}
    
    # Ensure our required objects are present before continuing
    for req_obj in ("candidate", "requistion", "interview"):
        if req_obj not in obj_map:
            print(f"Error: Custom object '{req_obj}' is missing. Run create_objects.py first.")
            sys.exit(1)
            
    # Define custom fields to create on each object
    fields_to_create = {
        "candidate": [
            {
                "name": "overallScore",
                "label": "Overall score",
                "type": "NUMBER",
                "settings": {"type": "number", "decimals": 0}
            },
            {
                "name": "resumeUrl",
                "label": "Resume URL",
                "type": "TEXT",
                "settings": {"displayedMaxRows": 0}
            },
            {
                "name": "transcript",
                "label": "Transcript",
                "type": "TEXT",
                "settings": {"displayedMaxRows": 99}
            },
            {
                "name": "sentiment",
                "label": "Sentiment",
                "type": "SELECT",
                "options": [
                    {"label": "Very Positive", "value": "VERY_POSITIVE", "color": "green", "position": 0},
                    {"label": "Positive", "value": "POSITIVE", "color": "jade", "position": 1},
                    {"label": "Neutral", "value": "NEUTRAL", "color": "mint", "position": 2},
                    {"label": "Negative", "value": "NEGATIVE", "color": "turquoise", "position": 3},
                    {"label": "Very Negative", "value": "VERY_NEGATIVE", "color": "cyan", "position": 4}
                ]
            },
            {
                "name": "interviewStatus",
                "label": "Interview Status",
                "type": "SELECT",
                "options": [
                    {"label": "Applied", "value": "APPLIED", "color": "green", "position": 0},
                    {"label": "Screening", "value": "SCREENING", "color": "jade", "position": 1},
                    {"label": "Interview_scheduled", "value": "INTERVIEW_SCHEDULED", "color": "mint", "position": 2},
                    {"label": "Interview_completed", "value": "INTERVIEW_COMPLETED", "color": "turquoise", "position": 3},
                    {"label": "Shorlisted", "value": "SHORLISTED", "color": "cyan", "position": 4},
                    {"label": "Rejected", "value": "REJECTED", "color": "sky", "position": 5},
                    {"label": "Hired", "value": "HIRED", "color": "blue", "position": 6},
                    {"label": "Option 8", "value": "OPTION_8", "color": "iris", "position": 7}
                ]
            }
        ],
        "requistion": [
            {
                "name": "jobTitle",
                "label": "Job Title",
                "type": "TEXT",
                "settings": {"displayedMaxRows": 0}
            },
            {
                "name": "jobDescription",
                "label": "Job Description",
                "type": "TEXT",
                "settings": {"displayedMaxRows": 99}
            },
            {
                "name": "experience",
                "label": "Experience",
                "type": "TEXT",
                "settings": {"displayedMaxRows": 0}
            },
            {
                "name": "department",
                "label": "Department",
                "type": "TEXT",
                "settings": {"displayedMaxRows": 0}
            },
            {
                "name": "requiredSkills",
                "label": "Required Skills",
                "type": "TEXT",
                "settings": {"displayedMaxRows": 99}
            },
            {
                "name": "location",
                "label": "Location",
                "type": "TEXT",
                "settings": {"displayedMaxRows": 0}
            },
            {
                "name": "employmentType",
                "label": "Employment Type",
                "type": "SELECT",
                "options": [
                    {"label": "Full-Time", "value": "FULL_TIME", "color": "green", "position": 0},
                    {"label": "Part-Time", "value": "PART_TIME", "color": "jade", "position": 1},
                    {"label": "Internship", "value": "INTERNSHIP", "color": "mint", "position": 2},
                    {"label": "Option 4", "value": "OPTION_4", "color": "turquoise", "position": 3}
                ]
            },
            {
                "name": "status",
                "label": "Status",
                "type": "SELECT",
                "options": [
                    {"label": "Draft", "value": "DRAFT", "color": "green", "position": 0},
                    {"label": "Open", "value": "OPEN", "color": "jade", "position": 1},
                    {"label": "In review", "value": "IN_REVIEW", "color": "mint", "position": 2},
                    {"label": "Closed", "value": "CLOSED", "color": "turquoise", "position": 3},
                    {"label": "On Hold", "value": "ON_HOLD", "color": "cyan", "position": 4}
                ]
            }
        ]
    }
    
    fields_url = f"{api_url.rstrip('/')}/rest/metadata/fields"
    
    for obj_name, fields in fields_to_create.items():
        obj_id = obj_map[obj_name]["id"]
        existing_fields = {f["name"] for f in obj_map[obj_name].get("fields", [])}
        
        for field_def in fields:
            field_name = field_def["name"]
            if field_name in existing_fields:
                print(f"Field '{field_name}' already exists on object '{obj_name}'. Skipping.")
            else:
                print(f"Creating field '{field_name}' on custom object '{obj_name}'...")
                # Inject objectMetadataId into creation payload
                payload = field_def.copy()
                payload["objectMetadataId"] = obj_id
                
                try:
                    res = httpx.post(fields_url, headers=headers, json=payload, timeout=15.0)
                    if res.status_code in (200, 201):
                        print(f"Successfully created field '{field_name}' (ID: {res.json().get('id')})")
                    else:
                        print(f"Failed to create field '{field_name}': {res.status_code} - {res.text}")
                except Exception as e:
                    print(f"Error creating field '{field_name}': {e}")

if __name__ == "__main__":
    create_fields()
