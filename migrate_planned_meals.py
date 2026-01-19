#!/usr/bin/env python3
"""
Migrate planned meals from Notion "Meals" database to Airtable.

This script:
1. Fetches all planned meals from Notion Meals database
2. Transforms the data to match Airtable Planned Meals schema
3. Links to Day, Meal Plans, and Recipes tables
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

logger = setup_logging("migrate_planned_meals")

# Database/Table IDs
NOTION_MEALS_DB_ID = "5bb1831d-713e-4caf-af3e-0519c06576f8"
PLANNED_MEALS_TABLE_ID = "tblTAfTWjHWwjV30Y"
DAY_TABLE_ID = "tblHMwUnVg8bA1xoP"
RECIPES_TABLE_ID = "tbl0R6ndVQvvLzEoN"
MEAL_PLANS_TABLE_ID = "tblXeRfKofAHtbt6e"


def get_day_table_mapping():
    """Get Day table records and create date mapping."""
    logger.info("=" * 60)
    logger.info("Fetching Day Table Records")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        table = api.table(Config.AIRTABLE_BASE_ID, DAY_TABLE_ID)

        records = table.all()
        logger.info(f"Found {len(records)} Day records")

        # Create mapping from "Day" field value to record ID
        date_to_id = {}
        for record in records:
            fields = record.get("fields", {})
            day_value = fields.get("Day")
            if day_value:
                date_to_id[day_value] = record["id"]

        logger.info(f"Created mapping for {len(date_to_id)} dates")
        return date_to_id

    except Exception as e:
        logger.error(f"Error fetching Day table: {e}")
        import traceback
        traceback.print_exc()
        return {}


def get_recipes_mapping():
    """Get Recipes table records and create name mapping."""
    logger.info("\n" + "=" * 60)
    logger.info("Fetching Recipes Table Records")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        table = api.table(Config.AIRTABLE_BASE_ID, RECIPES_TABLE_ID)

        records = table.all()
        logger.info(f"Found {len(records)} Recipe records")

        # Create mapping from recipe name to record ID
        name_to_id = {}
        for record in records:
            fields = record.get("fields", {})
            name = fields.get("Name")
            if name:
                name_to_id[name.lower()] = record["id"]

        logger.info(f"Created mapping for {len(name_to_id)} recipe names")
        return name_to_id

    except Exception as e:
        logger.error(f"Error fetching Recipes table: {e}")
        import traceback
        traceback.print_exc()
        return {}


def get_meal_plans_mapping():
    """Get Meal Plans table records and create name mapping."""
    logger.info("\n" + "=" * 60)
    logger.info("Fetching Meal Plans Table Records")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        table = api.table(Config.AIRTABLE_BASE_ID, MEAL_PLANS_TABLE_ID)

        records = table.all()
        logger.info(f"Found {len(records)} Meal Plan records")

        # Create mapping from meal plan name to record ID
        name_to_id = {}
        for record in records:
            fields = record.get("fields", {})
            name = fields.get("Name")
            if name:
                name_to_id[name.lower()] = record["id"]

        logger.info(f"Created mapping for {len(name_to_id)} meal plan names")
        return name_to_id

    except Exception as e:
        logger.error(f"Error fetching Meal Plans table: {e}")
        import traceback
        traceback.print_exc()
        return {}


def fetch_notion_planned_meals():
    """Fetch all planned meals from Notion."""
    logger.info("\n" + "=" * 60)
    logger.info("Fetching Planned Meals from Notion")
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
                path=f"data_sources/{NOTION_MEALS_DB_ID}/query",
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

        elif prop_type == "checkbox":
            return prop.get("checkbox", False)

        elif prop_type == "relation":
            # Return list of related IDs
            relation_list = prop.get("relation", [])
            return [item.get("id") for item in relation_list]

        else:
            return None

    except Exception as e:
        logger.warning(f"Error extracting property {prop_name}: {e}")
        return None


def transform_notion_to_airtable(notion_records, notion):
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
                "Name": extract_notion_property(properties, "Meal", "title"),
                "Date": extract_notion_property(properties, "Date", "date"),
                "Meal Type": extract_notion_property(properties, "Meal Type", "select"),
                "Servings": extract_notion_property(properties, "Servings Eaten", "number"),
                "Notes": extract_notion_property(properties, "Notes", "rich_text"),
            }

            # Map Prep Status to Status
            prep_status = extract_notion_property(properties, "Prep Status", "select")
            completed = extract_notion_property(properties, "Completed", "checkbox")

            if completed:
                fields["Status"] = "Prepared"
            elif prep_status == "Pre-prepped":
                fields["Status"] = "Prepared"
            else:
                fields["Status"] = "Planned"

            # Get Recipe relation (need to fetch the related recipe page)
            recipe_relations = extract_notion_property(properties, "Recipe", "relation")
            if recipe_relations and len(recipe_relations) > 0:
                # Get the first related recipe ID
                recipe_page_id = recipe_relations[0]
                # Fetch recipe page to get the name
                try:
                    recipe_page = notion.request(
                        path=f"pages/{recipe_page_id}",
                        method="GET"
                    )
                    recipe_props = recipe_page.get("properties", {})
                    recipe_name_prop = recipe_props.get("Recipe Name", {})
                    recipe_title_list = recipe_name_prop.get("title", [])
                    recipe_name = "".join([t.get("plain_text", "") for t in recipe_title_list])
                    if recipe_name:
                        fields["_recipe_name"] = recipe_name
                except Exception as e:
                    logger.warning(f"Could not fetch recipe name for relation: {e}")

            # Store date for Day table linking
            if fields.get("Date"):
                fields["_date"] = fields["Date"]

            # Remove None values
            fields = {k: v for k, v in fields.items() if v is not None}

            if fields.get("Name"):  # Only add if we have a name
                airtable_records.append(fields)

        except Exception as e:
            logger.error(f"Error transforming record: {e}")
            import traceback
            traceback.print_exc()
            continue

    logger.info(f"Transformed {len(airtable_records)} records")
    return airtable_records


def import_to_airtable(airtable_records, day_mapping, recipes_mapping, meal_plans_mapping):
    """Import records to Airtable Planned Meals table."""
    logger.info("\n" + "=" * 60)
    logger.info("Importing to Airtable")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        table = api.table(Config.AIRTABLE_BASE_ID, PLANNED_MEALS_TABLE_ID)

        # Prepare records for batch creation
        records_to_create = []
        for record in airtable_records:
            # Extract linking data
            date_str = record.pop("_date", None)
            recipe_name = record.pop("_recipe_name", None)

            # Add Day table link if date exists in mapping
            if date_str and date_str in day_mapping:
                record["Day"] = [day_mapping[date_str]]

            # Add Recipe link if recipe name exists in mapping
            if recipe_name:
                recipe_name_lower = recipe_name.lower()
                if recipe_name_lower in recipes_mapping:
                    record["Recipe"] = [recipes_mapping[recipe_name_lower]]
                else:
                    logger.warning(f"Recipe not found in mapping: {recipe_name}")

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

        backup_file = Path("data") / f"planned_meals_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
    logger.info("Planned Meals Migration: Notion -> Airtable")
    logger.info("=" * 60)

    # Step 1: Get mapping tables
    day_mapping = get_day_table_mapping()
    recipes_mapping = get_recipes_mapping()
    meal_plans_mapping = get_meal_plans_mapping()

    # Step 2: Fetch from Notion
    notion_records = fetch_notion_planned_meals()
    if not notion_records:
        logger.error("Failed to fetch records from Notion")
        return 1

    # Initialize Notion client for recipe fetching
    notion = NotionClient(auth=Config.NOTION_TOKEN)

    # Step 3: Transform data
    airtable_records = transform_notion_to_airtable(notion_records, notion)
    if not airtable_records:
        logger.error("Failed to transform records")
        return 1

    # Step 4: Save backup
    if not save_backup(notion_records, airtable_records):
        logger.warning("Failed to create backup (continuing anyway)")

    # Step 5: Import to Airtable
    if not import_to_airtable(airtable_records, day_mapping, recipes_mapping, meal_plans_mapping):
        logger.error("Failed to import records to Airtable")
        return 1

    logger.info("\n" + "=" * 60)
    logger.info("Migration Complete!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("1. Verify planned meals in Airtable Planned Meals table")
    logger.info("2. Check that Day, Recipe, and Meal Plan links are correct")
    logger.info("3. Review backup file for any data loss")

    return 0


if __name__ == "__main__":
    sys.exit(main())
