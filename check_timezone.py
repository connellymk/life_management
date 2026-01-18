"""
Check that event times are in Mountain Time.
"""

from airtable.base_client import AirtableClient
from datetime import datetime

def main():
    client = AirtableClient()
    table = client.get_calendar_events_table()

    # Get timed events (not all-day)
    records = table.all(formula='NOT({All Day})', max_records=10, sort=['Date'])

    print("=" * 60)
    print("TIMEZONE VERIFICATION - Mountain Time (Bozeman, MT)")
    print("=" * 60)
    print()
    print("Sample timed events (NOT all-day):")
    print()

    for r in records:
        fields = r['fields']
        title = fields.get('Name', fields.get('Title', 'Unknown'))
        start = fields.get('Start Time')
        end = fields.get('End Time')

        print(f"Event: {title}")
        print(f"  Start: {start}")
        print(f"  End: {end}")

        # Check if time looks reasonable for Mountain Time
        if start:
            # Parse the ISO time
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            hour = start_dt.hour
            print(f"  Start hour (UTC): {hour}")
            # Mountain Time is UTC-7 (MST) or UTC-6 (MDT)
            # So if an event shows 8:00 AM local, it should be around 14:00-15:00 UTC
            # After conversion, should show around 8:00 AM
        print()

    print("=" * 60)
    print()
    print("Note: Times should be in Mountain Time format")
    print("Example: 8:00 AM class should show as 08:00:00 (not 15:00:00 UTC)")
    print()


if __name__ == "__main__":
    main()
