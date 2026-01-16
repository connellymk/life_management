#!/usr/bin/env python3
"""
Fix calendar sync issues by resetting state and re-syncing fresh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.state_manager import StateManager

def main():
    print("\n" + "=" * 60)
    print("Calendar Sync Fix Script")
    print("=" * 60)

    print("\nThis script will:")
    print("1. Clear all calendar event mappings from the state database")
    print("2. Clear sync tokens for Google calendars")
    print("\nAfter running this, you should:")
    print("- Delete all events from your Notion Calendar database")
    print("- Run the calendar sync again")

    response = input("\nContinue? (yes/no): ").strip().lower()
    if response != "yes":
        print("Aborted.")
        return

    state_manager = StateManager()

    # Reset all calendar-related state
    print("\nResetting calendar sync state...")

    # Method 1: Reset by source pattern
    import sqlite3
    conn = sqlite3.connect('state.db')
    cursor = conn.cursor()

    # Delete all calendar event mappings
    cursor.execute("DELETE FROM event_mapping WHERE event_type = 'calendar'")
    deleted_mappings = cursor.rowcount
    print(f"  Deleted {deleted_mappings} calendar event mappings")

    # Delete sync tokens for Google calendars
    cursor.execute("DELETE FROM sync_state WHERE source LIKE 'google_%'")
    deleted_tokens = cursor.rowcount
    print(f"  Deleted {deleted_tokens} sync tokens")

    # Delete sync history for calendar syncs
    cursor.execute("DELETE FROM sync_history WHERE source LIKE 'google_%'")
    deleted_history = cursor.rowcount
    print(f"  Deleted {deleted_history} sync history records")

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("State database cleared successfully!")
    print("=" * 60)

    print("\nNext steps:")
    print("1. Go to your Notion Calendar Events database")
    print("2. Delete ALL events (select all and delete)")
    print("3. Run the calendar sync:")
    print("   python orchestrators/sync_calendar.py")
    print("\nThis will create a fresh sync with no duplicates.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
