#!/usr/bin/env python3
"""
Discover Notion meal-related databases by searching for them.

This script:
1. Searches Notion for meal-related data sources
2. Displays their IDs, names, and URLs
3. Helps identify the correct database IDs for migration
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from notion_client import Client as NotionClient
from core.config import Config
from core.utils import setup_logging

logger = setup_logging("discover_meal_databases")


def discover_meal_databases():
    """Search for meal-related databases in Notion."""
    logger.info("=" * 60)
    logger.info("Discovering Meal Databases in Notion")
    logger.info("=" * 60)

    try:
        notion = NotionClient(auth=Config.NOTION_TOKEN)

        # Search for all data sources (databases)
        logger.info("\nSearching for all data sources...")
        response = notion.search(
            filter={"property": "object", "value": "data_source"}
        )

        databases = response.get("results", [])
        logger.info(f"Found {len(databases)} total databases\n")

        # First, show all databases
        logger.info("All available databases:")
        logger.info("-" * 60)
        for db in databases:
            db_id = db.get("id", "N/A")
            title_list = db.get("title", [])
            title = "".join([t.get("plain_text", "") for t in title_list]) if title_list else "Untitled"
            logger.info(f"  - {title} (ID: {db_id})")

        # Look for meal-related databases
        meal_keywords = ["recipe", "meal", "grocery", "food", "cooking"]
        meal_databases = []

        logger.info("\nSearching for meal-related databases...")
        logger.info("-" * 60)

        for db in databases:
            db_id = db.get("id", "N/A")
            title_list = db.get("title", [])
            title = "".join([t.get("plain_text", "") for t in title_list]) if title_list else "Untitled"
            url = db.get("url", "N/A")

            # Check if title contains any meal-related keywords
            title_lower = title.lower()
            is_meal_related = any(keyword in title_lower for keyword in meal_keywords)

            if is_meal_related:
                meal_databases.append({
                    "id": db_id,
                    "title": title,
                    "url": url
                })

                logger.info(f"\nFound: {title}")
                logger.info(f"  ID: {db_id}")
                logger.info(f"  URL: {url}")

        logger.info("\n" + "=" * 60)
        logger.info(f"Summary: Found {len(meal_databases)} meal-related databases")
        logger.info("=" * 60)

        if meal_databases:
            logger.info("\nMeal Databases:")
            for i, db in enumerate(meal_databases, 1):
                logger.info(f"\n{i}. {db['title']}")
                logger.info(f"   ID: {db['id']}")
                logger.info(f"   URL: {db['url']}")

            # Save to file for reference
            output_file = Path("data") / "meal_database_ids.txt"
            output_file.parent.mkdir(exist_ok=True)

            with open(output_file, "w", encoding="utf-8") as f:
                f.write("Meal Database IDs\n")
                f.write("=" * 60 + "\n\n")
                for db in meal_databases:
                    f.write(f"Title: {db['title']}\n")
                    f.write(f"ID: {db['id']}\n")
                    f.write(f"URL: {db['url']}\n")
                    f.write("-" * 60 + "\n")

            logger.info(f"\nDatabase IDs saved to: {output_file}")

            # Display expected databases
            logger.info("\n" + "=" * 60)
            logger.info("Expected Databases")
            logger.info("=" * 60)
            logger.info("\nBased on the provided URLs, we're looking for:")
            logger.info("1. Recipes (https://www.notion.so/556a9ac89c5e4113a4245936d319e522)")
            logger.info("2. Meal Planning (https://www.notion.so/332af6a461e44cf598311cc6546bacaa)")
            logger.info("3. Grocery List (https://www.notion.so/e0b69d97cfe34bf88ce0b7007bc5f406)")

            logger.info("\nPlease verify the discovered IDs match these databases.")
        else:
            logger.warning("\nNo meal-related databases found!")
            logger.info("\nTrying to fetch specific databases by URL IDs...")

            # Try the known URL IDs
            url_ids = [
                ("Recipes", "556a9ac89c5e4113a4245936d319e522"),
                ("Meal Planning", "332af6a461e44cf598311cc6546bacaa"),
                ("Grocery List", "e0b69d97cfe34bf88ce0b7007bc5f406")
            ]

            for name, url_id in url_ids:
                logger.info(f"\nTrying to fetch {name} (URL ID: {url_id})...")
                try:
                    # Try to get the database/page
                    db = notion.databases.retrieve(database_id=url_id)
                    logger.info(f"  Success! Found as database")
                    logger.info(f"  Actual ID: {db.get('id', 'N/A')}")
                except Exception as e:
                    logger.warning(f"  Not a database: {e}")
                    # Try as a page
                    try:
                        page = notion.pages.retrieve(page_id=url_id)
                        logger.info(f"  Found as page")
                        logger.info(f"  ID: {page.get('id', 'N/A')}")
                    except Exception as e2:
                        logger.error(f"  Not accessible: {e2}")

        return True

    except Exception as e:
        logger.error(f"Error discovering databases: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("Meal Database Discovery")
    logger.info("=" * 60)

    if not discover_meal_databases():
        logger.error("\nDiscovery failed")
        return 1

    logger.info("\n" + "=" * 60)
    logger.info("Discovery Complete!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("1. Verify the discovered database IDs")
    logger.info("2. Update MEAL_MIGRATION_PLAN.md with actual IDs if needed")
    logger.info("3. Run setup_meal_schemas.py to create Airtable table schemas")

    return 0


if __name__ == "__main__":
    sys.exit(main())
