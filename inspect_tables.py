"""
Inspect the structure of Day and Week tables.
"""

from airtable.base_client import AirtableClient

def main():
    print("=" * 60)
    print("INSPECTING AIRTABLE TABLES")
    print("=" * 60)
    print()

    client = AirtableClient()

    # Inspect Day table
    print("DAY TABLE")
    print("-" * 40)
    try:
        day_table = client.get_day_table()
        records = day_table.all(max_records=3)

        if records:
            print(f"Found {len(records)} sample records")
            for i, record in enumerate(records, 1):
                print(f"\nRecord {i}:")
                print(f"  ID: {record['id']}")
                print(f"  Fields: {list(record['fields'].keys())}")
                print(f"  Sample data: {record['fields']}")
        else:
            print("No records found in Day table")
    except Exception as e:
        print(f"Error: {e}")
    print()

    # Inspect Week table
    print("WEEK TABLE")
    print("-" * 40)
    try:
        week_table = client.get_week_table()
        records = week_table.all(max_records=3)

        if records:
            print(f"Found {len(records)} sample records")
            for i, record in enumerate(records, 1):
                print(f"\nRecord {i}:")
                print(f"  ID: {record['id']}")
                print(f"  Fields: {list(record['fields'].keys())}")
                print(f"  Sample data: {record['fields']}")
        else:
            print("No records found in Week table")
    except Exception as e:
        print(f"Error: {e}")
    print()

    # Inspect Calendar Events table (if it exists)
    print("CALENDAR EVENTS TABLE")
    print("-" * 40)
    try:
        cal_table = client.get_calendar_events_table()
        records = cal_table.all(max_records=3)

        if records:
            print(f"Found {len(records)} sample records")
            for i, record in enumerate(records, 1):
                print(f"\nRecord {i}:")
                print(f"  ID: {record['id']}")
                print(f"  Fields: {list(record['fields'].keys())}")
        else:
            print("No records found in Calendar Events table")
            print("This is expected for a new table")
    except Exception as e:
        print(f"Note: {e}")
        print("Calendar Events table may not exist yet")
    print()

    print("=" * 60)

if __name__ == "__main__":
    main()
