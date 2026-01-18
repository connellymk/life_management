"""
Fix the missing link and checkbox fields that failed during initial creation.
"""

import requests
from core.config import AirtableConfig
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def add_field(base_url, headers, table_id, field_config):
    """Add a single field to a table."""
    url = f"{base_url}/{table_id}/fields"
    response = requests.post(url, headers=headers, json=field_config)

    if response.status_code in (200, 201):
        logger.info(f"  + Added field: {field_config['name']}")
        return True
    else:
        error_msg = response.json().get('error', {}).get('message', response.text)
        logger.warning(f"  x Failed to add {field_config['name']}: {error_msg}")
        return False


def main():
    print("=" * 60)
    print("FIX MISSING FIELDS")
    print("=" * 60)
    print()

    access_token = AirtableConfig.AIRTABLE_ACCESS_TOKEN or AirtableConfig.AIRTABLE_API_KEY
    base_id = AirtableConfig.AIRTABLE_BASE_ID
    base_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Get table IDs
    response = requests.get(base_url, headers=headers)
    if response.status_code != 200:
        logger.error(f"Failed to fetch tables: {response.text}")
        return

    tables = {table["name"]: table["id"] for table in response.json().get("tables", [])}

    day_table_id = tables.get("Day")
    week_table_id = tables.get("Week")

    logger.info(f"Day table ID: {day_table_id}")
    logger.info(f"Week table ID: {week_table_id}")
    logger.info("")

    # Fix Calendar Events
    if "Calendar Events" in tables:
        logger.info("Fixing Calendar Events...")
        table_id = tables["Calendar Events"]

        # Add Day link field
        add_field(base_url, headers, table_id, {
            "name": "Day",
            "type": "multipleRecordLinks",
            "options": {
                "linkedTableId": day_table_id
            }
        })

        # Add checkboxes
        add_field(base_url, headers, table_id, {
            "name": "All Day",
            "type": "checkbox",
            "options": {}
        })

        add_field(base_url, headers, table_id, {
            "name": "Recurring",
            "type": "checkbox",
            "options": {}
        })
        print()

    # Fix Health Metrics
    if "Health Metrics" in tables:
        logger.info("Fixing Health Metrics...")
        table_id = tables["Health Metrics"]

        add_field(base_url, headers, table_id, {
            "name": "Day",
            "type": "multipleRecordLinks",
            "options": {
                "linkedTableId": day_table_id
            }
        })
        print()

    # Fix Body Metrics
    if "Body Metrics" in tables:
        logger.info("Fixing Body Metrics...")
        table_id = tables["Body Metrics"]

        add_field(base_url, headers, table_id, {
            "name": "Day",
            "type": "multipleRecordLinks",
            "options": {
                "linkedTableId": day_table_id
            }
        })
        print()

    # Fix Training Plans
    if "Training Plans" in tables:
        logger.info("Fixing Training Plans...")
        table_id = tables["Training Plans"]

        add_field(base_url, headers, table_id, {
            "name": "Start Week",
            "type": "multipleRecordLinks",
            "options": {
                "linkedTableId": week_table_id
            }
        })

        add_field(base_url, headers, table_id, {
            "name": "End Week",
            "type": "multipleRecordLinks",
            "options": {
                "linkedTableId": week_table_id
            }
        })
        print()

    # Add Training Sessions if missing
    if "Training Sessions" not in tables:
        logger.warning("Training Sessions table not found!")
        logger.warning("Please create an empty table called 'Training Sessions' in Airtable")
        logger.warning("Then run add_table_fields.py again to add its fields")
    else:
        logger.info("Fixing Training Sessions...")
        table_id = tables["Training Sessions"]

        add_field(base_url, headers, table_id, {
            "name": "Day",
            "type": "multipleRecordLinks",
            "options": {
                "linkedTableId": day_table_id
            }
        })

        add_field(base_url, headers, table_id, {
            "name": "Week",
            "type": "multipleRecordLinks",
            "options": {
                "linkedTableId": week_table_id
            }
        })
        print()

    print("=" * 60)
    print("COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
