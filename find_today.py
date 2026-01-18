"""Find today's record in Day table."""

from airtable.base_client import AirtableClient
from datetime import datetime

client = AirtableClient()
day_table = client.get_day_table()

# Get all January 2026 records
formula = 'AND(YEAR({Day})=2026, MONTH({Day})=1)'
records = day_table.all(formula=formula, max_records=31, sort=['Day'])

print(f"January 2026 records: {len(records)} total")
if records:
    print("\nAll January dates:")
    for r in records:
        day_value = r['fields'].get('Day')
        print(f"  {day_value}")

    # Check for today specifically
    today_iso = "2026-01-17"
    today_record = [r for r in records if r['fields'].get('Day') == today_iso]

    if today_record:
        print(f"\nFound record for today ({today_iso})!")
        print(f"Record ID: {today_record[0]['id']}")
        print(f"All fields: {today_record[0]['fields']}")
    else:
        print(f"\nNo record found for today ({today_iso})")
else:
    print("\nNo January 2026 records found in Day table")
