#!/usr/bin/env python3
"""
Verify the training plan migration results.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pyairtable import Api
from core.config import Config
from core.utils import setup_logging

logger = setup_logging("verify_migration")

PLANNED_TRAINING_ACTIVITIES_TABLE_ID = "tblxSnGD6CS9ea0cM"
WEEKLY_PLANNING_TABLE_ID = "tbl2B7ecl7heYiKha"


def verify_planned_activities_schema():
    """Verify Planned Training Activities table schema."""
    logger.info("=" * 60)
    logger.info("Verifying Planned Training Activities Table")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        base = api.base(Config.AIRTABLE_BASE_ID)
        schema = base.schema()

        # Find the table
        table = None
        for t in schema.tables:
            if t.id == PLANNED_TRAINING_ACTIVITIES_TABLE_ID:
                table = t
                break

        if not table:
            logger.error(f"Table {PLANNED_TRAINING_ACTIVITIES_TABLE_ID} not found")
            return False

        logger.info(f"Table: {table.name}")
        logger.info(f"Total fields: {len(table.fields)}")

        # Check for required fields
        required_fields = [
            "Name", "Date", "Week Number", "Day of Week", "Status",
            "Workout Type", "Training Phase", "Priority", "Focus Areas",
            "Workout Description", "Planned Distance", "Planned Duration",
            "Planned Elevation Gain", "Target Pace Effort", "Workout Notes",
            "Weekly Mileage Target", "Weekly Elevation Target"
        ]

        existing_field_names = [f.name for f in table.fields]

        missing = []
        for field_name in required_fields:
            if field_name in existing_field_names:
                logger.info(f"  Found: {field_name}")
            else:
                missing.append(field_name)
                logger.error(f"  Missing: {field_name}")

        if missing:
            logger.error(f"\nMissing {len(missing)} required fields")
            return False
        else:
            logger.info(f"\nAll {len(required_fields)} required fields present")

        return True

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_weekly_planning_schema():
    """Verify Weekly Planning table schema."""
    logger.info("\n" + "=" * 60)
    logger.info("Verifying Weekly Planning Table")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        base = api.base(Config.AIRTABLE_BASE_ID)
        schema = base.schema()

        # Find the table
        table = None
        for t in schema.tables:
            if t.id == WEEKLY_PLANNING_TABLE_ID:
                table = t
                break

        if not table:
            logger.error(f"Table {WEEKLY_PLANNING_TABLE_ID} not found")
            return False

        logger.info(f"Table: {table.name}")
        logger.info(f"Total fields: {len(table.fields)}")

        # Check for required fields
        required_fields = [
            "Week Number", "Week Starting", "Week Ending", "Training Phase",
            "Weekly Goals", "Mileage Target", "Elevation Target", "Key Workouts",
            "Weekly Reflection", "Challenges", "Wins", "Energy Level",
            "Recovery Quality", "Overall Rating", "Adjustments Made",
            "Next Week Focus", "Notes"
        ]

        existing_field_names = [f.name for f in table.fields]

        missing = []
        for field_name in required_fields:
            if field_name in existing_field_names:
                logger.info(f"  Found: {field_name}")
            else:
                missing.append(field_name)
                logger.error(f"  Missing: {field_name}")

        if missing:
            logger.error(f"\nMissing {len(missing)} required fields")
            return False
        else:
            logger.info(f"\nAll {len(required_fields)} required fields present")

        return True

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_weekly_goals():
    """Verify weekly goals have been populated."""
    logger.info("\n" + "=" * 60)
    logger.info("Verifying Weekly Goals")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        table = api.table(Config.AIRTABLE_BASE_ID, WEEKLY_PLANNING_TABLE_ID)

        # Fetch all records
        records = table.all()
        logger.info(f"Total weekly records: {len(records)}")

        # Check records with week numbers 1-25
        weeks_with_goals = 0
        weeks_with_phase = 0
        weeks_with_number = 0

        for record in records:
            fields = record["fields"]
            week_number = fields.get("Week Number")

            if week_number and 1 <= week_number <= 25:
                weeks_with_number += 1

                if fields.get("Weekly Goals"):
                    weeks_with_goals += 1

                if fields.get("Training Phase"):
                    weeks_with_phase += 1

                # Show sample for first 3 weeks
                if week_number <= 3:
                    logger.info(f"\nWeek {week_number}:")
                    logger.info(f"  Phase: {fields.get('Training Phase', 'Not set')}")
                    goals = fields.get('Weekly Goals', 'Not set')
                    if goals and len(goals) > 80:
                        goals = goals[:80] + "..."
                    logger.info(f"  Goals: {goals}")

        logger.info(f"\nSummary (Weeks 1-25):")
        logger.info(f"  Records with Week Number: {weeks_with_number}/25")
        logger.info(f"  Records with Training Phase: {weeks_with_phase}/25")
        logger.info(f"  Records with Weekly Goals: {weeks_with_goals}/25")

        success = (weeks_with_number == 25 and
                   weeks_with_phase == 25 and
                   weeks_with_goals == 25)

        if success:
            logger.info("\nAll 25 weeks have goals and phases!")
        else:
            logger.warning(f"\nSome weeks are missing data")

        return success

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("Training Plan Migration Verification")
    logger.info("=" * 60)

    success = True

    # Verify Planned Training Activities schema
    if not verify_planned_activities_schema():
        success = False

    # Verify Weekly Planning schema
    if not verify_weekly_planning_schema():
        success = False

    # Verify Weekly Goals
    if not verify_weekly_goals():
        success = False

    logger.info("\n" + "=" * 60)
    if success:
        logger.info("VERIFICATION PASSED")
        logger.info("=" * 60)
        logger.info("\nAll schemas and data are correctly set up!")
    else:
        logger.info("VERIFICATION FAILED")
        logger.info("=" * 60)
        logger.info("\nSome issues were found. Check logs above.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
