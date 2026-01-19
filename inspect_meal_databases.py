#!/usr/bin/env python3
"""
Inspect discovered meal databases to understand their structure.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from notion_client import Client as NotionClient
from core.config import Config
from core.utils import setup_logging

logger = setup_logging("inspect_meal_databases")

# Discovered IDs
RECIPES_DB_ID = "fcb34d45-4529-4347-b983-0330858d9999"
MEALS_DB_ID = "5bb1831d-713e-4caf-af3e-0519c06576f8"
BY_WEEK_DB_ID = "f3046d76-a7ab-4363-8285-de98de26aaf4"


def inspect_database(notion, db_id, db_name):
    """Inspect a database schema."""
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Inspecting: {db_name}")
    logger.info(f"ID: {db_id}")
    logger.info("=" * 60)

    try:
        # Get database schema
        response = notion.request(
            path=f"data_sources/{db_id}",
            method="GET"
        )

        # Get properties
        properties = response.get("properties", {})
        logger.info(f"\nProperties ({len(properties)}):")
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get("type", "unknown")
            logger.info(f"  - {prop_name}: {prop_type}")

        # Get a sample record
        logger.info("\nFetching sample records...")
        query_response = notion.request(
            path=f"data_sources/{db_id}/query",
            method="POST",
            body={"page_size": 3}
        )

        records = query_response.get("results", [])
        logger.info(f"Sample records: {len(records)}")

        if records:
            logger.info("\nFirst record properties:")
            first_record = records[0]
            props = first_record.get("properties", {})
            for prop_name, prop_data in props.items():
                prop_type = prop_data.get("type", "unknown")

                # Extract a sample value
                value = None
                if prop_type == "title":
                    title_list = prop_data.get("title", [])
                    value = "".join([t.get("plain_text", "") for t in title_list])
                elif prop_type == "rich_text":
                    text_list = prop_data.get("rich_text", [])
                    value = "".join([t.get("plain_text", "") for t in text_list])
                elif prop_type == "number":
                    value = prop_data.get("number")
                elif prop_type == "select":
                    select_obj = prop_data.get("select")
                    value = select_obj.get("name") if select_obj else None
                elif prop_type == "date":
                    date_obj = prop_data.get("date")
                    value = date_obj.get("start") if date_obj else None

                if value:
                    logger.info(f"  - {prop_name} ({prop_type}): {value}")

        return True

    except Exception as e:
        logger.error(f"Error inspecting {db_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def search_for_grocery():
    """Search for grocery-related databases or pages."""
    logger.info("\n" + "=" * 60)
    logger.info("Searching for Grocery-related items")
    logger.info("=" * 60)

    try:
        notion = NotionClient(auth=Config.NOTION_TOKEN)

        # Search for "grocery"
        response = notion.search(query="grocery")
        results = response.get("results", [])

        logger.info(f"\nFound {len(results)} results for 'grocery':")
        for result in results:
            obj_type = result.get("object", "unknown")
            result_id = result.get("id", "N/A")

            if obj_type == "data_source":
                title_list = result.get("title", [])
                title = "".join([t.get("plain_text", "") for t in title_list])
                logger.info(f"  Database: {title} (ID: {result_id})")
            elif obj_type == "page":
                props = result.get("properties", {})
                title_prop = props.get("title", {})
                title_list = title_prop.get("title", [])
                title = "".join([t.get("plain_text", "") for t in title_list])
                logger.info(f"  Page: {title} (ID: {result_id})")

    except Exception as e:
        logger.error(f"Error searching: {e}")


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("Meal Database Inspection")
    logger.info("=" * 60)

    notion = NotionClient(auth=Config.NOTION_TOKEN)

    # Inspect Recipes
    inspect_database(notion, RECIPES_DB_ID, "Recipes")

    # Inspect Meals
    inspect_database(notion, MEALS_DB_ID, "Meals")

    # Inspect By Week (might be related)
    inspect_database(notion, BY_WEEK_DB_ID, "By Week")

    # Search for grocery
    search_for_grocery()

    logger.info("\n" + "=" * 60)
    logger.info("Inspection Complete!")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
