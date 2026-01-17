#!/usr/bin/env python3
"""
Health & Training Sync Orchestrator
Syncs Garmin Connect data:
- Workouts → Notion (manual annotations useful)
- Daily Metrics → SQL database (high volume, analytics)
- Body Metrics → SQL database (if available)
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
from core.database import Database
from storage.health import HealthStorage
from integrations.garmin.sync import GarminSync
from notion.health import NotionSync

logger = setup_logging("health_sync")


def sync_workouts(garmin: GarminSync, notion: NotionSync, state: StateManager, dry_run: bool = False) -> dict:
    """
    Sync workouts from Garmin to Notion.

    Workouts stay in Notion because:
    - Manual annotations/notes are useful
    - Low volume (~100 activities)
    - Visual workout log is helpful

    Args:
        garmin: Garmin sync client
        notion: Notion sync client
        state: State manager
        dry_run: If True, don't actually create/update pages

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
        activities = garmin.get_activities()
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
            existing_page_id = state.get_notion_page_id(external_id)

            try:
                if existing_page_id:
                    # Update existing
                    result = notion.update_workout(existing_page_id, activity)
                    if result:
                        stats["updated"] += 1
                else:
                    # Create new
                    result = notion.create_workout(activity)
                    if result:
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


def sync_daily_metrics(garmin: GarminSync, storage: HealthStorage, dry_run: bool = False) -> dict:
    """
    Sync daily metrics from Garmin to SQL database.

    Daily metrics go to SQL because:
    - High volume (365+ days per year)
    - Need historical analysis
    - SQL queries for trends/correlations

    Args:
        garmin: Garmin sync client
        storage: Health storage client
        dry_run: If True, don't actually save data

    Returns:
        Dictionary with sync stats
    """
    logger.info("=" * 50)
    logger.info("Syncing Daily Metrics to SQL...")
    logger.info("=" * 50)

    start_time = time.time()
    stats = {"fetched": 0, "saved": 0, "errors": 0}

    try:
        # Fetch daily metrics (uses SYNC_LOOKBACK_DAYS from config, defaults to 90 days)
        daily_metrics = garmin.get_daily_metrics()
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

        # Save each day to SQL (upsert for updates)
        for metric in daily_metrics:
            try:
                if storage.save_daily_metric(metric):
                    stats["saved"] += 1
            except Exception as e:
                logger.error(f"Error saving daily metric for {metric.get('date')}: {e}")
                stats["errors"] += 1

        elapsed = time.time() - start_time
        logger.info(f"Daily metrics sync complete in {elapsed:.1f}s")
        logger.info(f"  Fetched: {stats['fetched']}, Saved: {stats['saved']}, Errors: {stats['errors']}")

        return stats

    except Exception as e:
        logger.error(f"X Daily metrics sync failed: {e}")
        stats["errors"] += 1
        return stats


def sync_body_metrics(garmin: GarminSync, storage: HealthStorage, dry_run: bool = False) -> dict:
    """
    Sync body composition metrics from Garmin to SQL database.

    Args:
        garmin: Garmin sync client
        storage: Health storage client
        dry_run: If True, don't actually save data

    Returns:
        Dictionary with sync stats
    """
    logger.info("=" * 50)
    logger.info("Syncing Body Metrics to SQL...")
    logger.info("=" * 50)

    start_time = time.time()
    stats = {"fetched": 0, "saved": 0, "errors": 0}

    try:
        # Fetch body metrics (if available from Garmin)
        body_metrics = garmin.get_body_composition()
        stats["fetched"] = len(body_metrics)

        if not body_metrics:
            logger.info("No body metrics found (may not be available from Garmin)")
            return stats

        logger.info(f"Found {len(body_metrics)} body metric entries")

        if dry_run:
            logger.info("DRY RUN: Would sync body metrics")
            return stats

        # Save each entry to SQL
        for metric in body_metrics:
            try:
                if storage.save_body_metric(metric):
                    stats["saved"] += 1
            except Exception as e:
                logger.error(f"Error saving body metric: {e}")
                stats["errors"] += 1

        elapsed = time.time() - start_time
        logger.info(f"Body metrics sync complete in {elapsed:.1f}s")
        logger.info(f"  Fetched: {stats['fetched']}, Saved: {stats['saved']}, Errors: {stats['errors']}")

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

    # Check configuration
    logger.info("\n1. Checking configuration...")
    is_valid, errors = Config.validate()

    if not is_valid:
        logger.error("X Configuration not valid:")
        for error in errors:
            logger.error(f"  - {error}")
        return False

    logger.info("+ Configuration valid")

    # Check Notion connection (for workouts)
    logger.info("\n2. Checking Notion connection (for workouts)...")
    try:
        from notion_client import Client

        client = Client(auth=Config.NOTION_TOKEN)
        response = client.databases.retrieve(database_id=Config.NOTION_WORKOUTS_DB_ID)
        logger.info("  + Workouts database accessible")

    except Exception as e:
        logger.error(f"  X Notion connection failed: {e}")
        return False

    # Check SQL database (for daily metrics)
    logger.info("\n3. Checking SQL database (for daily metrics)...")
    try:
        db = Database(Config.DATA_DB_PATH)
        is_valid, errors = db.verify_schema()

        if not is_valid:
            logger.error("X Database schema invalid:")
            for error in errors:
                logger.error(f"  - {error}")
            logger.error("\nRun: python scripts/init_database.py")
            return False

        logger.info("+ Database schema valid")

        # Show current data counts
        counts = db.get_table_counts()
        logger.info(f"  Daily metrics: {counts['daily_metrics']}")
        logger.info(f"  Body metrics: {counts['body_metrics']}")

    except Exception as e:
        logger.error(f"X Database error: {e}")
        return False

    # Check Garmin credentials
    logger.info("\n4. Checking Garmin credentials...")
    try:
        garmin = GarminSync()
        # Try to authenticate (will fail if credentials are wrong)
        logger.info("  + Garmin credentials configured")

    except Exception as e:
        logger.error(f"  X Garmin connection failed: {e}")
        return False

    logger.info("\n" + "=" * 60)
    logger.info("+ Health check passed!")
    logger.info("=" * 60)
    logger.info("\nData storage:")
    logger.info("  - Workouts: Notion (manual annotations)")
    logger.info("  - Daily Metrics: SQL database (analytics)")
    logger.info(f"  - History: {Config.SYNC_LOOKBACK_DAYS} days")
    logger.info("\nNext steps:")
    logger.info("  1. Run 'python orchestrators/sync_health.py' to sync data")
    logger.info("  2. Query metrics using storage.queries or SQL")

    return True


