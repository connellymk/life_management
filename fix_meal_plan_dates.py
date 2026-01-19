#!/usr/bin/env python3
"""
Fix Planned Meals dates to align with correct training plan start date.
The meals should start on Monday, January 19, 2026 (not Tuesday, January 20).
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from pyairtable import Api
from core.config import Config
from core.utils import setup_logging

logger = setup_logging("fix_meal_dates")

PLANNED_MEALS_TABLE_ID = "tblTAfTWjHWwjV30Y"
MEAL_PLANS_TABLE_ID = "tblXeRfKofAHtbt6e"
DAY_TABLE_ID = "tblHMwUnVg8bA1xoP"

CORRECT_START = datetime(2026, 1, 19)  # Monday
WRONG_START = datetime(2026, 1, 20)    # Tuesday


def fix_meal_plan_dates():
    """Fix the start dates in Meal Plans and Planned Meals."""
    logger.info("=" * 60)
    logger.info("Fixing Meal Plan Dates")
    logger.info("=" * 60)
    logger.info(f"Correct start: {CORRECT_START.strftime('%A, %B %d, %Y')}")
    logger.info(f"Wrong start: {WRONG_START.strftime('%A, %B %d, %Y')}")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        meal_plans_table = api.table(Config.AIRTABLE_BASE_ID, MEAL_PLANS_TABLE_ID)
        planned_meals_table = api.table(Config.AIRTABLE_BASE_ID, PLANNED_MEALS_TABLE_ID)
        day_table = api.table(Config.AIRTABLE_BASE_ID, DAY_TABLE_ID)

        # Get all records
        meal_plans = meal_plans_table.all()
        planned_meals = planned_meals_table.all()
        day_records = day_table.all()

        logger.info(f"\nFound {len(meal_plans)} meal plans")
        logger.info(f"Found {len(planned_meals)} planned meals")
        logger.info(f"Found {len(day_records)} day records")

        # Create date lookup: date string -> day record ID
        date_to_day = {}
        for record in day_records:
            date_str = record["fields"].get("Day")
            if date_str:
                date_to_day[date_str] = record["id"]

        # Step 1: Fix Meal Plans start date
        logger.info("\n" + "=" * 60)
        logger.info("Step 1: Updating Meal Plans")
        logger.info("=" * 60)

        for meal_plan in meal_plans:
            fields = meal_plan["fields"]
            start_date = fields.get("Start Date")

            if start_date == "2026-01-20":
                logger.info(f"\nUpdating: {fields.get('Name')}")
                logger.info(f"  Old start: {start_date}")
                logger.info(f"  New start: 2026-01-19")

                meal_plans_table.update(meal_plan["id"], {
                    "Start Date": "2026-01-19"
                })
                logger.info("  ✓ Updated")

        # Step 2: Fix Planned Meals day links
        logger.info("\n" + "=" * 60)
        logger.info("Step 2: Updating Planned Meals")
        logger.info("=" * 60)

        # Build lookup: old day ID -> new day ID (shifting back by 1 day)
        day_shift_map = {}
        for record in day_records:
            date_str = record["fields"].get("Day")
            if date_str:
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    # If this date is >= Jan 20, find the corresponding day 1 day earlier
                    if date_obj >= WRONG_START:
                        new_date = date_obj - timedelta(days=1)
                        new_date_str = new_date.strftime("%Y-%m-%d")
                        if new_date_str in date_to_day:
                            day_shift_map[record["id"]] = date_to_day[new_date_str]
                except:
                    pass

        updates_needed = []
        for meal in planned_meals:
            fields = meal["fields"]
            if "Day" in fields and fields["Day"]:
                old_day_id = fields["Day"][0]
                if old_day_id in day_shift_map:
                    new_day_id = day_shift_map[old_day_id]
                    updates_needed.append({
                        "id": meal["id"],
                        "old_day": old_day_id,
                        "new_day": new_day_id,
                        "name": fields.get("Name", "N/A")
                    })

        logger.info(f"\nFound {len(updates_needed)} meals to update")

        if updates_needed:
            # Get day info for logging
            day_info = {r["id"]: r["fields"] for r in day_records}

            logger.info("\nSample updates:")
            for update in updates_needed[:5]:
                old_date = day_info.get(update["old_day"], {}).get("Day", "Unknown")
                new_date = day_info.get(update["new_day"], {}).get("Day", "Unknown")
                logger.info(f"  {update['name']}: {old_date} → {new_date}")

            # Batch update
            batch_updates = [{"id": u["id"], "fields": {"Day": [u["new_day"]]}} for u in updates_needed]

            batch_size = 10
            updated_count = 0

            for i in range(0, len(batch_updates), batch_size):
                batch = batch_updates[i:i + batch_size]
                try:
                    planned_meals_table.batch_update(batch)
                    updated_count += len(batch)
                    logger.info(f"  Updated {updated_count}/{len(batch_updates)} meals...")
                except Exception as e:
                    logger.error(f"  Failed to update batch: {e}")

            logger.info(f"\n✓ Successfully updated {updated_count} planned meals")
        else:
            logger.info("\nNo updates needed - all meals are already on correct dates")

        logger.info("\n" + "=" * 60)
        logger.info("COMPLETE!")
        logger.info("=" * 60)
        logger.info("\nMeal plans now start on Monday, January 19, 2026")
        logger.info("All planned meals have been shifted back by 1 day")

        return 0

    except Exception as e:
        logger.error(f"Error fixing meal dates: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point."""
    return fix_meal_plan_dates()


if __name__ == "__main__":
    sys.exit(main())
