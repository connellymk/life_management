#!/usr/bin/env python3
"""
Test script for health sync to Notion.
Verifies the Garmin integration and Notion sync are working correctly.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.utils import setup_logging
from orchestrators.sync_health import health_check

logger = setup_logging("test_health_sync")


def main():
    """Run health check to verify Garmin + Notion integration."""
    logger.info("=" * 60)
    logger.info("Testing Garmin + Notion Health Sync")
    logger.info("=" * 60)

    # Run health check
    success = health_check()

    if success:
        logger.info("\n+ Health sync is ready!")
        logger.info("\nTo sync data, run:")
        logger.info("  python orchestrators/sync_health.py")
        logger.info("\nOptions:")
        logger.info("  --dry-run           Preview sync without making changes")
        logger.info("  --workouts-only     Sync only workouts to Garmin Activities")
        logger.info("  --metrics-only      Sync only daily metrics to Daily Tracking")
        logger.info("  --body-only         Sync only body metrics to Daily Tracking")
        sys.exit(0)
    else:
        logger.error("\nX Health check failed")
        logger.error("\nPlease fix the issues above and try again")
        sys.exit(1)


if __name__ == "__main__":
    main()
