#!/usr/bin/env python3
"""
Notion Database Explorer
Query and analyze available Notion databases and their schemas
"""

import os
import sys
from notion_client import Client
import json
from datetime import datetime

def main():
    # Get Notion token from environment
    notion = Client(auth=os.getenv("NOTION_TOKEN"))
    
    print("🔍 Exploring Notion Workspace...")
    print("=" * 50)
    
    try:
        # List all databases the integration has access to
        print("\n📊 Available Databases:")
        print("-" * 30)
        
        # Search for databases
        results = notion.search(filter={"property": "object", "value": "database"})
        
        if not results["results"]:
            print("❌ No databases found. Make sure the integration is connected to your databases.")
            return
        
        databases = []
        for db in results["results"]:
            db_info = {
                "id": db["id"],
                "title": db["title"][0]["plain_text"] if db["title"] else "Untitled",
                "url": db["url"],
                "properties": db["properties"]
            }
            databases.append(db_info)
            
            print(f"\n📋 Database: {db_info['title']}")
            print(f"   ID: {db_info['id']}")
            print(f"   URL: {db_info['url']}")
            print(f"   Properties ({len(db_info['properties'])}):")
            
            for prop_name, prop_config in db_info['properties'].items():
                prop_type = prop_config['type']
                print(f"     • {prop_name}: {prop_type}")
                
                # Show additional details for specific property types
                if prop_type == "select" and "select" in prop_config:
                    options = [opt["name"] for opt in prop_config["select"]["options"]]
                    print(f"       Options: {', '.join(options)}")
                elif prop_type == "multi_select" and "multi_select" in prop_config:
                    options = [opt["name"] for opt in prop_config["multi_select"]["options"]]
                    print(f"       Options: {', '.join(options)}")
                elif prop_type == "relation" and "relation" in prop_config:
                    related_db = prop_config["relation"]["database_id"]
                    print(f"       Related DB: {related_db}")
        
        # Save detailed info to file
        with open("notion_database_analysis.json", "w") as f:
            json.dump({
                "analyzed_at": datetime.now().isoformat(),
                "databases": databases
            }, f, indent=2)
        
        print(f"\n✅ Analysis complete! Found {len(databases)} database(s)")
        print("📄 Detailed analysis saved to: notion_database_analysis.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())