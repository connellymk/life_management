#!/usr/bin/env python3
"""
Health & Training Sync Orchestrator
Syncs Garmin Connect data to Notion:

- Garmin Activities → Notion (workouts/activities)
- Daily Tracking → Notion (daily health data + body metrics combined)
"""

import sys
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import GarminConfig as Config
from core.utils import setup_logging
from core.state_manager import StateManager
from integrations.garmin.sync import GarminSync
from notion.health import NotionActivitiesSync, NotionDailyTrackingSync

logger = setup_logging("health_sync")


def sync_workouts(
    garmin: GarminSync,
    notion_sync: NotionActivitiesSync,
    state: StateManager,
    dry_run: bool = False,
    start_date: datetime = None,
    end_date: datetime = None
) -> dict:
    """
    Sync workouts from Garmin to Notion Garmin Activities database.

    Args:
        garmin: Garmin sync client
        notion_sync: Notion activities sync client
        state: State manager
        dry_run: If True, don't actually create/update records
        start_date: Optional start date
        end_date: Optional end date

    Returns:
        Dictionary with sync stats
    """
    logger.info("=" * 50)
    logger.info("Syncing Workouts to Notion...")
    logger.info("=" * 50)

    start_time = time.time()
    stats = {"fetched": 0, "created": 0, "updated": 0, "errors": 0}

    try:
        # Fetch activities from Garmin
        activities = garmin.get_activities(start_date=start_date, end_date=end_date)
        stats["fetched"] = len(activities)

        if not activities:
            logger.info("No activities found")
            return stats

        logger.info(f"Found {len(activities)} activities")

        if dry_run:
            logger.info("DRY RUN: Would sync the following activities:")
            for activity in activities[:5]:  # Show first 5
                logger.info(f"  - {activity.get('title')} on {activity.get('start_time')}")
            if len(activities) > 5:
                logger.info(f"  ... and {len(activities) - 5} more")
            return stats

        # Sync each activity to Notion
        for activity in activities:
            external_id = activity.get("external_id")

            try:
                # Check if activity already exists
                existing = notion_sync.get_activity_by_external_id(str(external_id))

                if existing:
                    # Update existing
                    notion_sync.update_activity(existing['id'], activity)
                    stats["updated"] += 1
                else:
                    # Create new
                    notion_sync.create_activity(activity)
                    stats["created"] += 1

            except Exception as e:
                logger.error(f"Error syncing activity {external_id}: {e}")
                stats["errors"] += 1

        # Update state
        duration = time.time() - start_time
        state.update_sync_state("garmin_workouts", success=True)
        state.log_sync(
            "garmin_workouts",
            "success",
            stats["created"],
            stats["updated"],
            stats["errors"],
            duration,
        )

        logger.info(f"+ Workout sync complete: {stats['created']} created, {stats['updated']} updated")
        return stats

    except Exception as e:
        logger.error(f"X Workout sync failed: {e}")
        duration = time.time() - start_time
        state.update_sync_state("garmin_workouts", success=False, error=str(e))
        state.log_sync("garmin_workouts", "failure", 0, 0, 0, duration, error=str(e))
        return stats


def sync_daily_metrics(
    garmin: GarminSync,
    notion_sync: NotionDailyTrackingSync,
    dry_run: bool = False,
    start_date: datetime = None,
    end_date: datetime = None
) -> dict:
    """
    Sync daily metrics from Garmin to Notion Daily Tracking database.

    Args:
        garmin: Garmin sync client
        notion_sync: Notion daily tracking sync client
        dry_run: If True, don't actually save data
        start_date: Optional start date
        end_date: Optional end date

    Returns:
        Dictionary with sync stats
    """
    logger.info("=" * 50)
    logger.info("Syncing Daily Metrics to Notion...")
    logger.info("=" * 50)

    start_time = time.time()
    stats = {"fetched": 0, "synced": 0, "errors": 0}

    try:
        # Fetch daily metrics
        daily_metrics = garmin.get_daily_metrics(start_date=start_date, end_date=end_date)
        stats["fetched"] = len(daily_metrics)

        if not daily_metrics:
            logger.info("No daily metrics found")
            return stats

        logger.info(f"Found {len(daily_metrics)} days of metrics")

        if dry_run:
            logger.info("DRY RUN: Would sync the following metrics:")
            for metric in daily_metrics[:5]:  # Show first 5
                logger.info(f"  - {metric.get('date')}: {metric.get('steps')} steps, {metric.get('sleep_hours')}h sleep")
            if len(daily_metrics) > 5:
                logger.info(f"  ... and {len(daily_metrics) - 5} more")
            return stats

        # Sync each day to Notion
        for metric in daily_metrics:
            try:
                # Sync to Notion (create or update)
                result = notion_sync.sync_daily_metrics(metric)
                if result:
                    stats["synced"] += 1

            except Exception as e:
                logger.error(f"Error syncing daily metric for {metric.get('date')}: {e}")
                stats["errors"] += 1

        elapsed = time.time() - start_time
        logger.info(f"Daily metrics sync complete in {elapsed:.1f}s")
        logger.info(f"  Fetched: {stats['fetched']}, Synced: {stats['synced']}, Errors: {stats['errors']}")

        return stats

    except Exception as e:
        logger.error(f"X Daily metrics sync failed: {e}")
        stats["errors"] += 1
        return stats


