#!/usr/bin/env python3
"""
Populate Day table with date records for a specific date range.
This ensures Day records exist before syncing health data.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from airtable.base_client import AirtableClient
from core.utils import setup_logging

logger = setup_logging("populate_days")


def populate_day_records(start_date: datetime, end_date: datetime):
    """
    Create Day table records for the specified date range.

    Args:
        start_date: Start date
        end_date: End date
    """
    logger.info(f"Populating Day records from {start_date.date()} to {end_date.date()}...")

    client = AirtableClient()
    day_table = client.get_day_table()

    # Generate all dates in range
    current_date = start_date
    days_to_create = []
    days_skipped = 0

    while current_date <= end_date:
        day_value = current_date.strftime("%Y-%m-%d")

        # Check if record already exists
        try:
            existing_id = client.get_day_record_id(day_value)
            logger.debug(f"  Day {day_value} already exists (ID: {existing_id})")
            days_skipped += 1
        except ValueError:
            # Doesn't exist, add to creation list
            days_to_create.append({
                'Day': day_value
            })
            logger.info(f"  Will create Day record for {day_value}")

        current_date += timedelta(days=1)

    # Create records in batch
    if days_to_create:
        logger.info(f"\nCreating {len(days_to_create)} Day records...")
        created = day_table.batch_create(days_to_create)
        logger.info(f"✓ Created {len(created)} Day records")
    else:
        logger.info("\nAll Day records already exist!")

    logger.info(f"\nSummary:")
    logger.info(f"  Created: {len(days_to_create)}")
    logger.info(f"  Skipped (already exist): {days_skipped}")
    logger.info(f"  Total: {(end_date - start_date).days + 1}")


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Populate Day table with date records")
    parser.add_argument("--start-date", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, required=True, help="End date (YYYY-MM-DD)")

    args = parser.parse_args()

    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")

    logger.info("=" * 60)
    logger.info("Populating Day Table")
    logger.info("=" * 60)

    populate_day_records(start_date, end_date)

    logger.info("\n✓ Day table population complete!")
    logger.info("\nYou can now run the health sync:")
    logger.info(f"  python orchestrators/sync_health.py --start-date {args.start_date} --end-date {args.end_date}")


if __name__ == "__main__":
    main()
