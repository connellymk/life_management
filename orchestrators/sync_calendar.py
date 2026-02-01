#!/usr/bin/env python3
"""
Calendar Sync Orchestrator
Syncs Google Calendar (and future: Microsoft Calendar) to Notion

Fetches events from Google Calendar API and creates/updates records in Notion's
Calendar Events database with links to the Day table for rollups and aggregations.
"""

import sys
import argparse
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import GoogleCalendarConfig as Config
from core.utils import logger, format_duration
from core.state_manager import StateManager
from integrations.google_calendar.sync import GoogleCalendarSync
from notion.calendar import NotionCalendarSync


def sync_google_calendars(
    notion_sync: NotionCalendarSync,
    state_manager: StateManager,
    dry_run: bool = False,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> dict:
    """
    Sync all configured Google Calendars to Notion

    Args:
        notion_sync: NotionCalendarSync instance for syncing to Notion
        state_manager: StateManager instance for incremental sync
        dry_run: If True, don't actually create/update in Notion
        start_date: Start date for event range (optional)
        end_date: End date for event range (optional)

    Returns:
        Dictionary with sync statistics
    """
    logger.info("=" * 60)
    logger.info("Starting Google Calendar Sync to Notion")
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
        "total_events_deleted": 0,
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
                start_date=start_date,
                end_date=end_date,
            )

            total_stats["calendars_synced"] += 1
            total_stats["total_events_fetched"] += stats["events_fetched"]
            total_stats["total_events_created"] += stats["events_created"]
            total_stats["total_events_updated"] += stats["events_updated"]
            total_stats["total_events_deleted"] += stats.get("events_deleted", 0)
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
        print(f"Events deleted: {stats.get('total_events_deleted', 0)}")
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
                print(f"    Deleted: {cal_stats.get('events_deleted', 0)}")
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
  python orchestrators/sync_calendar.py                              # Run full sync
  python orchestrators/sync_calendar.py --dry-run                    # Preview changes
  python orchestrators/sync_calendar.py --health-check               # Check system health
  python orchestrators/sync_calendar.py --start-date 2026-01-01 --end-date 2026-12-31  # Sync specific date range

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
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date for event range (YYYY-MM-DD format)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date for event range (YYYY-MM-DD format)",
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

    # Parse date range if provided
    start_date = None
    end_date = None
    if args.start_date or args.end_date:
        try:
            if args.start_date:
                start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
                start_date = start_date.replace(tzinfo=timezone.utc)
                logger.info(f"Start date: {start_date.date()}")
            if args.end_date:
                # Set end_date to end of day (23:59:59)
                end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
                end_date = end_date.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                logger.info(f"End date: {end_date.date()}")
            if start_date and end_date and start_date > end_date:
                logger.error("Start date must be before end date")
                return 1
        except ValueError as e:
            logger.error(f"Invalid date format: {e}")
            logger.error("Dates must be in YYYY-MM-DD format (e.g., 2026-01-01)")
            return 1

    # Health check mode
    if args.health_check:
        logger.info("\nRunning health checks...")
        logger.info("Configuration: ✓")

        # Test Notion connection
        try:
            notion = NotionCalendarSync()
            # Simple test: try to get an event (empty query is fine)
            notion.get_event_by_external_id("__health_check_test__")
            logger.info("Notion connection: ✓")
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

    # Initialize Notion sync
    try:
        notion_sync = NotionCalendarSync()
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
            notion_sync, state_manager, dry_run=args.dry_run,
            start_date=start_date, end_date=end_date
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