def main():
    """Main sync orchestrator."""
    parser = argparse.ArgumentParser(
        description="Sync health data from Garmin (workouts to Notion, metrics to SQL)"
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
        help="Sync only workouts to Notion",
    )
    parser.add_argument(
        "--metrics-only",
        action="store_true",
        help="Sync only daily metrics to SQL",
    )

    args = parser.parse_args()

    # Health check mode
    if args.health_check:
        success = health_check()
        sys.exit(0 if success else 1)

    # Normal sync mode
    logger.info("=" * 60)
    logger.info("Health & Training Data Sync - Starting")
    logger.info("=" * 60)
    logger.info(f"Workouts: Notion database")
    logger.info(f"Daily Metrics: SQL database ({Config.DATA_DB_PATH})")
    logger.info(f"History: {Config.SYNC_LOOKBACK_DAYS} days")

    if args.dry_run:
        logger.info("! DRY RUN MODE - No changes will be made")

    start_time = time.time()

    try:
        # Initialize clients
        garmin = GarminSync()

        # Determine what to sync
        sync_all = not any([args.workouts_only, args.metrics_only])

        # Sync workouts to Notion
        if sync_all or args.workouts_only:
            state_manager = StateManager()
            notion = NotionSync(state_manager=state_manager)
            workout_stats = sync_workouts(garmin, notion, state_manager, dry_run=args.dry_run)

        # Sync daily metrics to SQL
        if sync_all or args.metrics_only:
            db = Database(Config.DATA_DB_PATH)
            storage = HealthStorage(db)
            metrics_stats = sync_daily_metrics(garmin, storage, dry_run=args.dry_run)

            # Sync body metrics to SQL (if available)
            body_stats = sync_body_metrics(garmin, storage, dry_run=args.dry_run)

        # Summary
        elapsed = time.time() - start_time
        logger.info("\n" + "=" * 60)
        logger.info(f"Health sync complete in {elapsed:.1f}s")
        logger.info("=" * 60)

        if not args.dry_run:
            # Show Notion stats (workouts)
            if sync_all or args.workouts_only:
                logger.info("\nNotion (Workouts):")
                logger.info(f"  Created: {workout_stats.get('created', 0)}")
                logger.info(f"  Updated: {workout_stats.get('updated', 0)}")

            # Show SQL stats (metrics)
            if sync_all or args.metrics_only:
                db = Database(Config.DATA_DB_PATH)
                counts = db.get_table_counts()
                logger.info("\nSQL Database (Metrics):")
                logger.info(f"  Daily metrics: {counts['daily_metrics']} days")
                logger.info(f"  Body metrics: {counts['body_metrics']} entries")

            logger.info("\n+ Data saved successfully")
            logger.info("  - Workouts: Check Notion for manual annotations")
            logger.info("  - Metrics: Query using storage.queries or SQL")

    except Exception as e:
        logger.error(f"\nX Sync failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
