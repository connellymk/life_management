#!/usr/bin/env python3
"""
Migrate meal plans from Notion "By Week" database to Airtable.

This script:
1. Fetches all meal plans from Notion By Week database
2. Transforms the data to match Airtable Meal Plans schema
3. Links to Week table
4. Imports to Airtable
5. Creates a backup JSON file
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from pyairtable import Api
from notion_client import Client as NotionClient
from core.config import Config
from core.utils import setup_logging

logger = setup_logging("migrate_meal_plans")

# Database/Table IDs
NOTION_BY_WEEK_DB_ID = "f3046d76-a7ab-4363-8285-de98de26aaf4"
MEAL_PLANS_TABLE_ID = "tblXeRfKofAHtbt6e"
WEEK_TABLE_ID = "tbl2B7ecl7heYiKha"


def get_week_table_mapping():
    """Get Week table records and create week number mapping."""
    logger.info("=" * 60)
    logger.info("Fetching Week Table Records")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        table = api.table(Config.AIRTABLE_BASE_ID, WEEK_TABLE_ID)

        records = table.all()
        logger.info(f"Found {len(records)} Week records")

        # Create mapping from week number to record ID
        week_to_id = {}
        for record in records:
            fields = record.get("fields", {})
            week_number = fields.get("Week Number")
            if week_number:
                week_to_id[int(week_number)] = record["id"]

        logger.info(f"Created mapping for {len(week_to_id)} week numbers")
        return week_to_id

    except Exception as e:
        logger.error(f"Error fetching Week table: {e}")
        import traceback
        traceback.print_exc()
        return {}


def fetch_notion_meal_plans():
    """Fetch all meal plans from Notion."""
    logger.info("\n" + "=" * 60)
    logger.info("Fetching Meal Plans from Notion")
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

            response = notion.request(
                path=f"data_sources/{NOTION_BY_WEEK_DB_ID}/query",
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

        elif prop_type == "checkbox":
            return prop.get("checkbox", False)

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

            # Extract fields
            fields = {
                "Name": extract_notion_property(properties, "Week Name", "title"),
                "Start Date": extract_notion_property(properties, "Week Starting", "date"),
                "Notes": extract_notion_property(properties, "Notes", "rich_text"),
            }

            # Get week number for linking
            week_number = extract_notion_property(properties, "Week Number", "number")

            # Map shopping completed to grocery list generated
            shopping_completed = extract_notion_property(properties, "Shopping Completed", "checkbox")
            if shopping_completed is not None:
                fields["Grocery List Generated"] = shopping_completed

            # Map prep completed status
            prep_completed = extract_notion_property(properties, "Prep Completed", "checkbox")
            if prep_completed:
                fields["Status"] = "Completed"
            elif shopping_completed:
                fields["Status"] = "Active"
            else:
                fields["Status"] = "Planning"

            # Add meal prep notes to Notes
            meal_prep_notes = extract_notion_property(properties, "Meal Prep Notes", "rich_text")
            if meal_prep_notes:
                if fields.get("Notes"):
                    fields["Notes"] += f"\n\nMeal Prep Notes:\n{meal_prep_notes}"
                else:
                    fields["Notes"] = f"Meal Prep Notes:\n{meal_prep_notes}"

            # Add key training days to Notes
            key_training = extract_notion_property(properties, "Key Training Days", "rich_text")
            if key_training:
                if fields.get("Notes"):
                    fields["Notes"] += f"\n\nKey Training Days:\n{key_training}"
                else:
                    fields["Notes"] = f"Key Training Days:\n{key_training}"

            # Calculate End Date (7 days after Start Date)
            if fields.get("Start Date"):
                from datetime import datetime, timedelta
                start_date = datetime.fromisoformat(fields["Start Date"])
                end_date = start_date + timedelta(days=6)
                fields["End Date"] = end_date.strftime("%Y-%m-%d")

            # Store week number for linking
            if week_number is not None:
                fields["_week_number"] = int(week_number)

            # Remove None values
            fields = {k: v for k, v in fields.items() if v is not None}

            if fields.get("Name"):  # Only add if we have a name
                airtable_records.append(fields)

        except Exception as e:
            logger.error(f"Error transforming record: {e}")
            continue

    logger.info(f"Transformed {len(airtable_records)} records")
    return airtable_records


def import_to_airtable(airtable_records, week_mapping):
    """Import records to Airtable Meal Plans table."""
    logger.info("\n" + "=" * 60)
    logger.info("Importing to Airtable")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        table = api.table(Config.AIRTABLE_BASE_ID, MEAL_PLANS_TABLE_ID)

        # Prepare records for batch creation
        records_to_create = []
        for record in airtable_records:
            # Extract week number for linking
            week_number = record.pop("_week_number", None)

            # Add Week table link if week number exists in mapping
            if week_number and week_number in week_mapping:
                record["Week"] = [week_mapping[week_number]]

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
                logger.error(f"  Failed batch {i+1}-{min(i+batch_size, len(records_to_create))}: {e}")
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

        backup_file = Path("data") / f"meal_plans_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
    logger.info("Meal Plans Migration: Notion -> Airtable")
    logger.info("=" * 60)

    # Step 1: Get Week table mapping
    week_mapping = get_week_table_mapping()

    # Step 2: Fetch from Notion
    notion_records = fetch_notion_meal_plans()
    if not notion_records:
        logger.error("Failed to fetch records from Notion")
        return 1

    # Step 3: Transform data
    airtable_records = transform_notion_to_airtable(notion_records)
    if not airtable_records:
        logger.error("Failed to transform records")
        return 1

    # Step 4: Save backup
    if not save_backup(notion_records, airtable_records):
        logger.warning("Failed to create backup (continuing anyway)")

    # Step 5: Import to Airtable
    if not import_to_airtable(airtable_records, week_mapping):
        logger.error("Failed to import records to Airtable")
        return 1

    logger.info("\n" + "=" * 60)
    logger.info("Migration Complete!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("1. Verify meal plans in Airtable Meal Plans table")
    logger.info("2. Check that Week links are correct")
    logger.info("3. Run migrate_planned_meals.py to migrate planned meals")

    return 0


if __name__ == "__main__":
    sys.exit(main())
