#!/usr/bin/env python3
"""
Google Calendar → Obsidian Sync Orchestrator

Fetches events from Google Calendar and exports them directly to Obsidian vault as markdown files.
Bypasses Notion entirely for a simpler, direct sync workflow.

Usage:
    python orchestrators/sync_calendar_to_obsidian.py
    python orchestrators/sync_calendar_to_obsidian.py --dry-run
    python orchestrators/sync_calendar_to_obsidian.py --vault-path /path/to/vault
    python orchestrators/sync_calendar_to_obsidian.py --start-date 2026-02-01 --end-date 2026-03-01
    python orchestrators/sync_calendar_to_obsidian.py --clean-old 90
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from integrations.google_calendar.sync import GoogleCalendarSync
from integrations.obsidian.export import ObsidianExporter
from core.config import GoogleCalendarConfig
from core.utils import logger


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Sync Google Calendar events to Obsidian vault"
    )

    parser.add_argument(
        "--vault-path",
        type=str,
        default="/Users/marykate/Desktop/mkc",
        help="Path to Obsidian vault (default: /Users/marykate/Desktop/mkc)"
    )

    parser.add_argument(
        "--events-folder",
        type=str,
        default="1. Life Areas/Calendar/Events",
        help="Folder within vault for events (default: 1. Life Areas/Calendar/Events)"
    )

    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date for sync (YYYY-MM-DD). Default: 30 days ago"
    )

    parser.add_argument(
        "--end-date",
        type=str,
        help="End date for sync (YYYY-MM-DD). Default: 90 days from now"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing files"
    )

    parser.add_argument(
        "--clean-old",
        type=int,
        metavar="DAYS",
        help="Remove event files older than DAYS (e.g., --clean-old 90)"
    )

    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Verify configuration and API access"
    )

    return parser.parse_args()


def health_check(vault_path: str) -> bool:
    """
    Verify configuration and API access

    Returns:
        True if all checks pass, False otherwise
    """
    logger.info("Running health checks...")
    all_good = True

    # Check vault path
    vault = Path(vault_path)
    if not vault.exists():
        logger.error(f"❌ Vault path does not exist: {vault_path}")
        all_good = False
    else:
        logger.info(f"✅ Vault path exists: {vault_path}")

    # Check Google Calendar credentials
    try:
        calendar_sync = GoogleCalendarSync()
        if calendar_sync.authenticate():
            logger.info("✅ Google Calendar authentication successful")
        else:
            logger.error("❌ Google Calendar authentication failed")
            all_good = False
    except Exception as e:
        logger.error(f"❌ Google Calendar setup error: {e}")
        all_good = False

    # Check calendar configuration
    if GoogleCalendarConfig.GOOGLE_CALENDAR_IDS:
        logger.info(f"✅ Found {len(GoogleCalendarConfig.GOOGLE_CALENDAR_IDS)} calendar(s) configured")
    else:
        logger.error("❌ No calendars configured in GOOGLE_CALENDAR_IDS")
        all_good = False

    if all_good:
        logger.info("✅ All health checks passed!")
    else:
        logger.error("❌ Some health checks failed. Please review the errors above.")

    return all_good


def sync_calendar_to_obsidian(
    vault_path: str,
    events_folder: str,
    start_date: str = None,
    end_date: str = None,
    dry_run: bool = False
) -> bool:
    """
    Main sync function: Google Calendar → Obsidian

    Args:
        vault_path: Path to Obsidian vault
        events_folder: Folder within vault for calendar events
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        dry_run: If True, preview without writing

    Returns:
        True if successful, False otherwise
    """
    logger.info("=" * 60)
    logger.info("Google Calendar → Obsidian Sync")
    logger.info("=" * 60)

    if dry_run:
        logger.info("🔍 DRY RUN MODE - No files will be written")

    # Set date range
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")

    logger.info(f"Date range: {start_date} to {end_date}")

    try:
        # Initialize Google Calendar sync
        logger.info("\n📅 Authenticating with Google Calendar...")
        calendar_sync = GoogleCalendarSync()
        if not calendar_sync.authenticate():
            logger.error("Failed to authenticate with Google Calendar")
            return False

        # Initialize Obsidian exporter
        logger.info(f"\n📝 Initializing Obsidian exporter...")
        exporter = ObsidianExporter(vault_path, events_folder)

        # Process each calendar
        total_stats = {"created": 0, "updated": 0, "skipped": 0}

        for i, calendar_id in enumerate(GoogleCalendarConfig.GOOGLE_CALENDAR_IDS):
            calendar_name = GoogleCalendarConfig.GOOGLE_CALENDAR_NAMES[i] if i < len(GoogleCalendarConfig.GOOGLE_CALENDAR_NAMES) else calendar_id

            logger.info(f"\n📆 Processing calendar: {calendar_name}")

            # Fetch events from Google Calendar
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

            events = calendar_sync.get_calendar_events(
                calendar_id=calendar_id,
                start_date=start_dt,
                end_date=end_dt
            )

            if not events:
                logger.info(f"No events found for {calendar_name}")
                continue

            logger.info(f"Found {len(events)} events")

            # Export to Obsidian
            stats = exporter.export_events(events, calendar_name, dry_run)

            # Aggregate stats
            for key in total_stats:
                total_stats[key] += stats[key]

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("Sync Complete!")
        logger.info("=" * 60)
        logger.info(f"Created: {total_stats['created']}")
        logger.info(f"Updated: {total_stats['updated']}")
        logger.info(f"Skipped: {total_stats['skipped']}")
        logger.info(f"Total events processed: {sum(total_stats.values())}")

        if dry_run:
            logger.info("\n🔍 This was a DRY RUN - no files were actually written")

        return True

    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        return False


def main():
    """Main entry point"""
    args = parse_args()

    # Health check mode
    if args.health_check:
        success = health_check(args.vault_path)
        sys.exit(0 if success else 1)

    # Clean old events mode
    if args.clean_old:
        logger.info(f"Cleaning events older than {args.clean_old} days...")
        exporter = ObsidianExporter(args.vault_path, args.events_folder)
        deleted = exporter.clean_old_events(args.clean_old, args.dry_run)
        logger.info(f"Cleaned {deleted} old event files")
        sys.exit(0)

    # Regular sync
    success = sync_calendar_to_obsidian(
        vault_path=args.vault_path,
        events_folder=args.events_folder,
        start_date=args.start_date,
        end_date=args.end_date,
        dry_run=args.dry_run
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
