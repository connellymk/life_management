"""
Script to add missing fields to the Health Metrics table using Airtable REST API.

This script uses the REST API to add fields that match what the health sync expects.
"""

import requests
from core.config import AirtableConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_fields_to_health_metrics():
    """Add missing number fields to Health Metrics table."""

    token = AirtableConfig.AIRTABLE_ACCESS_TOKEN or AirtableConfig.AIRTABLE_API_KEY
    base_id = AirtableConfig.AIRTABLE_BASE_ID

    # Get the table ID for Health Metrics
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
    health_table = None
    for table in tables:
        if table["name"] == "Health Metrics":
            health_table = table
            break

    if not health_table:
        logger.error("Health Metrics table not found")
        return False

    table_id = health_table["id"]
    existing_fields = {field["name"] for field in health_table["fields"]}

    logger.info(f"Found Health Metrics table: {table_id}")
    logger.info(f"Existing fields: {sorted(existing_fields)}")

    # Define fields to add (only the ones that don't exist)
    fields_to_add = [
        {"name": "Sleep Duration", "type": "number", "options": {"precision": 0}},
        {"name": "Deep Sleep", "type": "number", "options": {"precision": 0}},
        {"name": "REM Sleep", "type": "number", "options": {"precision": 0}},
        {"name": "Light Sleep", "type": "number", "options": {"precision": 0}},
        {"name": "Awake Time", "type": "number", "options": {"precision": 0}},
        {"name": "Intensity Minutes", "type": "number", "options": {"precision": 0}},
        {"name": "Moderate Intensity Minutes", "type": "number", "options": {"precision": 0}},
        {"name": "Vigorous Intensity Minutes", "type": "number", "options": {"precision": 0}},
        {"name": "Max Stress", "type": "number", "options": {"precision": 0}},
        {"name": "Notes", "type": "multilineText"},
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
    logger.info("Add Health Metrics Fields Script")
    logger.info("="*60)
    logger.info("\nThis script will add missing fields to the Health Metrics table.")
    logger.info("Your Airtable token must have 'schema.bases:write' permission.\n")

    try:
        success = add_fields_to_health_metrics()
        if success:
            logger.info("\n✓ All fields added successfully!")
        else:
            logger.warning("\n⚠ Some fields failed to add. Check errors above.")
    except Exception as e:
        logger.error(f"\n✗ Script failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
