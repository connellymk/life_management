#!/usr/bin/env python3
"""
Update Training Plans in Airtable:
1. Link to Day table records based on dates
2. Fetch and populate Workout Description from Notion page content
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

logger = setup_logging("update_training_plans")

PLANNED_TRAINING_ACTIVITIES_TABLE_ID = "tblxSnGD6CS9ea0cM"
DAY_TABLE_ID = "tblHMwUnVg8bA1xoP"


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

        # Create mapping from "Day" field value (e.g., "2026-01-20") to record ID
        date_to_id = {}
        for record in records:
            fields = record.get("fields", {})
            # The Day field contains the date string
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


def fetch_page_content(notion, page_id):
    """Fetch page content (blocks) from Notion."""
    try:
        # Get all blocks from the page
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

                # Handle different block types
                if block_type == "paragraph":
                    rich_text = block_content.get("rich_text", [])
                    text = "".join([t.get("plain_text", "") for t in rich_text])
                    if text.strip():
                        content_parts.append(text)

                elif block_type == "heading_1":
                    rich_text = block_content.get("rich_text", [])
                    text = "".join([t.get("plain_text", "") for t in rich_text])
                    if text.strip():
                        content_parts.append(f"# {text}")

                elif block_type == "heading_2":
                    rich_text = block_content.get("rich_text", [])
                    text = "".join([t.get("plain_text", "") for t in rich_text])
                    if text.strip():
                        content_parts.append(f"## {text}")

                elif block_type == "heading_3":
                    rich_text = block_content.get("rich_text", [])
                    text = "".join([t.get("plain_text", "") for t in rich_text])
                    if text.strip():
                        content_parts.append(f"### {text}")

                elif block_type == "bulleted_list_item":
                    rich_text = block_content.get("rich_text", [])
                    text = "".join([t.get("plain_text", "") for t in rich_text])
                    if text.strip():
                        content_parts.append(f"• {text}")

                elif block_type == "numbered_list_item":
                    rich_text = block_content.get("rich_text", [])
                    text = "".join([t.get("plain_text", "") for t in rich_text])
                    if text.strip():
                        content_parts.append(f"1. {text}")

        return "\n".join(content_parts) if content_parts else None

    except Exception as e:
        logger.warning(f"Error fetching page content for {page_id}: {e}")
        return None


def update_training_plans():
    """Update Training Plans with Day links and Workout Descriptions."""
    logger.info("\n" + "=" * 60)
    logger.info("Updating Training Plans")
    logger.info("=" * 60)

    try:
        # Get Day table mapping
        day_mapping = get_day_table_mapping()

        # Initialize clients
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        table = api.table(Config.AIRTABLE_BASE_ID, PLANNED_TRAINING_ACTIVITIES_TABLE_ID)
        notion = NotionClient(auth=Config.NOTION_TOKEN)

        # Load backup to get Notion page IDs
        backup_path = Path("data/training_plan_backup_20260118_082144.json")
        with open(backup_path, encoding="utf-8") as f:
            backup_data = json.load(f)

        notion_records = backup_data["notion_records"]
        logger.info(f"\nLoaded {len(notion_records)} Notion records from backup")

        # Create mapping from Name to Notion page ID
        name_to_page_id = {}
        name_to_date = {}
        for record in notion_records:
            page_id = record.get("id")
            properties = record.get("properties", {})

            # Extract name
            name_prop = properties.get("Name", {})
            name_list = name_prop.get("title", [])
            name = "".join([t.get("plain_text", "") for t in name_list]) if name_list else None

            # Extract date
            date_prop = properties.get("Date", {})
            date_obj = date_prop.get("date")
            date_str = date_obj.get("start") if date_obj else None

            if name:
                name_to_page_id[name] = page_id
                if date_str:
                    name_to_date[name] = date_str

        logger.info(f"Created mapping for {len(name_to_page_id)} page IDs")

        # Fetch all Training Plans records
        training_records = table.all()
        logger.info(f"Found {len(training_records)} Training Plans in Airtable\n")

        # Update records
        updates = []
        fetch_count = 0

        for i, record in enumerate(training_records):
            fields = record.get("fields", {})
            name = fields.get("Name")

            if not name:
                continue

            update_fields = {}

            # Add Day link if we have a date
            if name in name_to_date:
                date_str = name_to_date[name]
                if date_str in day_mapping:
                    update_fields["Day"] = [day_mapping[date_str]]

            # Fetch and add Workout Description if page ID exists
            if name in name_to_page_id:
                page_id = name_to_page_id[name]
                content = fetch_page_content(notion, page_id)

                if content:
                    update_fields["Workout Description"] = content
                    fetch_count += 1

                # Log progress every 25 records
                if (i + 1) % 25 == 0:
                    logger.info(f"  Processed {i + 1}/{len(training_records)} records...")

            if update_fields:
                updates.append({
                    "id": record["id"],
                    "fields": update_fields
                })

        logger.info(f"\nFetched content for {fetch_count} records")
        logger.info(f"Prepared {len(updates)} records for update\n")

        if updates:
            logger.info("Updating records...")

            # Batch update (max 10 at a time)
            batch_size = 10
            success_count = 0

            for i in range(0, len(updates), batch_size):
                batch = updates[i:i + batch_size]
                try:
                    table.batch_update(batch)
                    success_count += len(batch)
                    logger.info(f"  Updated records {i+1}-{min(i+batch_size, len(updates))}")
                except Exception as e:
                    logger.error(f"  Failed batch {i+1}-{min(i+batch_size, len(updates))}: {e}")

            logger.info(f"\nSuccessfully updated {success_count}/{len(updates)} records")
        else:
            logger.info("No records need updating")

        return True

    except Exception as e:
        logger.error(f"Error updating training plans: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("Update Training Plans: Day Links & Descriptions")
    logger.info("=" * 60)

    if not update_training_plans():
        logger.error("\nUpdate failed")
        return 1

    logger.info("\n" + "=" * 60)
    logger.info("Update Complete!")
    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
