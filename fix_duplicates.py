#!/usr/bin/env python3
"""
Fix duplicate events by keeping older pages and deleting newer duplicates
"""

import sqlite3
from notion_client import Client
from core.config import GoogleCalendarConfig as Config
from datetime import datetime

def main():
    # Connect to databases
    new_db = sqlite3.connect('state.db')
    old_db = sqlite3.connect('_archive/calendar-sync/state.db')

    # Get all mappings from both databases
    old_cursor = old_db.cursor()
    new_cursor = new_db.cursor()

    old_mappings = {}
    for row in old_cursor.execute('SELECT external_id, notion_page_id, created_at FROM event_mapping'):
        old_mappings[row[0]] = (row[1], row[2])

    new_mappings = {}
    for row in new_cursor.execute('SELECT external_id, notion_page_id, created_at FROM event_mapping'):
        new_mappings[row[0]] = (row[1], row[2])

    # Find duplicates
    duplicates = set(old_mappings.keys()) & set(new_mappings.keys())
    print(f"Found {len(duplicates)} duplicate event mappings")

    if not duplicates:
        print("No duplicates found!")
        return

    # For each duplicate, identify which is older
    pages_to_delete = []
    pages_to_keep = []

    for external_id in duplicates:
        old_page_id, old_created = old_mappings[external_id]
        new_page_id, new_created = new_mappings[external_id]

        # Keep the older page, delete the newer one
        if old_created < new_created:
            pages_to_delete.append(new_page_id)
            pages_to_keep.append(old_page_id)
        else:
            pages_to_delete.append(old_page_id)
            pages_to_keep.append(new_page_id)

    print(f"\nWill delete {len(pages_to_delete)} duplicate pages (keeping the older versions)")
    print(f"Will keep {len(pages_to_keep)} original pages")
    print("\nProceeding with deletion...")

    # Delete duplicate pages from Notion
    client = Client(auth=Config.NOTION_TOKEN)
    deleted_count = 0
    errors = 0

    print(f"\nDeleting {len(pages_to_delete)} duplicate pages...")
    for i, page_id in enumerate(pages_to_delete, 1):
        try:
            # Archive (soft delete) the page
            client.pages.update(page_id=page_id, archived=True)
            deleted_count += 1
            if i % 10 == 0:
                print(f"  Deleted {i}/{len(pages_to_delete)}...")
        except Exception as e:
            print(f"  Error deleting page {page_id}: {e}")
            errors += 1

    print(f"\n✅ Deleted {deleted_count} duplicate pages")
    if errors > 0:
        print(f"⚠️  {errors} errors occurred")

    # Now merge the old state database into the new one
    # We want to keep the old mappings (since they point to the older pages we kept)
    print(f"\nUpdating state database...")

    # For each duplicate external_id, update the new database to point to the old page
    updated = 0
    for external_id in duplicates:
        old_page_id, old_created = old_mappings[external_id]
        try:
            new_cursor.execute(
                'UPDATE event_mapping SET notion_page_id = ?, created_at = ? WHERE external_id = ?',
                (old_page_id, old_created, external_id)
            )
            updated += 1
        except Exception as e:
            print(f"  Error updating mapping for {external_id}: {e}")

    new_db.commit()
    print(f"✅ Updated {updated} mappings in state database")

    # Close connections
    old_db.close()
    new_db.close()

    print(f"\n🎉 Done! Duplicates have been cleaned up.")
    print(f"   - Deleted {deleted_count} duplicate pages from Notion")
    print(f"   - Updated {updated} mappings in state database")

if __name__ == "__main__":
    main()
