"""
Get table IDs from Airtable base for use in table creation.
"""

from pyairtable import Api
from core.config import AirtableConfig

def main():
    access_token = AirtableConfig.AIRTABLE_ACCESS_TOKEN or AirtableConfig.AIRTABLE_API_KEY
    base_id = AirtableConfig.AIRTABLE_BASE_ID

    api = Api(access_token)

    # Get base schema
    print("Fetching base schema...")
    base_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"

    import requests
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(base_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        tables = data.get("tables", [])

        print(f"\nFound {len(tables)} tables in base:\n")

        day_table_id = None
        week_table_id = None

        for table in tables:
            table_name = table.get("name")
            table_id = table.get("id")
            print(f"  {table_name}: {table_id}")

            if table_name == "Day":
                day_table_id = table_id
            elif table_name == "Week":
                week_table_id = table_id

        print(f"\n\nFor use in table creation:")
        print(f"DAY_TABLE_ID = '{day_table_id}'")
        print(f"WEEK_TABLE_ID = '{week_table_id}'")

    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()
