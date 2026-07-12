import os
import sys
import httpx
from pathlib import Path

# Add project root to sys.path to easily locate files
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

def load_twenty_env():
    """Helper to parse TWENTY_API_URL and TWENTY_API_KEY from backend/.env"""
    env_path = PROJECT_ROOT / "backend" / ".env"
    if not env_path.exists():
        print(f"Error: Environment file not found at {env_path}")
        print("Please copy backend/.env.example to backend/.env and configure it.")
        sys.exit(1)
        
    env_vars = {}
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                env_vars[key.strip()] = val.strip().strip('"').strip("'")
                
    api_url = env_vars.get("TWENTY_API_URL")
    api_key = env_vars.get("TWENTY_API_KEY")
    
    # Inside docker, TWENTY_API_URL might use host.docker.internal, but from host machine scripts
    # we should connect via localhost:3000 if host.docker.internal is not accessible.
    if api_url and "host.docker.internal" in api_url:
        api_url = api_url.replace("host.docker.internal", "localhost")
        
    if not api_url or not api_key or "your-twenty-api-key" in api_key:
        print("Error: TWENTY_API_URL or TWENTY_API_KEY not configured in backend/.env")
        sys.exit(1)
        
    return api_url, api_key

def get_headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

def create_objects():
    api_url, api_key = load_twenty_env()
    headers = get_headers(api_key)
    
    # 1. Fetch current metadata objects to check what exists
    metadata_url = f"{api_url.rstrip('/')}/rest/metadata/objects"
    print(f"Fetching metadata from {metadata_url}...")
    
    try:
        response = httpx.get(metadata_url, headers=headers, timeout=10.0)
        response.raise_for_status()
        existing_objects = response.json().get("data", [])
    except Exception as e:
        print(f"Failed to query Twenty CRM Metadata API: {e}")
        sys.exit(1)
        
    existing_singulars = {obj["nameSingular"] for obj in existing_objects}
    print(f"Found existing objects: {existing_singulars}")
    
    # Custom objects definition to create
    objects_to_create = [
        {
            "nameSingular": "candidate",
            "namePlural": "candidates",
            "labelSingular": "Candidate",
            "labelPlural": "Candidates",
            "description": "Stores candidate information for recruitment",
            "icon": "IconListNumbers"
        },
        {
            "nameSingular": "requistion",
            "namePlural": "requistions",
            "labelSingular": "Requistion",
            "labelPlural": "Requistions",
            "description": "Stores job requisitions.",
            "icon": "IconBriefcase"
        },
        {
            "nameSingular": "interview",
            "namePlural": "interviews",
            "labelSingular": "Interview",
            "labelPlural": "Interviews",
            "description": "Stores interview sessions and results.",
            "icon": "IconCalendarEvent"
        }
    ]
    
    for obj in objects_to_create:
        name = obj["nameSingular"]
        if name in existing_singulars:
            print(f"Object '{name}' already exists. Skipping.")
        else:
            print(f"Creating custom object '{name}'...")
            try:
                res = httpx.post(metadata_url, headers=headers, json=obj, timeout=15.0)
                if res.status_code in (200, 201):
                    print(f"Successfully created object '{name}' (ID: {res.json().get('id')})")
                else:
                    print(f"Failed to create object '{name}': {res.status_code} - {res.text}")
            except Exception as e:
                print(f"Error creating object '{name}': {e}")

if __name__ == "__main__":
    create_objects()
