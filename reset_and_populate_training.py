#!/usr/bin/env python3
"""
Reset Training Plans table and repopulate with correct dates.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pyairtable import Api
from core.config import Config
from core.utils import setup_logging

logger = setup_logging("reset_training")

TRAINING_PLANS_TABLE_ID = "tblxSnGD6CS9ea0cM"


def delete_all_training_plans():
    """Delete all existing training plan records."""
    logger.info("=" * 60)
    logger.info("Deleting All Training Plans")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        table = api.table(Config.AIRTABLE_BASE_ID, TRAINING_PLANS_TABLE_ID)

        # Get all records
        records = table.all()
        logger.info(f"Found {len(records)} records to delete")

        if not records:
            logger.info("No records to delete")
            return True

        # Delete in batches of 10
        record_ids = [r["id"] for r in records]
        batch_size = 10
        deleted_count = 0

        for i in range(0, len(record_ids), batch_size):
            batch = record_ids[i:i + batch_size]
            try:
                table.batch_delete(batch)
                deleted_count += len(batch)
                logger.info(f"  Deleted {deleted_count}/{len(record_ids)} records...")
            except Exception as e:
                logger.error(f"  Failed to delete batch: {e}")

        logger.info(f"\nSuccessfully deleted {deleted_count} records")
        return True

    except Exception as e:
        logger.error(f"Error deleting records: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    # Step 1: Delete all existing records
    if not delete_all_training_plans():
        logger.error("Failed to delete existing records")
        return 1

    # Step 2: Run populate script
    logger.info("\n" + "=" * 60)
    logger.info("Now running populate_training_plans.py...")
    logger.info("=" * 60)

    import populate_training_plans
    result = populate_training_plans.main()

    if result == 0:
        logger.info("\n" + "=" * 60)
        logger.info("SUCCESS!")
        logger.info("=" * 60)
        logger.info("Training plans have been reset and repopulated with correct dates")
        logger.info("Start date: Monday, January 19, 2026")
        logger.info("Race date: Saturday, July 12, 2026")

    return result


if __name__ == "__main__":
    sys.exit(main())