def sync_body_metrics(
    garmin: GarminSync,
    notion_sync: NotionDailyTrackingSync,
    dry_run: bool = False,
    start_date: datetime = None,
    end_date: datetime = None
) -> dict:
    """
    Sync body composition metrics from Garmin to Notion Daily Tracking database.

    Args:
        garmin: Garmin sync client
        notion_sync: Notion daily tracking sync client
        dry_run: If True, don't actually save data
        start_date: Optional start date
        end_date: Optional end date

    Returns:
        Dictionary with sync stats
    """
    logger.info("=" * 50)
    logger.info("Syncing Body Metrics to Notion...")
    logger.info("=" * 50)

    start_time = time.time()
    stats = {"fetched": 0, "synced": 0, "errors": 0}

    try:
        # Fetch body metrics (if available from Garmin)
        body_metrics = garmin.get_body_composition(start_date=start_date, end_date=end_date)
        stats["fetched"] = len(body_metrics)

        if not body_metrics:
            logger.info("No body metrics found (may not be available from Garmin)")
            return stats

        logger.info(f"Found {len(body_metrics)} body metric entries")

        if dry_run:
            logger.info("DRY RUN: Would sync body metrics")
            for metric in body_metrics[:5]:
                logger.info(f"  - {metric.get('date')}: {metric.get('weight')} lbs")
            if len(body_metrics) > 5:
                logger.info(f"  ... and {len(body_metrics) - 5} more")
            return stats

        # Sync each entry to Notion
        for metric in body_metrics:
            try:
                # Sync to Notion (create or update)
                result = notion_sync.sync_body_metrics(metric)
                if result:
                    stats["synced"] += 1

            except Exception as e:
                logger.error(f"Error syncing body metric for {metric.get('date')}: {e}")
                stats["errors"] += 1

        elapsed = time.time() - start_time
        logger.info(f"Body metrics sync complete in {elapsed:.1f}s")
        logger.info(f"  Fetched: {stats['fetched']}, Synced: {stats['synced']}, Errors: {stats['errors']}")

        return stats

    except Exception as e:
        logger.error(f"X Body metrics sync failed: {e}")
        stats["errors"] += 1
        return stats


def health_check() -> bool:
    """
    Run health check to verify configuration.

    Returns:
        True if all checks pass, False otherwise
    """
    logger.info("=" * 60)
    logger.info("Health Sync - Health Check")
    logger.info("=" * 60)

    # Check Garmin configuration
    logger.info("\n1. Checking Garmin configuration...")
    is_valid, errors = Config.validate()

    if not is_valid:
        logger.error("X Configuration not valid:")
        for error in errors:
            logger.error(f"  - {error}")
        return False

    logger.info("+ Configuration valid")

    # Check Notion connection
    logger.info("\n2. Checking Notion connection...")
    try:
        activities_sync = NotionActivitiesSync()
        tracking_sync = NotionDailyTrackingSync()
        logger.info(f"  + Garmin Activities database: {Config.NOTION_WORKOUTS_DB_ID}")
        logger.info(f"  + Daily Tracking database: {Config.NOTION_DAILY_TRACKING_DB_ID}")

    except Exception as e:
        logger.error(f"  X Notion connection failed: {e}")
        return False

    # Check Garmin credentials
    logger.info("\n3. Checking Garmin authentication...")
    try:
        garmin = GarminSync()
        if garmin.authenticate():
            logger.info("  + Garmin authentication successful")
        else:
            logger.error("  X Garmin authentication failed")
            return False

    except Exception as e:
        logger.error(f"  X Garmin connection failed: {e}")
        return False

    logger.info("\n" + "=" * 60)
    logger.info("+ Health check passed!")
    logger.info("=" * 60)
    logger.info("\nData storage:")
    logger.info("  - Garmin Activities: Notion")
    logger.info("  - Daily Tracking: Notion (daily metrics + body metrics)")
    logger.info(f"  - History: {Config.SYNC_LOOKBACK_DAYS} days")
    logger.info("\nNext steps:")
    logger.info("  1. Run 'python orchestrators/sync_health.py' to sync data")
    logger.info("  2. View data in Notion databases")

    return True


