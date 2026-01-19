#!/usr/bin/env python3
"""
Migrate recipes from Notion to Airtable.

This script:
1. Fetches all recipes from Notion Recipes database
2. Transforms the data to match Airtable schema
3. Imports to Airtable Recipes table
4. Creates a backup JSON file
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

logger = setup_logging("migrate_recipes")

# Database/Table IDs
NOTION_RECIPES_DB_ID = "fcb34d45-4529-4347-b983-0330858d9999"
RECIPES_TABLE_ID = "tbl0R6ndVQvvLzEoN"


def fetch_notion_recipes():
    """Fetch all recipes from Notion."""
    logger.info("=" * 60)
    logger.info("Fetching Recipes from Notion")
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
                path=f"data_sources/{NOTION_RECIPES_DB_ID}/query",
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


def fetch_page_content(notion, page_id):
    """Fetch page content (blocks) from Notion for ingredients and instructions."""
    try:
        response = notion.request(
            path=f"blocks/{page_id}/children",
            method="GET"
        )

        blocks = response.get("results", [])

        # Extract text from blocks
        content_parts = []
        for block in blocks:
            block_type = block.get("type")
            if block_type and block_type in block:
                block_content = block[block_type]

                if block_type in ["paragraph", "heading_1", "heading_2", "heading_3"]:
                    rich_text = block_content.get("rich_text", [])
                    text = "".join([t.get("plain_text", "") for t in rich_text])
                    if text.strip():
                        if block_type == "heading_1":
                            content_parts.append(f"# {text}")
                        elif block_type == "heading_2":
                            content_parts.append(f"## {text}")
                        elif block_type == "heading_3":
                            content_parts.append(f"### {text}")
                        else:
                            content_parts.append(text)

                elif block_type == "bulleted_list_item":
                    rich_text = block_content.get("rich_text", [])
                    text = "".join([t.get("plain_text", "") for t in rich_text])
                    if text.strip():
                        content_parts.append(f"• {text}")

                elif block_type == "numbered_list_item":
                    rich_text = block_content.get("rich_text", [])
                    text = "".join([t.get("plain_text", "") for t in rich_text])
                    if text.strip():
                        content_parts.append(f"{text}")

        return "\n".join(content_parts) if content_parts else None

    except Exception as e:
        logger.warning(f"Error fetching page content for {page_id}: {e}")
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

        elif prop_type == "select":
            select_obj = prop.get("select")
            if select_obj:
                return select_obj.get("name")
            return None

        elif prop_type == "multi_select":
            multi_select_list = prop.get("multi_select", [])
            return [item.get("name") for item in multi_select_list]

        elif prop_type == "checkbox":
            return prop.get("checkbox", False)

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
    fetch_count = 0

    for i, record in enumerate(notion_records):
        try:
            page_id = record.get("id")
            properties = record.get("properties", {})

            # Extract basic fields
            fields = {
                "Name": extract_notion_property(properties, "Recipe Name", "title"),
                "Prep Time": extract_notion_property(properties, "Prep Time (min)", "number"),
                "Cook Time": extract_notion_property(properties, "Cook Time (min)", "number"),
                "Servings": extract_notion_property(properties, "Servings", "number"),
                "Calories": extract_notion_property(properties, "Calories per Serving", "number"),
                "Protein": extract_notion_property(properties, "Protein (g)", "number"),
                "Carbs": extract_notion_property(properties, "Carbs (g)", "number"),
                "Fat": extract_notion_property(properties, "Fat (g)", "number"),
            }

            # Map Meal Type (multi_select in Notion -> Category singleSelect in Airtable)
            meal_types = extract_notion_property(properties, "Meal Type", "multi_select")
            if meal_types and len(meal_types) > 0:
                # Take the first meal type as the category
                meal_type = meal_types[0]
                # Map to valid Airtable categories
                category_map = {
                    "Breakfast": "Breakfast",
                    "Lunch": "Lunch",
                    "Dinner": "Dinner",
                    "Snack": "Snack",
                    "Dessert": "Dessert"
                }
                fields["Category"] = category_map.get(meal_type, "Snack")

            # Map Dietary Tags to Tags
            dietary_tags = extract_notion_property(properties, "Dietary Tags", "multi_select")
            if dietary_tags:
                # Map Notion tags to Airtable tags
                tag_map = {
                    "High Protein": "High-Protein",
                    "Low Carb": "Low-Carb",
                    "Vegetarian": "Vegetarian",
                    "Gluten Free": "Gluten-Free",
                    "Dairy Free": "Dairy-Free"
                }
                mapped_tags = []
                for tag in dietary_tags:
                    mapped_tag = tag_map.get(tag, tag)
                    # Only include tags that exist in Airtable schema
                    if mapped_tag in ["Healthy", "Quick", "Budget-Friendly", "Meal Prep",
                                     "Freezer-Friendly", "One-Pot", "Slow Cooker", "Instant Pot",
                                     "Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free",
                                     "Low-Carb", "High-Protein"]:
                        mapped_tags.append(mapped_tag)
                if mapped_tags:
                    fields["Tags"] = mapped_tags

            # Check if meal prep friendly
            meal_prep = extract_notion_property(properties, "Meal Prep Friendly", "checkbox")
            if meal_prep and "Tags" in fields:
                if "Meal Prep" not in fields["Tags"]:
                    fields["Tags"].append("Meal Prep")
            elif meal_prep:
                fields["Tags"] = ["Meal Prep"]

            # Calculate Total Time
            if fields.get("Prep Time") is not None and fields.get("Cook Time") is not None:
                fields["Total Time"] = fields["Prep Time"] + fields["Cook Time"]

            # Fetch page content for ingredients and instructions
            if page_id and (i % 10 == 0):
                logger.info(f"  Processing record {i+1}/{len(notion_records)}...")

            page_content = fetch_page_content(notion, page_id)
            if page_content:
                # Try to split into ingredients and instructions
                # Assuming ingredients come first, then instructions
                content_lower = page_content.lower()
                if "ingredients" in content_lower and "instructions" in content_lower:
                    ing_idx = content_lower.find("ingredients")
                    inst_idx = content_lower.find("instructions")
                    if ing_idx < inst_idx:
                        ingredients_section = page_content[ing_idx:inst_idx].strip()
                        instructions_section = page_content[inst_idx:].strip()
                        fields["Ingredients"] = ingredients_section
                        fields["Instructions"] = instructions_section
                    else:
                        fields["Instructions"] = page_content
                else:
                    # Just store everything in instructions
                    fields["Instructions"] = page_content
                fetch_count += 1

            # Remove None values
            fields = {k: v for k, v in fields.items() if v is not None}

            if fields.get("Name"):  # Only add if we have a name
                airtable_records.append(fields)

        except Exception as e:
            logger.error(f"Error transforming record: {e}")
            continue

    logger.info(f"\nTransformed {len(airtable_records)} records")
    logger.info(f"Fetched page content for {fetch_count} records")
    return airtable_records


def import_to_airtable(airtable_records):
    """Import records to Airtable Recipes table."""
    logger.info("\n" + "=" * 60)
    logger.info("Importing to Airtable")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        table = api.table(Config.AIRTABLE_BASE_ID, RECIPES_TABLE_ID)

        # Batch create (max 10 records at a time)
        batch_size = 10
        created_count = 0
        failed_count = 0

        logger.info(f"\nImporting {len(airtable_records)} records...")

        for i in range(0, len(airtable_records), batch_size):
            batch = airtable_records[i:i + batch_size]
            try:
                table.batch_create(batch)
                created_count += len(batch)
                logger.info(f"  Imported records {i+1}-{min(i+batch_size, len(airtable_records))}")
            except Exception as e:
                logger.error(f"  Failed batch {i+1}-{min(i+batch_size, len(airtable_records))}: {e}")
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

        backup_file = Path("data") / f"recipes_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
    logger.info("Recipe Migration: Notion -> Airtable")
    logger.info("=" * 60)

    # Step 1: Fetch from Notion
    notion_records = fetch_notion_recipes()
    if not notion_records:
        logger.error("Failed to fetch records from Notion")
        return 1

    # Initialize Notion client for page content fetching
    notion = NotionClient(auth=Config.NOTION_TOKEN)

    # Step 2: Transform data
    airtable_records = transform_notion_to_airtable(notion_records, notion)
    if not airtable_records:
        logger.error("Failed to transform records")
        return 1

    # Step 3: Save backup
    if not save_backup(notion_records, airtable_records):
        logger.warning("Failed to create backup (continuing anyway)")

    # Step 4: Import to Airtable
    if not import_to_airtable(airtable_records):
        logger.error("Failed to import records to Airtable")
        return 1

    logger.info("\n" + "=" * 60)
    logger.info("Migration Complete!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("1. Verify recipes in Airtable Recipes table")
    logger.info("2. Review backup file for any data loss")
    logger.info("3. Run migrate_meal_plans.py to migrate meal plans")

    return 0


if __name__ == "__main__":
    sys.exit(main())
