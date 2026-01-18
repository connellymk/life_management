#!/usr/bin/env python3
"""
Update Airtable table fields to match the sync script requirements.

This script checks which fields need to be updated in:
- Training Sessions table
- Health Metrics table

To keep field names consistent with the sync code.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pyairtable import Api
from core.config import Config
from core.utils import setup_logging

logger = setup_logging("update_airtable_fields")


def update_training_sessions_fields():
    """Check Training Sessions table fields."""
    logger.info("=" * 60)
    logger.info("Training Sessions Table Fields")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        base = api.base(Config.AIRTABLE_BASE_ID)
        schema = base.schema()

        # Find Training Sessions table
        training_table = None
        for table in schema.tables:
            if table.name == Config.AIRTABLE_TRAINING_SESSIONS:
                training_table = table
                break

        if not training_table:
            logger.error(f"✗ Training Sessions table not found")
            return False

        logger.info(f"✓ Found Training Sessions table (ID: {training_table.id})")

        # Field updates needed
        field_updates = {
            'Duration (min)': 'Duration',
            'Distance (mi)': 'Distance',
            'Elevation Gain (ft)': 'Elevation Gain',
            'Avg HR': 'Average HR',
            'Avg Pace (min/mi)': 'Average Pace',
            'Avg Speed (mph)': 'Average Speed',
        }

        logger.info("\n⚠️  MANUAL ACTION REQUIRED:")
        logger.info("=" * 60)
        logger.info("Rename these fields in the Airtable UI:\n")

        logger.info("1. Open your Airtable base in a browser")
        logger.info(f"2. Go to the '{Config.AIRTABLE_TRAINING_SESSIONS}' table")
        logger.info("3. For each field, click header → 'Customize field type' → Change name:\n")

        for old_name, new_name in field_updates.items():
            logger.info(f"   • '{old_name}' → '{new_name}'")

        logger.info("\nNOTE: These renames remove the unit suffixes to match the sync code.")
        logger.info("The sync code expects: Duration, Distance, Elevation Gain, Average HR, Average Pace")

        return True

    except Exception as e:
        logger.error(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def update_health_metrics_fields():
    """Check Health Metrics table fields."""
    logger.info("\n" + "=" * 60)
    logger.info("Health Metrics Table Fields")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        base = api.base(Config.AIRTABLE_BASE_ID)
        schema = base.schema()

        # Find Health Metrics table
        health_table = None
        for table in schema.tables:
            if table.name == Config.AIRTABLE_HEALTH_METRICS:
                health_table = table
                break

        if not health_table:
            logger.error(f"✗ Health Metrics table not found")
            return False

        logger.info(f"✓ Found Health Metrics table (ID: {health_table.id})")

        # Get existing field names
        existing_fields = {field.name for field in health_table.fields}
        logger.info(f"\nCurrent fields: {sorted(existing_fields)}")

        # Define required fields with their types
        required_fields = {
            'Resting HR': 'number',
            'HRV': 'number',
            'Sleep Duration': 'number',  # seconds
            'Deep Sleep': 'number',  # seconds
            'REM Sleep': 'number',  # seconds
            'Light Sleep': 'number',  # seconds
            'Awake Time': 'number',  # seconds
            'Sleep Score': 'number',
            'Steps': 'number',
            'Floors Climbed': 'number',
            'Active Calories': 'number',
            'Total Calories': 'number',
            'Intensity Minutes': 'number',
            'Moderate Intensity Minutes': 'number',
            'Vigorous Intensity Minutes': 'number',
            'Stress Level': 'number',
            'Max Stress': 'number',
            'Body Battery': 'number',
        }

        # Find missing fields
        missing_fields = []
        for field_name, field_type in required_fields.items():
            if field_name not in existing_fields:
                missing_fields.append((field_name, field_type))

        if missing_fields:
            logger.info(f"\n⚠️  Missing fields to add ({len(missing_fields)}):")
            logger.info("=" * 60)
            logger.info("\nPlease add these fields to the 'Health Metrics' table in Airtable:\n")

            for field_name, field_type in sorted(missing_fields):
                type_display = {
                    'number': 'Number',
                }.get(field_type, field_type)
                logger.info(f"   • {field_name} ({type_display})")

        else:
            logger.info("\n✓ All required fields already exist!")

        return True

    except Exception as e:
        logger.error(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("Airtable Field Update Script")
    logger.info("=" * 60)
    logger.info("\nThis script checks which fields need to be updated in Airtable")
    logger.info("to match the sync script requirements.\n")

    success = True

    # Check Training Sessions fields
    if not update_training_sessions_fields():
        success = False

    # Check Health Metrics fields
    if not update_health_metrics_fields():
        success = False

    logger.info("\n" + "=" * 60)
    if success:
        logger.info("✓ Field check complete!")
        logger.info("\nPlease make the manual changes listed above in Airtable,")
        logger.info("then run the health sync again:")
        logger.info("  python orchestrators/sync_health.py --start-date 2026-01-01 --end-date 2026-01-17")
    else:
        logger.info("✗ Some checks failed")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
