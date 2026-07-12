import os
import sys
import httpx
from pathlib import Path
from create_objects import load_twenty_env, get_headers

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def create_relationships():
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
    
    # Ensure our required objects are present
    for req_obj in ("candidate", "requistion", "interview"):
        if req_obj not in obj_map:
            print(f"Error: Custom object '{req_obj}' is missing. Run create_objects.py first.")
            sys.exit(1)
            
    candidate_id = obj_map["candidate"]["id"]
    requisition_id = obj_map["requistion"]["id"]
    interview_id = obj_map["interview"]["id"]
    
    # Relationships definition to create as RELATION fields
    relationships_to_create = [
        # 1. interview -> candidate (MANY_TO_ONE)
        {
            "source_obj": "interview",
            "source_id": interview_id,
            "field_name": "candidate",
            "field_payload": {
                "name": "candidate",
                "label": "Candidate",
                "type": "RELATION",
                "objectMetadataId": interview_id,
                "relationCreationPayload": {
                    "targetObjectMetadataId": candidate_id,
                    "type": "MANY_TO_ONE",
                    "targetFieldLabel": "Interviews",
                    "targetFieldName": "interviews",
                    "targetFieldIcon": "IconRelationOneToMany"
                }
            }
        },
        # 2. requistion -> candidate (MANY_TO_ONE: listing -> requisitions)
        {
            "source_obj": "requistion",
            "source_id": requisition_id,
            "field_name": "listing",
            "field_payload": {
                "name": "listing",
                "label": "Listing",
                "type": "RELATION",
                "objectMetadataId": requisition_id,
                "relationCreationPayload": {
                    "targetObjectMetadataId": candidate_id,
                    "type": "MANY_TO_ONE",
                    "targetFieldLabel": "Requisitions",
                    "targetFieldName": "requisitions",
                    "targetFieldIcon": "IconRelationOneToMany"
                }
            }
        },
        # 3. requistion -> candidate (MANY_TO_ONE: candidate -> candidates)
        {
            "source_obj": "requistion",
            "source_id": requisition_id,
            "field_name": "candidate",
            "field_payload": {
                "name": "candidate",
                "label": "Candidate",
                "type": "RELATION",
                "objectMetadataId": requisition_id,
                "relationCreationPayload": {
                    "targetObjectMetadataId": candidate_id,
                    "type": "MANY_TO_ONE",
                    "targetFieldLabel": "Candidates",
                    "targetFieldName": "candidates",
                    "targetFieldIcon": "IconRelationOneToMany"
                }
            }
        }
    ]
    
    fields_url = f"{api_url.rstrip('/')}/rest/metadata/fields"
    
    for rel_def in relationships_to_create:
        source_obj_name = rel_def["source_obj"]
        field_name = rel_def["field_name"]
        
        # Check if the field already exists on the source object
        existing_fields = {f["name"] for f in obj_map[source_obj_name].get("fields", [])}
        if field_name in existing_fields:
            print(f"Relation field '{field_name}' already exists on object '{source_obj_name}'. Skipping.")
        else:
            print(f"Creating relation '{field_name}' on custom object '{source_obj_name}'...")
            try:
                res = httpx.post(fields_url, headers=headers, json=rel_def["field_payload"], timeout=20.0)
                if res.status_code in (200, 201):
                    print(f"Successfully created relation field '{field_name}' (ID: {res.json().get('id')})")
                else:
                    print(f"Failed to create relation field '{field_name}': {res.status_code} - {res.text}")
            except Exception as e:
                print(f"Error creating relation field '{field_name}': {e}")

if __name__ == "__main__":
    create_relationships()
