#!/usr/bin/env python3
"""
Debug script to identify calendar duplicate issues
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from notion.calendar import NotionSync
from core.state_manager import StateManager
from core.config import Config

def main():
    print("=" * 60)
    print("Calendar Duplicate Diagnostics")
    print("=" * 60)

    # Initialize
    state_manager = StateManager()
    notion = NotionSync(state_manager=state_manager)

    # Get all events from Notion
    print("\n1. Fetching all events from Notion database...")
    all_events = notion.get_all_events(limit=1000)
    print(f"   Found {len(all_events)} events in Notion")

    # Group by External ID
    print("\n2. Checking for duplicate External IDs...")
    external_ids = {}
    for event in all_events:
        props = event.get("properties", {})
        external_id_prop = props.get("External ID", {}).get("rich_text", [])

        if external_id_prop:
            external_id = external_id_prop[0].get("text", {}).get("content", "")
            title_prop = props.get("Title", {}).get("title", [])
            title = title_prop[0].get("text", {}).get("content", "No title") if title_prop else "No title"

            if external_id not in external_ids:
                external_ids[external_id] = []
            external_ids[external_id].append({
                "id": event["id"],
                "title": title
            })

    # Find duplicates
    duplicates = {k: v for k, v in external_ids.items() if len(v) > 1}

    if duplicates:
        print(f"   ❌ Found {len(duplicates)} duplicate External IDs!")
        print("\n   Duplicates:")
        for external_id, events in list(duplicates.items())[:10]:  # Show first 10
            print(f"\n   External ID: {external_id}")
            for event in events:
                print(f"     - {event['title']} (Page ID: {event['id'][:8]}...)")

        if len(duplicates) > 10:
            print(f"\n   ... and {len(duplicates) - 10} more duplicate groups")
    else:
        print("   ✓ No duplicates found based on External ID")

    # Check state manager mappings
    print("\n3. Checking state manager mappings...")
    calendar_mappings = state_manager.count_mappings("calendar")
    print(f"   State manager has {calendar_mappings} calendar event mappings")

    if calendar_mappings != len(external_ids):
        print(f"   ⚠ Mismatch: Notion has {len(external_ids)} unique events, but state manager has {calendar_mappings} mappings")
        print("   This could cause duplicates on next sync!")
    else:
        print("   ✓ State manager and Notion are in sync")

    # Recommendations
    print("\n" + "=" * 60)
    print("Recommendations:")
    print("=" * 60)

    if duplicates:
        print("\n✗ You have duplicates in your Notion database.")
        print("  To fix:")
        print("  1. Delete all events from the Notion database")
        print("  2. Reset the state manager:")
        print("     python -c \"from core.state_manager import StateManager; StateManager().reset_state()\"")
        print("  3. Run the sync again")
    elif calendar_mappings == 0 and len(all_events) > 0:
        print("\n⚠ Notion has events but state manager is empty.")
        print("  This will cause duplicates on next sync!")
        print("  To fix:")
        print("  1. Delete all events from the Notion database")
        print("  2. Run the sync again to populate fresh")
    else:
        print("\n✓ Everything looks good!")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
