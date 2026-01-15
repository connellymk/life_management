#!/usr/bin/env python3
"""
Quick script to check for duplicate events in Notion
"""

from notion_client import Client
from core.config import GoogleCalendarConfig as Config
from collections import defaultdict

def main():
    client = Client(auth=Config.NOTION_TOKEN)

    # Fetch all pages from the database
    all_pages = []
    has_more = True
    start_cursor = None

    print("Fetching events from Notion...")

    while has_more:
        kwargs = {"database_id": Config.NOTION_CALENDAR_DB_ID}
        if start_cursor:
            kwargs["start_cursor"] = start_cursor

        response = client.databases.query(**kwargs)
        all_pages.extend(response["results"])
        has_more = response.get("has_more", False)
        start_cursor = response.get("next_cursor")
        print(f"  Fetched {len(all_pages)} events so far...")

    print(f"\nTotal events in database: {len(all_pages)}")

    # Group by external ID
    external_ids = defaultdict(list)
    no_external_id = []

    for page in all_pages:
        external_id_prop = page["properties"].get("External ID", {})
        rich_text = external_id_prop.get("rich_text", [])

        if rich_text and len(rich_text) > 0:
            external_id = rich_text[0]["text"]["content"]
            external_ids[external_id].append(page["id"])
        else:
            no_external_id.append(page["id"])

    # Find duplicates
    duplicates = {ext_id: page_ids for ext_id, page_ids in external_ids.items() if len(page_ids) > 1}

    print(f"\nEvents with external IDs: {len(external_ids)}")
    print(f"Events without external IDs: {len(no_external_id)}")
    print(f"Duplicate external IDs found: {len(duplicates)}")

    if duplicates:
        print("\n⚠️  DUPLICATES FOUND:")
        for ext_id, page_ids in list(duplicates.items())[:10]:  # Show first 10
            print(f"  External ID: {ext_id}")
            print(f"    Notion page IDs: {page_ids}")
    else:
        print("\n✅ No duplicates found based on External ID")

    if no_external_id:
        print(f"\n⚠️  {len(no_external_id)} events have NO external ID (these could be duplicates)")

if __name__ == "__main__":
    main()
