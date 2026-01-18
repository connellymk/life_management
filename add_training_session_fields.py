"""
Script to add detailed metrics fields to the Training Sessions table.

This script adds fields for detailed activity metrics that are only available
when fetching individual activity details from Garmin.
"""

import requests
from core.config import AirtableConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_fields_to_training_sessions():
    """Add detailed metric fields to Training Sessions table."""

    token = AirtableConfig.AIRTABLE_ACCESS_TOKEN or AirtableConfig.AIRTABLE_API_KEY
    base_id = AirtableConfig.AIRTABLE_BASE_ID

    # Get the table ID for Training Sessions
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Get base schema to find table ID
    schema_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    response = requests.get(schema_url, headers=headers)

    if response.status_code != 200:
        logger.error(f"Failed to get schema: {response.status_code} - {response.text}")
        return False

    tables = response.json().get("tables", [])
    training_table = None
    for table in tables:
        if table["name"] == AirtableConfig.AIRTABLE_TRAINING_SESSIONS:
            training_table = table
            break

    if not training_table:
        logger.error("Training Sessions table not found")
        return False

    table_id = training_table["id"]
    existing_fields = {field["name"] for field in training_table["fields"]}

    logger.info(f"Found Training Sessions table: {table_id}")
    logger.info(f"Existing fields: {sorted(existing_fields)}")

    # Define fields to add (detailed metrics from Garmin activity summary)
    fields_to_add = [
        {
            "name": "Aerobic Training Effect",
            "type": "number",
            "options": {"precision": 1}
        },
        {
            "name": "Anaerobic Training Effect",
            "type": "number",
            "options": {"precision": 1}
        },
        {
            "name": "Activity Training Load",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Avg Grade Adjusted Speed (mph)",
            "type": "number",
            "options": {"precision": 2}
        },
        {
            "name": "Avg Moving Speed (mph)",
            "type": "number",
            "options": {"precision": 2}
        },
        {
            "name": "Avg Temperature (F)",
            "type": "number",
            "options": {"precision": 1}
        },
        {
            "name": "Body Battery Change",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Moving Duration (min)",
            "type": "number",
            "options": {"precision": 1}
        },
    ]

    # Filter out fields that already exist
    new_fields = [f for f in fields_to_add if f["name"] not in existing_fields]

    if not new_fields:
        logger.info("✓ All required fields already exist")
        return True

    logger.info(f"\nAdding {len(new_fields)} new fields:")
    for field in new_fields:
        logger.info(f"  - {field['name']} ({field['type']})")

    # Add fields one by one using POST to create new fields
    create_field_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables/{table_id}/fields"
    success_count = 0
    error_count = 0

    for field in new_fields:
        response = requests.post(create_field_url, headers=headers, json=field)

        if response.status_code == 200:
            logger.info(f"✓ Added field: {field['name']}")
            success_count += 1
        else:
            logger.error(f"✗ Failed to add field '{field['name']}': {response.status_code} - {response.text}")
            error_count += 1

    logger.info(f"\n{'='*60}")
    logger.info(f"Results: {success_count} succeeded, {error_count} failed")
    logger.info(f"{'='*60}")

    return error_count == 0


def main():
    """Main function."""
    logger.info("="*60)
    logger.info("Add Training Sessions Detailed Fields Script")
    logger.info("="*60)
    logger.info("\nThis script will add detailed metric fields to the Training Sessions table.")
    logger.info("Your Airtable token must have 'schema.bases:write' permission.\n")

    try:
        success = add_fields_to_training_sessions()
        if success:
            logger.info("\n✓ All fields added successfully!")
            logger.info("\nNext steps:")
            logger.info("1. The sync script will now fetch detailed activity data")
            logger.info("2. This includes an extra API call per activity")
            logger.info("3. Run: python orchestrators/sync_health.py --start-date 2026-01-01 --end-date 2026-01-17")
        else:
            logger.warning("\n⚠ Some fields failed to add. Check errors above.")
    except Exception as e:
        logger.error(f"\n✗ Script failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
