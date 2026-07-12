# Script to bootstrap and verify workspace setup
import os
import sys
from pathlib import Path

# Add scripts directory to path to allow importing modules
scripts_dir = Path(__file__).resolve().parent
sys.path.append(str(scripts_dir))

from create_objects import create_objects
from create_fields import create_fields
from create_relationships import create_relationships

def main():
    print("==================================================")
    print("Initializing Openclaw Recruiting Platform CRM Setup")
    print("==================================================")
    
    print("\n[Step 1/3] Creating Custom Objects...")
    create_objects()
    
    print("\n[Step 2/3] Creating Custom Fields...")
    create_fields()
    
    print("\n[Step 3/3] Creating Object Relationships...")
    create_relationships()
    
    print("\n==================================================")
    print("CRM Setup successfully completed!")
    print("==================================================")

if __name__ == "__main__":
    main()
