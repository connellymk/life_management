#!/usr/bin/env python3
"""
Calendar Sync Orchestrator
Syncs Google Calendar (and future: Microsoft Calendar) to Notion
"""

import sys
import argparse
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import GoogleCalendarConfig as Config
from core.utils import logger, format_duration
from core.state_manager import StateManager
from integrations.google_calendar.sync import GoogleCalendarSync
from notion.calendar import NotionSync


def sync_google_calendars(
    notion_sync: NotionSync, state_manager: StateManager, dry_run: bool = False
) -> dict:
    """
    Sync all configured Google Calendars

    Args:
        notion_sync: NotionSync instance
        state_manager: StateManager instance for incremental sync
        dry_run: If True, don't actually create/update in Notion

    Returns:
        Dictionary with sync statistics
    """
    logger.info("=" * 60)
    logger.info("Starting Google Calendar Sync")
    logger.info("=" * 60)

    google_sync = GoogleCalendarSync()

    # Authenticate
    logger.info("Authenticating with Google Calendar...")
    if not google_sync.authenticate():
        logger.error("Failed to authenticate with Google Calendar")
        return {"success": False, "error": "Authentication failed"}

    logger.info("✓ Authenticated successfully")

    # Sync each configured calendar
    total_stats = {
        "success": True,
        "calendars_synced": 0,
        "total_events_fetched": 0,
        "total_events_created": 0,
        "total_events_updated": 0,
        "total_events_skipped": 0,
        "total_errors": 0,
        "calendar_details": [],
    }

    for calendar_id, calendar_name in zip(
        Config.GOOGLE_CALENDAR_IDS, Config.GOOGLE_CALENDAR_NAMES
    ):
        calendar_id = calendar_id.strip()
        calendar_name = calendar_name.strip()

        logger.info(f"\nSyncing calendar: {calendar_name} ({calendar_id})")

        try:
            stats = google_sync.sync_calendar_to_notion(
                calendar_id=calendar_id,
                calendar_name=calendar_name,
                notion_sync=notion_sync,
                state_manager=state_manager,
                use_incremental=True,
                dry_run=dry_run,
            )

            total_stats["calendars_synced"] += 1
            total_stats["total_events_fetched"] += stats["events_fetched"]
            total_stats["total_events_created"] += stats["events_created"]
            total_stats["total_events_updated"] += stats["events_updated"]
            total_stats["total_events_skipped"] += stats["events_skipped"]
            total_stats["total_errors"] += stats["errors"]
            total_stats["calendar_details"].append(stats)

        except Exception as e:
            logger.error(f"Error syncing calendar '{calendar_name}': {e}")
            total_stats["total_errors"] += 1

    return total_stats


def print_sync_summary(stats: dict, duration: float, dry_run: bool = False):
    """
    Print a summary of the sync operation

    Args:
        stats: Statistics dictionary
        duration: Duration in seconds
        dry_run: Whether this was a dry run
    """
    print("\n" + "=" * 60)
    if dry_run:
        print("  SYNC SUMMARY (DRY RUN - No changes made)")
    else:
        print("  SYNC SUMMARY")
    print("=" * 60)

    if not stats.get("success", True):
        print(f"\n❌ Sync failed: {stats.get('error', 'Unknown error')}")
        return

    print(f"\nCalendars synced: {stats['calendars_synced']}")
    print(f"Events fetched: {stats['total_events_fetched']}")

    if not dry_run:
        print(f"Events created: {stats['total_events_created']}")
        print(f"Events updated: {stats['total_events_updated']}")
        print(f"Events skipped: {stats['total_events_skipped']}")

    if stats['total_errors'] > 0:
        print(f"Errors: {stats['total_errors']}")

    print(f"\nDuration: {format_duration(duration)}")

    # Per-calendar breakdown
    if stats.get("calendar_details"):
        print("\nPer-calendar breakdown:")
        for cal_stats in stats["calendar_details"]:
            print(f"\n  {cal_stats['calendar_name']}:")
            print(f"    Fetched: {cal_stats['events_fetched']}")
            if not dry_run:
                print(f"    Created: {cal_stats['events_created']}")
                print(f"    Updated: {cal_stats['events_updated']}")
                print(f"    Skipped: {cal_stats['events_skipped']}")
            if cal_stats['errors'] > 0:
                print(f"    Errors: {cal_stats['errors']}")

    print("\n" + "=" * 60)

    if not dry_run and stats['total_errors'] == 0:
        print("  ✓ Sync completed successfully!")
    elif stats['total_errors'] > 0:
        print("  ⚠ Sync completed with errors (check logs)")

    print("=" * 60 + "\n")


