import sys
import httpx
from pathlib import Path

# Add scripts directory to path to allow importing modules
scripts_dir = Path(__file__).resolve().parent
sys.path.append(str(scripts_dir))

from create_objects import load_twenty_env, get_headers

def verify_schema():
    print("==================================================")
    print("Verifying Twenty CRM Recruiting Platform Data Model")
    print("==================================================")
    
    api_url, api_key = load_twenty_env()
    headers = get_headers(api_key)
    
    metadata_url = f"{api_url.rstrip('/')}/rest/metadata/objects"
    
    try:
        response = httpx.get(metadata_url, headers=headers, timeout=10.0)
        response.raise_for_status()
        objects = response.json().get("data", [])
    except Exception as e:
        print(f"Failed to query objects metadata: {e}")
        sys.exit(1)
        
    obj_map = {obj["nameSingular"]: obj for obj in objects}
    
    expected_schema = {
        "candidate": {
            "fields": {
                "name": "TEXT",
                "overallScore": "NUMBER",
                "resumeUrl": "TEXT",
                "transcript": "TEXT",
                "sentiment": "SELECT",
                "interviewStatus": "SELECT"
            },
            "relations": {
                "interviews": "ONE_TO_MANY",
                "requisitions": "ONE_TO_MANY"
            }
        },
        "requistion": {
            "fields": {
                "name": "TEXT",
                "jobTitle": "TEXT",
                "jobDescription": "TEXT",
                "experience": "TEXT",
                "department": "TEXT",
                "requiredSkills": "TEXT",
                "location": "TEXT",
                "employmentType": "SELECT",
                "status": "SELECT"
            },
            "relations": {
                "listing": "MANY_TO_ONE",
                "candidate": "MANY_TO_ONE",
                "candidates": "ONE_TO_MANY"
            }
        },
        "interview": {
            "fields": {
                "name": "TEXT"
            },
            "relations": {
                "candidate": "MANY_TO_ONE"
            }
        }
    }
    
    all_passed = True
    
    for obj_name, expected in expected_schema.items():
        print(f"\nAnalyzing Object: '{obj_name}'...")
        if obj_name not in obj_map:
            print(f"    [FAILED] Custom object '{obj_name}' is missing entirely!")
            all_passed = False
            continue
            
        obj = obj_map[obj_name]
        print(f"  ID: {obj['id']}")
        print("  Checking Fields:")
        
        # Verify fields
        existing_fields = {f["name"]: f for f in obj.get("fields", [])}
        for field_name, expected_type in expected["fields"].items():
            if field_name not in existing_fields:
                print(f"    [MISSING] Field '{field_name}' ({expected_type}) is missing!")
                all_passed = False
            else:
                field = existing_fields[field_name]
                print(f"    [OK] Field '{field_name}' matches (Type: {field['type']})")
                
        # Verify relations
        print("  Checking Relationships:")
        for rel_field, expected_rel_type in expected["relations"].items():
            if rel_field not in existing_fields:
                print(f"    [MISSING] Relationship field '{rel_field}' is missing!")
                all_passed = False
            else:
                field = existing_fields[rel_field]
                actual_rel_type = field.get("settings", {}).get("relationType")
                if actual_rel_type != expected_rel_type:
                    print(f"    [ERROR] Relationship '{rel_field}' has type '{actual_rel_type}', expected '{expected_rel_type}'!")
                    all_passed = False
                else:
                    print(f"    [OK] Relationship '{rel_field}' matches (Type: {actual_rel_type})")
                    
    print("\n==================================================")
    if all_passed:
        print("    SUCCESS: CRM Data Model matches your layout 100%!")
        print("==================================================")
    else:
        print("    WARNING: Mismatches or missing elements found in CRM Data Model.")
        print("==================================================")
        sys.exit(1)

if __name__ == "__main__":
    verify_schema()
