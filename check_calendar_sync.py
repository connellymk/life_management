"""
Verify Calendar Events sync results.
"""

from airtable.base_client import AirtableClient

def main():
    client = AirtableClient()
    table = client.get_calendar_events_table()

    # Get sample events
    records = table.all(max_records=10, sort=['Date'])

    print("=" * 60)
    print("CALENDAR SYNC VERIFICATION")
    print("=" * 60)
    print()
    print(f"Total events in table: {len(table.all())}")
    print()
    print("Sample events:")
    print()

    events_with_day_link = 0
    events_without_day_link = 0
    all_day_events = []

    for r in records:
        fields = r['fields']
        title = fields.get('Name', fields.get('Title', 'Unknown'))
        date = fields.get('Date')
        start_time = fields.get('Start Time')
        end_time = fields.get('End Time')
        all_day = fields.get('All Day', False)
        day_link = fields.get('Day')
        duration = fields.get('Duration (min)')

        print(f"Title: {title}")
        print(f"  Date: {date}")
        print(f"  Start: {start_time}")
        print(f"  End: {end_time}")
        print(f"  All Day: {all_day}")
        print(f"  Day Link: {'YES' if day_link else 'NO'}")
        print(f"  Duration: {duration} min")
        print()

        if day_link:
            events_with_day_link += 1
        else:
            events_without_day_link += 1

        if all_day:
            all_day_events.append((title, start_time, end_time))

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Events with Day link: {events_with_day_link}")
    print(f"Events without Day link: {events_without_day_link}")
    print(f"All-day events found: {len(all_day_events)}")
    print()

    if all_day_events:
        print("All-day event times:")
        for title, start, end in all_day_events:
            print(f"  {title}")
            print(f"    Start: {start}")
            print(f"    End: {end}")
        print()

    print("Checks:")
    if events_with_day_link > 0:
        print("  OK Day links are being populated")
    else:
        print("  WARNING No Day links found")

    if all_day_events:
        # Check if all-day events have correct times
        correct_times = all([
            '00:00:00' in start and '23:59:00' in end
            for _, start, end in all_day_events
        ])
        if correct_times:
            print("  OK All-day events have 12:00am-11:59pm times")
        else:
            print("  WARNING All-day event times may not be correct")

    print()


if __name__ == "__main__":
    main()
