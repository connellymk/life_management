#!/usr/bin/env python3
"""
Health & Training Sync Orchestrator
Syncs Garmin Connect data (workouts, daily metrics, body composition) to Notion
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
from notion.health import NotionSync

logger = setup_logging("health_sync")


def sync_workouts(garmin: GarminSync, notion: NotionSync, state: StateManager, dry_run: bool = False) -> dict:
    """
    Sync workouts from Garmin to Notion.

    Args:
        garmin: Garmin sync client
        notion: Notion sync client
        state: State manager
        dry_run: If True, don't actually create/update pages

    Returns:
        Dictionary with sync stats
    """
    logger.info("=" * 50)
    logger.info("Syncing Workouts...")
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

        logger.info(f"✓ Workout sync complete: {stats['created']} created, {stats['updated']} updated")
        return stats

    except Exception as e:
        logger.error(f"✗ Workout sync failed: {e}")
        duration = time.time() - start_time
        state.update_sync_state("garmin_workouts", success=False, error=str(e))
        state.log_sync("garmin_workouts", "failure", 0, 0, 0, duration, error=str(e))
        return stats


def sync_daily_metrics(garmin: GarminSync, notion: NotionSync, state: StateManager, dry_run: bool = False) -> dict:
    """Sync daily metrics from Garmin to Notion."""
    logger.info("=" * 50)
    logger.info("Syncing Daily Metrics...")
    logger.info("=" * 50)

    start_time = time.time()
    stats = {"fetched": 0, "created": 0, "updated": 0, "errors": 0}

    try:
        # Fetch daily metrics (uses SYNC_LOOKBACK_DAYS from config, defaults to 90 days)
        daily_metrics = garmin.get_daily_metrics()
        stats["fetched"] = len(daily_metrics)

        if not daily_metrics:
            logger.info("No daily metrics found")
            return stats

        logger.info(f"Found {len(daily_metrics)} days of metrics")

        if dry_run:
            logger.info("DRY RUN: Would sync daily metrics")
            return stats

        # Sync each day to Notion
        for metric in daily_metrics:
            external_id = metric.get("external_id")
            existing_page_id = state.get_notion_page_id(external_id)

            try:
                if existing_page_id:
                    result = notion.update_daily_metric(existing_page_id, metric)
                    if result:
                        stats["updated"] += 1
                else:
                    result = notion.create_daily_metric(metric)
                    if result:
                        stats["created"] += 1
            except Exception as e:
                logger.error(f"Error syncing daily metric {external_id}: {e}")
                stats["errors"] += 1

        # Update state
        duration = time.time() - start_time
        state.update_sync_state("garmin_daily", success=True)
        state.log_sync("garmin_daily", "success", stats["created"], stats["updated"], stats["errors"], duration)

        logger.info(f"✓ Daily metrics sync complete: {stats['created']} created, {stats['updated']} updated")
        return stats

    except Exception as e:
        logger.error(f"✗ Daily metrics sync failed: {e}")
        duration = time.time() - start_time
        state.update_sync_state("garmin_daily", success=False, error=str(e))
        state.log_sync("garmin_daily", "failure", 0, 0, 0, duration, error=str(e))
        return stats


def sync_body_metrics(garmin: GarminSync, notion: NotionSync, state: StateManager, dry_run: bool = False) -> dict:
    """Sync body composition from Garmin to Notion."""
    logger.info("=" * 50)
    logger.info("Syncing Body Metrics...")
    logger.info("=" * 50)

    start_time = time.time()
    stats = {"fetched": 0, "created": 0, "updated": 0, "errors": 0}

    try:
        # Fetch body metrics (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        body_metrics = garmin.get_body_composition(start_date, end_date)
        stats["fetched"] = len(body_metrics)

        if not body_metrics:
            logger.info("No body metrics found")
            return stats

        logger.info(f"Found {len(body_metrics)} body composition measurements")

        if dry_run:
            logger.info("DRY RUN: Would sync body metrics")
            return stats

        # Sync each measurement to Notion
        for metric in body_metrics:
            external_id = metric.get("external_id")
            existing_page_id = state.get_notion_page_id(external_id)

            try:
                if existing_page_id:
                    result = notion.update_body_metric(existing_page_id, metric)
                    if result:
                        stats["updated"] += 1
                else:
                    result = notion.create_body_metric(metric)
                    if result:
                        stats["created"] += 1
            except Exception as e:
                logger.error(f"Error syncing body metric {external_id}: {e}")
                stats["errors"] += 1

        # Update state
        duration = time.time() - start_time
        state.update_sync_state("garmin_body", success=True)
        state.log_sync("garmin_body", "success", stats["created"], stats["updated"], stats["errors"], duration)

        logger.info(f"✓ Body metrics sync complete: {stats['created']} created, {stats['updated']} updated")
        return stats

    except Exception as e:
        logger.error(f"✗ Body metrics sync failed: {e}")
        duration = time.time() - start_time
        state.update_sync_state("garmin_body", success=False, error=str(e))
        state.log_sync("garmin_body", "failure", 0, 0, 0, duration, error=str(e))
        return stats


def health_check():
    """Run health check on all components."""
    logger.info("=" * 50)
    logger.info("Health Check")
    logger.info("=" * 50)

    # Check configuration
    logger.info("Checking configuration...")
    is_valid, errors = Config.validate()
    if not is_valid:
        logger.error("✗ Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        return False

    logger.info("✓ Configuration valid")

    # Check Garmin connection
    logger.info("Checking Garmin connection...")
    garmin = GarminSync()
    if not garmin.authenticate():
        logger.error("✗ Garmin authentication failed")
        return False
    logger.info("✓ Garmin connection successful")

    # Check Notion connection
    logger.info("Checking Notion connection...")
    try:
        notion = NotionSync()
        # Try to retrieve each database
        notion.client.databases.retrieve(Config.NOTION_WORKOUTS_DB_ID)
        logger.info("✓ Workouts database accessible")

        notion.client.databases.retrieve(Config.NOTION_DAILY_METRICS_DB_ID)
        logger.info("✓ Daily Metrics database accessible")

        notion.client.databases.retrieve(Config.NOTION_BODY_METRICS_DB_ID)
        logger.info("✓ Body Metrics database accessible")

    except Exception as e:
        logger.error(f"✗ Notion connection failed: {e}")
        return False

    logger.info("=" * 50)
    logger.info("✓ All systems operational")
    logger.info("=" * 50)
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Sync Garmin data to Notion")
    parser.add_argument("--dry-run", action="store_true", help="Preview sync without making changes")
    parser.add_argument("--health-check", action="store_true", help="Run health check")
    parser.add_argument("--workouts-only", action="store_true", help="Sync workouts only")
    parser.add_argument("--daily-only", action="store_true", help="Sync daily metrics only")
    parser.add_argument("--body-only", action="store_true", help="Sync body metrics only")
    args = parser.parse_args()

    logger.info("=" * 50)
    logger.info("Health & Training Sync")
    logger.info("=" * 50)

    # Health check
    if args.health_check:
        success = health_check()
        sys.exit(0 if success else 1)

    # Validate configuration
    is_valid, errors = Config.validate()
    if not is_valid:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)

    logger.info("✓ Configuration valid")

    # Initialize clients
    logger.info("Initializing sync clients...")
    garmin = GarminSync()
    state_manager = StateManager()
    notion = NotionSync(state_manager=state_manager)

    # Authenticate with Garmin
    if not garmin.authenticate():
        logger.error("✗ Failed to authenticate with Garmin")
        sys.exit(1)

    logger.info("✓ Authenticated with Garmin")

    # Run sync
    total_stats = {"workouts": {}, "daily": {}, "body": {}}

    if args.workouts_only:
        total_stats["workouts"] = sync_workouts(garmin, notion, state_manager, args.dry_run)
    elif args.daily_only:
        total_stats["daily"] = sync_daily_metrics(garmin, notion, state_manager, args.dry_run)
    elif args.body_only:
        total_stats["body"] = sync_body_metrics(garmin, notion, state_manager, args.dry_run)
    else:
        # Sync all
        total_stats["workouts"] = sync_workouts(garmin, notion, state_manager, args.dry_run)
        total_stats["daily"] = sync_daily_metrics(garmin, notion, state_manager, args.dry_run)
        total_stats["body"] = sync_body_metrics(garmin, notion, state_manager, args.dry_run)

    # Print summary
    logger.info("=" * 50)
    logger.info("Sync Summary")
    logger.info("=" * 50)

    for sync_type, stats in total_stats.items():
        if stats:
            logger.info(f"{sync_type.capitalize()}:")
            logger.info(f"  Fetched: {stats.get('fetched', 0)}")
            logger.info(f"  Created: {stats.get('created', 0)}")
            logger.info(f"  Updated: {stats.get('updated', 0)}")
            logger.info(f"  Errors: {stats.get('errors', 0)}")

    logger.info("=" * 50)
    logger.info("✓ Sync complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nSync cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
