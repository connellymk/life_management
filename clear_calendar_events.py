"""
Clear all Calendar Events from Airtable for re-sync testing.
"""

from airtable.base_client import AirtableClient
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def main():
    print("=" * 60)
    print("CLEAR CALENDAR EVENTS")
    print("=" * 60)
    print()

    client = AirtableClient()
    table = client.get_calendar_events_table()

    print("Fetching all Calendar Events...")
    records = table.all()

    if not records:
        print("No events to delete.")
        return

    print(f"Found {len(records)} events to delete")
    print()
    print("Deleting events...")

    for i, record in enumerate(records, 1):
        record_id = record['id']
        title = record['fields'].get('Title', record['fields'].get('Name', 'Unknown'))
        table.delete(record_id)
        if i % 10 == 0:
            print(f"  Deleted {i}/{len(records)}...")

    print(f"  Deleted {len(records)}/{len(records)}")
    print()
    print("All Calendar Events deleted!")
    print("Run test_calendar_sync.py to re-sync with updated logic.")
    print()


if __name__ == "__main__":
    main()
