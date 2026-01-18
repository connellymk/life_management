"""Check if Day table has records for event dates."""

from airtable.base_client import AirtableClient

client = AirtableClient()
day_table = client.get_day_table()

dates_to_check = ['2026-01-13', '2026-01-14', '2026-01-15', '2026-01-16', '2026-01-17']

print("Checking Day table for event dates:")
print()

for date_str in dates_to_check:
    formula = f'{{Day}}="{date_str}"'
    records = day_table.all(formula=formula, max_records=1)
    status = "FOUND" if records else "NOT FOUND"
    print(f"  {date_str}: {status}")
    if records:
        print(f"    Record ID: {records[0]['id']}")

print()
