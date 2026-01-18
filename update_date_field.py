#!/usr/bin/env python3
"""
Update Planned Training Activities table to replace Date field with link to Day table.
"""

import sys
from pathlib import Path
import requests

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pyairtable import Api
from core.config import Config
from core.utils import setup_logging

logger = setup_logging("update_date_field")

PLANNED_TRAINING_ACTIVITIES_TABLE_ID = "tblxSnGD6CS9ea0cM"
DAY_TABLE_NAME = "Day"


def get_day_table_id():
    """Get the Day table ID."""
    try:
        token = Config.AIRTABLE_ACCESS_TOKEN
        base_id = Config.AIRTABLE_BASE_ID

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Get table schema
        schema_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
        response = requests.get(schema_url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to get schema: {response.status_code} - {response.text}")
            return None

        tables = response.json().get("tables", [])
        for table in tables:
            if table["name"] == DAY_TABLE_NAME:
                logger.info(f"Found Day table: {table['id']}")
                return table["id"]

        logger.error(f"Day table '{DAY_TABLE_NAME}' not found")
        return None

    except Exception as e:
        logger.error(f"Error getting Day table ID: {e}")
        return None


def update_date_field_to_link():
    """Update the Date field to be a link to Day table."""
    logger.info("=" * 60)
    logger.info("Converting Date field to Day link")
    logger.info("=" * 60)

    try:
        # Get Day table ID
        day_table_id = get_day_table_id()
        if not day_table_id:
            return False

        token = Config.AIRTABLE_ACCESS_TOKEN
        base_id = Config.AIRTABLE_BASE_ID
        table_id = PLANNED_TRAINING_ACTIVITIES_TABLE_ID

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Get table schema
        schema_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
        response = requests.get(schema_url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to get schema: {response.status_code} - {response.text}")
            return False

        tables = response.json().get("tables", [])
        table = None
        for t in tables:
            if t["id"] == table_id:
                table = t
                break

        if not table:
            logger.error(f"Table {table_id} not found")
            return False

        # Find the Date field
        date_field_id = None
        for field in table["fields"]:
            if field["name"] == "Date":
                date_field_id = field["id"]
                break

        if not date_field_id:
            logger.error("Date field not found")
            return False

        logger.info(f"Found Date field: {date_field_id}")

        # Try to update the field type
        # Note: Airtable API doesn't support converting date to link directly
        # We need to create a new field with a different name
        logger.warning("Cannot convert Date field type directly via API")
        logger.warning("Will create a new 'Day' field instead")

        return True

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_day_link_field():
    """Create a linked record field to the Day table."""
    logger.info("\n" + "=" * 60)
    logger.info("Creating Day link field")
    logger.info("=" * 60)

    try:
        # Get Day table ID
        day_table_id = get_day_table_id()
        if not day_table_id:
            return False

        token = Config.AIRTABLE_ACCESS_TOKEN
        base_id = Config.AIRTABLE_BASE_ID
        table_id = PLANNED_TRAINING_ACTIVITIES_TABLE_ID

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Create the linked record field
        create_field_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables/{table_id}/fields"

        field_spec = {
            "name": "Day",
            "type": "multipleRecordLinks",
            "options": {
                "linkedTableId": day_table_id
            }
        }

        response = requests.post(create_field_url, headers=headers, json=field_spec)

        if response.status_code == 200:
            logger.info("Successfully created Day link field")
            return True
        else:
            logger.error(f"Failed to create Day link field: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error creating Day link field: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("Create Day Link Field")
    logger.info("=" * 60)
    logger.info("\nNote: The 'Date' field cannot be automatically deleted via API.")
    logger.info("You will need to manually delete it in the Airtable UI after verifying")
    logger.info("the new 'Day' field is working correctly.\n")

    success = True

    # Step 1: Check Date field exists
    if not update_date_field_to_link():
        logger.error("Failed to check Date field")
        success = False

    # Step 2: Create Day link field
    if not create_day_link_field():
        logger.error("Failed to create Day link field")
        success = False

    logger.info("\n" + "=" * 60)
    if success:
        logger.info("Successfully created Day link field!")
        logger.info("\nNext steps:")
        logger.info("1. Verify the 'Day' link field works correctly in Airtable")
        logger.info("2. Manually delete the 'Date' field in Airtable UI")
        logger.info("   (Table settings → Fields → Date → Delete)")
    else:
        logger.info("Some steps failed")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
