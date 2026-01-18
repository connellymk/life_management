"""
Test script for Airtable integration.
"""

from airtable.base_client import AirtableClient
from airtable.date_utils import date_to_day_id, date_to_week_id
from datetime import datetime

def main():
    print("=" * 60)
    print("AIRTABLE INTEGRATION TEST")
    print("=" * 60)
    print()

    # Test 1: Connection
    print("Test 1: Connection")
    print("-" * 40)
    try:
        client = AirtableClient()
        print(f"SUCCESS: Connected to base {client.base_id}")
    except Exception as e:
        print(f"FAILED: {e}")
        return
    print()

    # Test 2: Date conversion utilities
    print("Test 2: Date Conversion Utilities")
    print("-" * 40)
    test_date = datetime(2026, 1, 17)
    day_id = date_to_day_id(test_date)
    week_id = date_to_week_id(test_date)
    print(f"Test date: {test_date.strftime('%Y-%m-%d')}")
    print(f"Day ID format: {day_id} (expected: d/m/yy)")
    print(f"Week ID format: {week_id} (expected: W-YY)")
    print()

    # Test 3: Table access
    print("Test 3: Table Access")
    print("-" * 40)
    try:
        day_table = client.get_day_table()
        print("SUCCESS: Day table accessible")

        week_table = client.get_week_table()
        print("SUCCESS: Week table accessible")

        calendar_table = client.get_calendar_events_table()
        print("SUCCESS: Calendar Events table accessible")
    except Exception as e:
        print(f"WARNING: {e}")
        print("Some tables may not exist in your base yet")
    print()

    # Test 4: Check Day table records
    print("Test 4: Day Table Records")
    print("-" * 40)
    try:
        day_table = client.get_day_table()
        # Try to get today's record
        formula = f'{{Day}}="{day_id}"'
        records = day_table.all(formula=formula)

        if records:
            print(f"Found {len(records)} record(s) for {day_id}")
            for record in records:
                print(f"  Record ID: {record['id']}")
                print(f"  Fields: {record['fields']}")
        else:
            print(f"No record found for {day_id}")
            print("This is expected if you haven't populated the Day table yet")
    except Exception as e:
        print(f"WARNING: {e}")
    print()

    # Test 5: Check Week table records
    print("Test 5: Week Table Records")
    print("-" * 40)
    try:
        week_table = client.get_week_table()
        # Try to get this week's record
        formula = f'{{Week}}="{week_id}"'
        records = week_table.all(formula=formula)

        if records:
            print(f"Found {len(records)} record(s) for {week_id}")
            for record in records:
                print(f"  Record ID: {record['id']}")
                print(f"  Fields: {record['fields']}")
        else:
            print(f"No record found for {week_id}")
            print("This is expected if you haven't populated the Week table yet")
    except Exception as e:
        print(f"WARNING: {e}")
    print()

    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