def main():
    """Main orchestrator function"""
    parser = argparse.ArgumentParser(
        description="Sync Google Calendar to Notion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python orchestrators/sync_calendar.py                 # Run full sync
  python orchestrators/sync_calendar.py --dry-run       # Preview changes
  python orchestrators/sync_calendar.py --health-check  # Check system health

For more information, see README.md and MIGRATION_GUIDE.md
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without making changes",
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Run health checks and exit",
    )

    args = parser.parse_args()

    # Print header
    print("\n" + "=" * 60)
    print("  Calendar Sync Orchestrator")
    print("=" * 60)
    print(f"  Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if args.dry_run:
        print("  Mode: DRY RUN (no changes will be made)")
    print("=" * 60 + "\n")

    # Validate configuration
    logger.info("Validating configuration...")
    is_valid, errors = Config.validate()
    if not is_valid:
        logger.error("Configuration errors found:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.error("\nPlease fix these errors in your .env file")
        logger.error("See MIGRATION_GUIDE.md for instructions")
        return 1

    logger.info("✓ Configuration valid")

    # Health check mode
    if args.health_check:
        logger.info("\nRunning health checks...")
        logger.info("Configuration: ✓")

        # Test Notion connection
        try:
            notion = NotionSync()
            if notion.test_connection():
                logger.info("Notion connection: ✓")
            else:
                logger.error("Notion connection: ✗")
                return 1
        except Exception as e:
            logger.error(f"Notion connection: ✗ ({e})")
            return 1

        # Test Google Calendar auth
        try:
            google_sync = GoogleCalendarSync()
            if google_sync.authenticate():
                logger.info("Google Calendar auth: ✓")
            else:
                logger.error("Google Calendar auth: ✗")
                return 1
        except Exception as e:
            logger.error(f"Google Calendar auth: ✗ ({e})")
            return 1

        print("\n" + "=" * 60)
        print("  ✓ All health checks passed!")
        print("=" * 60 + "\n")
        return 0

    # Initialize state manager
    try:
        state_manager = StateManager()
        logger.info("✓ Initialized state manager")
    except Exception as e:
        logger.error(f"Failed to initialize state manager: {e}")
        return 1

    # Initialize Notion sync with state manager
    try:
        notion_sync = NotionSync(state_manager=state_manager)
        logger.info("✓ Initialized Notion sync")
    except Exception as e:
        logger.error(f"Failed to initialize Notion sync: {e}")
        return 1

    # Start sync
    start_time = time.time()
    overall_success = True

    try:
        # Sync Google Calendars
        stats = sync_google_calendars(
            notion_sync, state_manager, dry_run=args.dry_run
        )
        if not stats.get("success", True):
            overall_success = False

    except KeyboardInterrupt:
        logger.warning("\n\nSync interrupted by user")
        overall_success = False
        stats = {"success": False, "error": "Interrupted by user"}
    except Exception as e:
        logger.error(f"\n\nSync failed with error: {e}")
        logger.exception("Full traceback:")
        overall_success = False
        stats = {"success": False, "error": str(e)}

    # Calculate duration
    duration = time.time() - start_time

    # Print summary
    print_sync_summary(stats, duration, dry_run=args.dry_run)

    # Log to file
    if overall_success:
        logger.info(f"Sync completed successfully in {format_duration(duration)}")
    else:
        logger.error(f"Sync failed after {format_duration(duration)}")

    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())
