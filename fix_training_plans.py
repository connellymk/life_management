#!/usr/bin/env python3
"""
Fix training plans data:
1. Remove duplicate plans for the same date
2. Move rest days to Mondays
"""

import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from pyairtable import Api
from core.config import Config
from core.utils import setup_logging

logger = setup_logging("fix_training_plans")

PLANNED_TRAINING_ACTIVITIES_TABLE_ID = "tblxSnGD6CS9ea0cM"


def analyze_training_plans():
    """Analyze current training plans for issues."""
    logger.info("=" * 60)
    logger.info("Analyzing Training Plans")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        table = api.table(Config.AIRTABLE_BASE_ID, PLANNED_TRAINING_ACTIVITIES_TABLE_ID)

        records = table.all()
        logger.info(f"Total records: {len(records)}")

        # Group by date
        by_date = defaultdict(list)
        rest_days = []

        for record in records:
            fields = record.get("fields", {})
            date = fields.get("Date")
            workout_type = fields.get("Workout Type", "N/A")
            day_of_week = fields.get("Day of Week")

            if date:
                by_date[date].append({
                    "id": record["id"],
                    "name": fields.get("Name", "N/A"),
                    "type": workout_type,
                    "day": day_of_week,
                    "date": date
                })

                if workout_type == "Rest":
                    rest_days.append({
                        "id": record["id"],
                        "date": date,
                        "day": day_of_week,
                        "name": fields.get("Name", "N/A")
                    })

        # Find duplicates
        duplicates = {date: items for date, items in by_date.items() if len(items) > 1}

        logger.info(f"\nDates with duplicates: {len(duplicates)}")
        if duplicates:
            logger.info("\nDuplicate records:")
            for date, items in sorted(duplicates.items()):
                logger.info(f"\n  Date: {date}")
                for item in items:
                    logger.info(f"    - {item['name']} ({item['type']}) - Day: {item['day']}")

        # Analyze rest days
        logger.info(f"\nRest days found: {len(rest_days)}")
        non_monday_rest = [r for r in rest_days if r["day"] != "Monday"]

        if non_monday_rest:
            logger.info(f"\nRest days NOT on Monday: {len(non_monday_rest)}")
            for rest in non_monday_rest[:10]:
                logger.info(f"  - {rest['date']} ({rest['day']}): {rest['name']}")

        return {
            "all_records": records,
            "duplicates": duplicates,
            "rest_days": rest_days,
            "non_monday_rest": non_monday_rest
        }

    except Exception as e:
        logger.error(f"Error analyzing: {e}")
        import traceback
        traceback.print_exc()
        return None


def remove_duplicates(duplicates):
    """Remove duplicate records, keeping the first one for each date."""
    logger.info("\n" + "=" * 60)
    logger.info("Removing Duplicates")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        table = api.table(Config.AIRTABLE_BASE_ID, PLANNED_TRAINING_ACTIVITIES_TABLE_ID)

        records_to_delete = []

        for date, items in duplicates.items():
            # Keep the first record, delete the rest
            logger.info(f"\nDate: {date}")
            logger.info(f"  Keeping: {items[0]['name']} ({items[0]['type']})")

            for item in items[1:]:
                logger.info(f"  Deleting: {item['name']} ({item['type']}) - ID: {item['id']}")
                records_to_delete.append(item['id'])

        if records_to_delete:
            logger.info(f"\nDeleting {len(records_to_delete)} duplicate records...")

            # Delete in batches of 10
            batch_size = 10
            deleted_count = 0

            for i in range(0, len(records_to_delete), batch_size):
                batch = records_to_delete[i:i + batch_size]
                try:
                    table.batch_delete(batch)
                    deleted_count += len(batch)
                    logger.info(f"  Deleted batch {i+1}-{min(i+batch_size, len(records_to_delete))}")
                except Exception as e:
                    logger.error(f"  Failed to delete batch: {e}")

            logger.info(f"\nSuccessfully deleted {deleted_count}/{len(records_to_delete)} duplicates")
            return True
        else:
            logger.info("No duplicates to delete")
            return True

    except Exception as e:
        logger.error(f"Error removing duplicates: {e}")
        import traceback
        traceback.print_exc()
        return False


def fix_rest_day_schedule(non_monday_rest):
    """Update rest days to be on Monday instead of their current day."""
    logger.info("\n" + "=" * 60)
    logger.info("Fixing Rest Day Schedule")
    logger.info("=" * 60)
    logger.info("\nNote: This will update Day of Week field to Monday")
    logger.info("The Date field will remain the same")

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        table = api.table(Config.AIRTABLE_BASE_ID, PLANNED_TRAINING_ACTIVITIES_TABLE_ID)

        updates = []

        for rest in non_monday_rest:
            logger.info(f"\nUpdating: {rest['date']} from {rest['day']} to Monday")
            updates.append({
                "id": rest["id"],
                "fields": {
                    "Day of Week": "Monday"
                }
            })

        if updates:
            logger.info(f"\nUpdating {len(updates)} records...")

            # Update in batches of 10
            batch_size = 10
            updated_count = 0

            for i in range(0, len(updates), batch_size):
                batch = updates[i:i + batch_size]
                try:
                    table.batch_update(batch)
                    updated_count += len(batch)
                    logger.info(f"  Updated batch {i+1}-{min(i+batch_size, len(updates))}")
                except Exception as e:
                    logger.error(f"  Failed to update batch: {e}")

            logger.info(f"\nSuccessfully updated {updated_count}/{len(updates)} rest days")
            return True
        else:
            logger.info("No rest days to update")
            return True

    except Exception as e:
        logger.error(f"Error fixing rest days: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("Fix Training Plans Data")
    logger.info("=" * 60)

    # Step 1: Analyze
    analysis = analyze_training_plans()
    if not analysis:
        logger.error("Failed to analyze training plans")
        return 1

    # Step 2: Remove duplicates
    if analysis["duplicates"]:
        logger.info("\n" + "=" * 60)
        logger.info("Found duplicates - proceeding with removal")
        logger.info("=" * 60)
        if not remove_duplicates(analysis["duplicates"]):
            logger.error("Failed to remove duplicates")
            return 1
    else:
        logger.info("\nNo duplicates found")

    # Step 3: Fix rest day schedule
    if analysis["non_monday_rest"]:
        logger.info("\n" + "=" * 60)
        logger.info(f"Found {len(analysis['non_monday_rest'])} rest days not on Monday")
        logger.info("=" * 60)
        if not fix_rest_day_schedule(analysis["non_monday_rest"]):
            logger.error("Failed to fix rest day schedule")
            return 1
    else:
        logger.info("\nAll rest days are already on Monday")

    logger.info("\n" + "=" * 60)
    logger.info("Complete!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("1. Verify training plans in Airtable")
    logger.info("2. Check that rest days are on Mondays")
    logger.info("3. Verify no duplicate records exist")

    return 0


if __name__ == "__main__":
    sys.exit(main())
