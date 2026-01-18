#!/usr/bin/env python3
"""
Migrate training plan records from Notion to Airtable.

This script:
1. Fetches all training activities from the Notion training plan database
2. Transforms the data to match Airtable schema
3. Imports records to Airtable Training Plans table
4. Links records to the Day table
5. Creates a backup JSON file
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pyairtable import Api
from notion_client import Client as NotionClient
from core.config import Config
from core.utils import setup_logging

logger = setup_logging("migrate_notion_training_plans")

# Table IDs
PLANNED_TRAINING_ACTIVITIES_TABLE_ID = "tblxSnGD6CS9ea0cM"
DAY_TABLE_ID = "tblHMwUnVg8bA1xoP"

# Notion Database ID (discovered via search - actual data source ID)
# The URL contains: 9a3c2dd1b2354f2a8e8f330d7fda16c3 (page/database view ID)
# But the actual data source ID is: 24620dff-0071-4fee-a445-03a56ed60843
NOTION_TRAINING_PLAN_DB_ID = "24620dff-0071-4fee-a445-03a56ed60843"


def fetch_notion_training_plans():
    """Fetch all training plan records from Notion."""
    logger.info("=" * 60)
    logger.info("Fetching Training Plans from Notion")
    logger.info("=" * 60)

    try:
        notion = NotionClient(auth=Config.NOTION_TOKEN)

        all_records = []
        has_more = True
        start_cursor = None

        while has_more:
            body = {"page_size": 100}
            if start_cursor:
                body["start_cursor"] = start_cursor

            # Use the request method to query the data source
            response = notion.request(
                path=f"data_sources/{NOTION_TRAINING_PLAN_DB_ID}/query",
                method="POST",
                body=body
            )

            all_records.extend(response.get("results", []))

            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")

            logger.info(f"Fetched {len(all_records)} records so far...")

        logger.info(f"\nTotal records fetched: {len(all_records)}")
        return all_records

    except Exception as e:
        logger.error(f"Error fetching from Notion: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_notion_property(properties, prop_name, prop_type):
    """Extract value from Notion property based on type."""
    try:
        prop = properties.get(prop_name)
        if not prop:
            return None

        if prop_type == "title":
            title_list = prop.get("title", [])
            if title_list:
                return "".join([t.get("plain_text", "") for t in title_list])
            return None

        elif prop_type == "rich_text":
            text_list = prop.get("rich_text", [])
            if text_list:
                return "".join([t.get("plain_text", "") for t in text_list])
            return None

        elif prop_type == "number":
            return prop.get("number")

        elif prop_type == "date":
            date_obj = prop.get("date")
            if date_obj:
                return date_obj.get("start")
            return None

        elif prop_type == "select":
            select_obj = prop.get("select")
            if select_obj:
                return select_obj.get("name")
            return None

        elif prop_type == "multi_select":
            multi_select_list = prop.get("multi_select", [])
            return [item.get("name") for item in multi_select_list]

        else:
            return None

    except Exception as e:
        logger.warning(f"Error extracting property {prop_name}: {e}")
        return None


def transform_notion_to_airtable(notion_records):
    """Transform Notion records to Airtable format."""
    logger.info("\n" + "=" * 60)
    logger.info("Transforming Data")
    logger.info("=" * 60)

    airtable_records = []

    for record in notion_records:
        try:
            properties = record.get("properties", {})

            # Extract all fields according to field mapping
            fields = {
                "Name": extract_notion_property(properties, "Name", "title"),
                "Week Number": extract_notion_property(properties, "Week Number", "number"),
                "Day of Week": extract_notion_property(properties, "Day of Week", "select"),
                "Status": extract_notion_property(properties, "Status", "select") or "Planned",
                "Workout Type": extract_notion_property(properties, "Workout Type", "select"),
                "Training Phase": extract_notion_property(properties, "Training Phase", "select"),
                "Priority": extract_notion_property(properties, "Priority", "select"),
                "Focus Areas": extract_notion_property(properties, "Focus Areas", "multi_select"),
                "Workout Description": extract_notion_property(properties, "Workout Description", "rich_text"),
                "Planned Distance": extract_notion_property(properties, "Planned Distance", "number"),
                "Planned Duration": extract_notion_property(properties, "Planned Duration", "number"),
                "Planned Elevation Gain": extract_notion_property(properties, "Planned Elevation Gain", "number"),
                "Target Pace Effort": extract_notion_property(properties, "Target Pace Effort", "rich_text"),
                "Workout Notes": extract_notion_property(properties, "Workout Notes", "rich_text"),
                "Weekly Mileage Target": extract_notion_property(properties, "Weekly Mileage Target", "number"),
                "Weekly Elevation Target": extract_notion_property(properties, "Weekly Elevation Target", "number"),
            }

            # Extract date (for backup and linking purposes)
            date_str = extract_notion_property(properties, "Date", "date")

            # Remove None values
            fields = {k: v for k, v in fields.items() if v is not None}

            # Store date separately for Day table linking
            if date_str:
                fields["_date"] = date_str

            airtable_records.append(fields)

        except Exception as e:
            logger.error(f"Error transforming record: {e}")
            continue

    logger.info(f"Transformed {len(airtable_records)} records")
    return airtable_records


def get_day_table_records():
    """Fetch all Day table records to create a date-to-record-id mapping."""
    logger.info("\n" + "=" * 60)
    logger.info("Fetching Day Table Records")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        table = api.table(Config.AIRTABLE_BASE_ID, DAY_TABLE_ID)

        records = table.all()
        logger.info(f"Found {len(records)} Day records")

        # Create date to record ID mapping
        # Check what the actual date field name is
        if records:
            sample_fields = list(records[0].get("fields", {}).keys())
            logger.info(f"Sample Day record fields: {sample_fields}")

        date_to_id = {}
        for record in records:
            fields = record.get("fields", {})
            # Try different possible date field names
            date_str = fields.get("Date") or fields.get("date") or fields.get("Name")
            if date_str:
                date_to_id[date_str] = record["id"]

        logger.info(f"Created mapping for {len(date_to_id)} dates")
        return date_to_id

    except Exception as e:
        logger.error(f"Error fetching Day table: {e}")
        import traceback
        traceback.print_exc()
        return {}


def import_to_airtable(airtable_records, day_table_mapping):
    """Import records to Airtable Training Plans table."""
    logger.info("\n" + "=" * 60)
    logger.info("Importing to Airtable")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        table = api.table(Config.AIRTABLE_BASE_ID, PLANNED_TRAINING_ACTIVITIES_TABLE_ID)

        # Prepare records for batch creation
        records_to_create = []
        for record in airtable_records:
            # Extract date for Day table linking
            date_str = record.pop("_date", None)

            # Add Day table link if date exists in mapping
            if date_str and date_str in day_table_mapping:
                record["Day"] = [day_table_mapping[date_str]]

            # pyairtable batch_create expects just the fields dict, not wrapped in {"fields": ...}
            records_to_create.append(record)

        # Batch create (max 10 records at a time)
        batch_size = 10
        created_count = 0
        failed_count = 0

        logger.info(f"\nImporting {len(records_to_create)} records...")

        for i in range(0, len(records_to_create), batch_size):
            batch = records_to_create[i:i + batch_size]
            try:
                table.batch_create(batch)
                created_count += len(batch)
                logger.info(f"  Imported records {i+1}-{min(i+batch_size, len(records_to_create))}")
            except Exception as e:
                logger.error(f"  Failed to import batch {i+1}-{min(i+batch_size, len(records_to_create))}: {e}")
                failed_count += len(batch)

        logger.info(f"\nResults:")
        logger.info(f"  Successfully imported: {created_count}")
        logger.info(f"  Failed: {failed_count}")

        return created_count > 0

    except Exception as e:
        logger.error(f"Error importing to Airtable: {e}")
        import traceback
        traceback.print_exc()
        return False


def save_backup(notion_records, airtable_records):
    """Save backup of exported data to JSON file."""
    logger.info("\n" + "=" * 60)
    logger.info("Creating Backup")
    logger.info("=" * 60)

    try:
        backup_data = {
            "exported_at": datetime.now().isoformat(),
            "notion_records_count": len(notion_records),
            "airtable_records_count": len(airtable_records),
            "notion_records": notion_records,
            "airtable_records": airtable_records,
        }

        backup_file = Path("data") / f"training_plan_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_file.parent.mkdir(exist_ok=True)

        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Backup saved to: {backup_file}")
        return True

    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("Training Plan Migration: Notion -> Airtable")
    logger.info("=" * 60)

    # Step 1: Fetch from Notion
    notion_records = fetch_notion_training_plans()
    if not notion_records:
        logger.error("Failed to fetch records from Notion")
        return 1

    # Step 2: Transform data
    airtable_records = transform_notion_to_airtable(notion_records)
    if not airtable_records:
        logger.error("Failed to transform records")
        return 1

    # Step 3: Save backup
    if not save_backup(notion_records, airtable_records):
        logger.warning("Failed to create backup (continuing anyway)")

    # Step 4: Get Day table mapping
    day_table_mapping = get_day_table_records()

    # Step 5: Import to Airtable
    if not import_to_airtable(airtable_records, day_table_mapping):
        logger.error("Failed to import records to Airtable")
        return 1

    logger.info("\n" + "=" * 60)
    logger.info("Migration Complete!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("1. Verify records in Airtable Training Plans table")
    logger.info("2. Check that Day links are correct")
    logger.info("3. Review backup file for any data loss")

    return 0


if __name__ == "__main__":
    sys.exit(main())
