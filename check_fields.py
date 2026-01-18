#!/usr/bin/env python3
"""
Check current fields in Planned Training Activities table.
"""

import sys
from pathlib import Path
import requests

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config
from core.utils import setup_logging

logger = setup_logging("check_fields")

PLANNED_TRAINING_ACTIVITIES_TABLE_ID = "tblxSnGD6CS9ea0cM"


def main():
    """Main function."""
    try:
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
            return 1

        tables = response.json().get("tables", [])
        table = None
        for t in tables:
            if t["id"] == table_id:
                table = t
                break

        if not table:
            logger.error(f"Table {table_id} not found")
            return 1

        logger.info(f"Table: {table['name']}")
        logger.info(f"Total fields: {len(table['fields'])}\n")

        for field in table["fields"]:
            logger.info(f"  {field['name']} ({field['type']}) - ID: {field['id']}")

        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
