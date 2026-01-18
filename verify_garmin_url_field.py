#!/usr/bin/env python3
"""
Verify that the Garmin URL field exists in the Training Sessions table.
If it doesn't exist, provide instructions to add it.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pyairtable import Api
from core.config import Config
from core.utils import setup_logging

logger = setup_logging("verify_garmin_url")


def main():
    """Check if Garmin URL field exists in Training Sessions table."""
    logger.info("=" * 60)
    logger.info("Verifying Garmin URL Field")
    logger.info("=" * 60)

    try:
        # Connect to Airtable
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        base = api.base(Config.AIRTABLE_BASE_ID)

        # Get schema
        schema = base.schema()
        training_table = None

        for table in schema.tables:
            if table.name == Config.AIRTABLE_TRAINING_SESSIONS:
                training_table = table
                break

        if not training_table:
            logger.error(f"✗ Training Sessions table not found")
            logger.error(f"  Expected table name: {Config.AIRTABLE_TRAINING_SESSIONS}")
            sys.exit(1)

        logger.info(f"✓ Found Training Sessions table (ID: {training_table.id})")

        # Check for Garmin URL field
        garmin_url_field = None
        url_fields = []

        for field in training_table.fields:
            if field.type == 'url':
                url_fields.append(field.name)
                if field.name == 'Garmin URL':
                    garmin_url_field = field

        logger.info(f"\nURL fields in Training Sessions: {url_fields if url_fields else 'None'}")

        if garmin_url_field:
            logger.info("\n" + "=" * 60)
            logger.info("✓ Garmin URL field exists!")
            logger.info("=" * 60)
            logger.info(f"\nField name: {garmin_url_field.name}")
            logger.info(f"Field type: {garmin_url_field.type}")
            logger.info(f"Field ID: {garmin_url_field.id}")
            if garmin_url_field.description:
                logger.info(f"Description: {garmin_url_field.description}")

            logger.info("\n✓ Ready to sync! The Garmin sync will populate this field with activity URLs.")
            logger.info("\nTo sync Garmin data:")
            logger.info("  python orchestrators/sync_health.py")
            sys.exit(0)
        else:
            logger.warning("\n" + "=" * 60)
            logger.warning("! Garmin URL field NOT FOUND")
            logger.warning("=" * 60)
            logger.warning("\nYou need to add this field to your Training Sessions table.")
            logger.warning("\nOption 1: Add Manually in Airtable (EASIEST)")
            logger.warning("-" * 60)
            logger.warning("1. Open your Airtable base in a browser")
            logger.warning("2. Go to the 'Training Sessions' table")
            logger.warning("3. Click the '+' button to add a new field")
            logger.warning("4. Configure:")
            logger.warning("   - Field name: Garmin URL")
            logger.warning("   - Field type: URL")
            logger.warning("   - Description: Direct link to activity on Garmin Connect")
            logger.warning("5. Click 'Create field'")
            logger.warning("\nOption 2: Use Airtable REST API")
            logger.warning("-" * 60)
            logger.warning(f"Table ID: {training_table.id}")
            logger.warning(f"Base ID: {Config.AIRTABLE_BASE_ID}")
            logger.warning("\nSee add_garmin_url_field.md for detailed API instructions")
            logger.warning("\nAfter adding the field, run this script again to verify:")
            logger.warning("  python verify_garmin_url_field.py")
            sys.exit(1)

    except Exception as e:
        logger.error(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