def main():
    """Main sync orchestrator."""
    parser = argparse.ArgumentParser(
        description="Sync health data from Garmin to Notion"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview sync without making changes",
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Run health check to verify configuration",
    )
    parser.add_argument(
        "--workouts-only",
        action="store_true",
        help="Sync only workouts to Notion Garmin Activities",
    )
    parser.add_argument(
        "--metrics-only",
        action="store_true",
        help="Sync only daily metrics to Notion Daily Tracking",
    )
    parser.add_argument(
        "--body-only",
        action="store_true",
        help="Sync only body metrics to Notion Daily Tracking",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date for sync (YYYY-MM-DD format, e.g., 2026-01-01)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date for sync (YYYY-MM-DD format, e.g., 2026-01-17)",
    )

    args = parser.parse_args()

    # Health check mode
    if args.health_check:
        success = health_check()
        sys.exit(0 if success else 1)

    # Parse date arguments
    sync_start_date = None
    sync_end_date = None
    if args.start_date:
        sync_start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    if args.end_date:
        sync_end_date = datetime.strptime(args.end_date, "%Y-%m-%d")

    # Normal sync mode
    logger.info("=" * 60)
    logger.info("Health & Training Data Sync - Starting")
    logger.info("=" * 60)
    logger.info(f"Garmin Activities: Notion")
    logger.info(f"Daily Tracking: Notion (metrics + body)")

    if sync_start_date or sync_end_date:
        start_str = sync_start_date.strftime("%Y-%m-%d") if sync_start_date else "default"
        end_str = sync_end_date.strftime("%Y-%m-%d") if sync_end_date else "default"
        logger.info(f"Date Range: {start_str} to {end_str}")
    else:
        logger.info(f"History: {Config.SYNC_LOOKBACK_DAYS} days")

    if args.dry_run:
        logger.info("! DRY RUN MODE - No changes will be made")

    start_time = time.time()

    try:
        # Initialize clients
        garmin = GarminSync()

        # Initialize a shared Daily Tracking sync (serves as Day table for relations)
        notion_tracking = NotionDailyTrackingSync()

        # Determine what to sync
        sync_all = not any([args.workouts_only, args.metrics_only, args.body_only])

        # Sync workouts to Notion (with Day relation to Daily Tracking)
        workout_stats = {}
        if sync_all or args.workouts_only:
            state_manager = StateManager()
            # Pass daily_tracking_sync to enable Day relations
            notion_activities = NotionActivitiesSync(daily_tracking_sync=notion_tracking)
            workout_stats = sync_workouts(
                garmin, notion_activities, state_manager,
                dry_run=args.dry_run,
                start_date=sync_start_date,
                end_date=sync_end_date
            )

        # Sync daily metrics to Notion
        metrics_stats = {}
        if sync_all or args.metrics_only:
            metrics_stats = sync_daily_metrics(
                garmin, notion_tracking,
                dry_run=args.dry_run,
                start_date=sync_start_date,
                end_date=sync_end_date
            )

        # Sync body metrics to Notion
        body_stats = {}
        if sync_all or args.body_only:
            body_stats = sync_body_metrics(
                garmin, notion_tracking,
                dry_run=args.dry_run,
                start_date=sync_start_date,
                end_date=sync_end_date
            )

        # Summary
        elapsed = time.time() - start_time
        logger.info("\n" + "=" * 60)
        logger.info(f"Health sync complete in {elapsed:.1f}s")
        logger.info("=" * 60)

        if not args.dry_run:
            if sync_all or args.workouts_only:
                logger.info("\nNotion Garmin Activities:")
                logger.info(f"  Created: {workout_stats.get('created', 0)}")
                logger.info(f"  Updated: {workout_stats.get('updated', 0)}")

            if sync_all or args.metrics_only:
                logger.info("\nNotion Daily Tracking (metrics):")
                logger.info(f"  Synced: {metrics_stats.get('synced', 0)}")

            if sync_all or args.body_only:
                logger.info("\nNotion Daily Tracking (body):")
                logger.info(f"  Synced: {body_stats.get('synced', 0)}")

            logger.info("\n+ Data synced successfully")
            logger.info("  - View in Notion databases")

    except Exception as e:
        logger.error(f"\nX Sync failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
