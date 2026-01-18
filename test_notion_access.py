#!/usr/bin/env python3
"""
Test Notion access and search for training plan database.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from notion_client import Client as NotionClient
from core.config import Config

def test_notion_connection():
    """Test Notion connection and search for databases."""
    print("Testing Notion connection...")

    try:
        notion = NotionClient(auth=Config.NOTION_TOKEN)

        # Search for databases (now called data_sources in the API)
        print("\nSearching for data sources (databases)...")
        response = notion.search(
            filter={"property": "object", "value": "data_source"}
        )

        databases = response.get("results", [])
        print(f"Found {len(databases)} databases:\n")

        for db in databases:
            db_id = db.get("id", "N/A")
            title_list = db.get("title", [])
            title = "".join([t.get("plain_text", "") for t in title_list]) if title_list else "Untitled"
            print(f"  - {title}")
            print(f"    ID: {db_id}")
            print(f"    URL: {db.get('url', 'N/A')}\n")

        # Also search for pages
        print("\nSearching for pages with 'training' in the title...")
        response = notion.search(
            query="training",
            filter={"property": "object", "value": "page"}
        )

        pages = response.get("results", [])
        print(f"Found {len(pages)} pages:\n")

        for page in pages[:5]:  # Show first 5
            page_id = page.get("id", "N/A")
            props = page.get("properties", {})
            title_prop = props.get("title", {})
            title_list = title_prop.get("title", [])
            title = "".join([t.get("plain_text", "") for t in title_list]) if title_list else "Untitled"
            print(f"  - {title}")
            print(f"    ID: {page_id}")
            print(f"    URL: {page.get('url', 'N/A')}\n")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_notion_connection()
