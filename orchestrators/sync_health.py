#!/usr/bin/env python3
"""
Health & Training Sync Orchestrator
Syncs Garmin Connect data to Airtable and SQL:

- Training Sessions → Airtable (workouts with Day/Week links for rollups)
- Health Metrics → Airtable (daily health data with Day links)
- Body Metrics → Airtable (weight/composition with Day links)
- Historical Data (>90 days) → SQL database (optional archival)

Note: Currently still uses Notion code. Migration to Airtable in progress.
See MIGRATION_NOTES.md for refactoring tasks.
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
from airtable.health import AirtableTrainingSessionsSync, AirtableHealthMetricsSync, AirtableBodyMetricsSync
from airtable.base_client import AirtableClient

logger = setup_logging("health_sync")


def sync_workouts(garmin: GarminSync, airtable_sync: AirtableTrainingSessionsSync, state: StateManager, dry_run: bool = False, start_date: datetime = None, end_date: datetime = None) -> dict:
    """
    Sync workouts from Garmin to Airtable Training Sessions table.

    Args:
        garmin: Garmin sync client
        airtable_sync: Airtable training sessions sync client
        state: State manager
        dry_run: If True, don't actually create/update records

    Returns:
        Dictionary with sync stats
    """
    logger.info("=" * 50)
    logger.info("Syncing Workouts to Airtable...")
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

        # Sync each activity to Airtable
        for activity in activities:
            external_id = activity.get("external_id")

            try:
                # Map Garmin activity to Airtable format
                session_data = {
                    'Activity ID': external_id,
                    'Activity Name': activity.get('title'),
                    'Activity Type': activity.get('activity_type'),
                    'Start Time': activity.get('start_time'),
                    'Distance': activity.get('distance'),
                    'Calories': activity.get('calories'),
                    'Average HR': activity.get('avg_heart_rate'),
                    'Max HR': activity.get('max_heart_rate'),
                    'Elevation Gain': activity.get('elevation'),
                    'Garmin URL': activity.get('garmin_url'),
                }

                # Add duration in seconds (convert from minutes)
                if activity.get('duration_minutes'):
                    session_data['Duration'] = int(activity.get('duration_minutes') * 60)

                # Add pace and speed
                if activity.get('pace'):
                    # Keep pace as string in MM:SS format for Airtable
                    session_data['Average Pace'] = str(activity.get('pace'))

                if activity.get('speed'):
                    session_data['Average Speed'] = activity.get('speed')

                # Sync to Airtable (create or update)
                result = airtable_sync.sync_session(session_data)

                if result:
                    # Check if it was a new record or update
                    existing = airtable_sync.get_session_by_activity_id(external_id)
                    if existing and existing['id'] == result['id']:
                        stats["updated"] += 1
                    else:
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


def sync_daily_metrics(garmin: GarminSync, airtable_sync: AirtableHealthMetricsSync, storage: HealthStorage = None, dry_run: bool = False, start_date: datetime = None, end_date: datetime = None) -> dict:
    """
    Sync daily metrics from Garmin to Airtable Health Metrics table.
    Optionally also save to SQL for historical archival.

    Args:
        garmin: Garmin sync client
        airtable_sync: Airtable health metrics sync client
        storage: Optional SQL storage for archival (HealthStorage)
        dry_run: If True, don't actually save data

    Returns:
        Dictionary with sync stats
    """
    logger.info("=" * 50)
    logger.info("Syncing Daily Metrics to Airtable...")
    logger.info("=" * 50)

    start_time = time.time()
    stats = {"fetched": 0, "synced": 0, "sql_saved": 0, "errors": 0}

    try:
        # Fetch daily metrics (uses SYNC_LOOKBACK_DAYS from config, defaults to 90 days)
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

        # Sync each day to Airtable
        for metric in daily_metrics:
            try:
                # Parse date string to datetime
                metric_date = datetime.fromisoformat(metric.get('date'))

                # Map Garmin metrics to Airtable format
                airtable_data = {
                    'Date': metric_date,
                    'Steps': metric.get('steps'),
                    'Floors Climbed': metric.get('floors_climbed'),
                    'Active Calories': metric.get('active_calories'),
                    'Total Calories': metric.get('total_calories'),
                    'Resting HR': metric.get('avg_hr'),
                    'Stress Level': metric.get('avg_stress'),
                    'Body Battery': metric.get('body_battery_max'),
                }

                # Add sleep data (convert hours to seconds for Duration field)
                if metric.get('sleep_hours'):
                    airtable_data['Sleep Duration'] = int(metric.get('sleep_hours') * 3600)

                # Add sleep score if available
                if metric.get('sleep_score'):
                    airtable_data['Sleep Score'] = metric.get('sleep_score')

                # Add intensity minutes if available
                if metric.get('moderate_intensity_minutes'):
                    airtable_data['Moderate Intensity Minutes'] = metric.get('moderate_intensity_minutes')
                if metric.get('vigorous_intensity_minutes'):
                    airtable_data['Vigorous Intensity Minutes'] = metric.get('vigorous_intensity_minutes')

                # Calculate total intensity minutes
                moderate = metric.get('moderate_intensity_minutes') or 0
                vigorous = metric.get('vigorous_intensity_minutes') or 0
                if moderate or vigorous:
                    airtable_data['Intensity Minutes'] = moderate + vigorous

                # Sync to Airtable (create or update)
                result = airtable_sync.create_or_update_metrics(airtable_data)
                if result:
                    stats["synced"] += 1

                # Also save to SQL if storage provided (for historical archival)
                if storage:
                    if storage.save_daily_metric(metric):
                        stats["sql_saved"] += 1

            except Exception as e:
                logger.error(f"Error syncing daily metric for {metric.get('date')}: {e}")
                stats["errors"] += 1

        elapsed = time.time() - start_time
        logger.info(f"Daily metrics sync complete in {elapsed:.1f}s")
        logger.info(f"  Fetched: {stats['fetched']}, Synced to Airtable: {stats['synced']}, SQL: {stats['sql_saved']}, Errors: {stats['errors']}")

        return stats

    except Exception as e:
        logger.error(f"X Daily metrics sync failed: {e}")
        stats["errors"] += 1
        return stats


def sync_body_metrics(garmin: GarminSync, airtable_sync: AirtableBodyMetricsSync, storage: HealthStorage = None, dry_run: bool = False, start_date: datetime = None, end_date: datetime = None) -> dict:
    """
    Sync body composition metrics from Garmin to Airtable Body Metrics table.
    Optionally also save to SQL for historical archival.

    Args:
        garmin: Garmin sync client
        airtable_sync: Airtable body metrics sync client
        storage: Optional SQL storage for archival (HealthStorage)
        dry_run: If True, don't actually save data

    Returns:
        Dictionary with sync stats
    """
    logger.info("=" * 50)
    logger.info("Syncing Body Metrics to Airtable...")
    logger.info("=" * 50)

    start_time = time.time()
    stats = {"fetched": 0, "synced": 0, "sql_saved": 0, "errors": 0}

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
            return stats

        # Sync each entry to Airtable
        for metric in body_metrics:
            try:
                # Parse date string to datetime
                metric_date = datetime.fromisoformat(metric.get('date'))

                # Map Garmin metrics to Airtable format
                airtable_data = {
                    'Date': metric_date,
                    'Time': metric_date,  # Use date as time if no specific time available
                    'Weight': metric.get('weight'),
                }

                # Add optional body composition fields
                if metric.get('bmi'):
                    airtable_data['BMI'] = metric.get('bmi')
                if metric.get('body_fat_percent'):
                    airtable_data['Body Fat %'] = metric.get('body_fat_percent')
                if metric.get('muscle_mass'):
                    airtable_data['Muscle Mass'] = metric.get('muscle_mass')
                if metric.get('bone_mass'):
                    airtable_data['Bone Mass'] = metric.get('bone_mass')
                if metric.get('body_water_percent'):
                    airtable_data['Body Water %'] = metric.get('body_water_percent')

                # Create measurement in Airtable
                result = airtable_sync.create_measurement(airtable_data)
                if result:
                    stats["synced"] += 1

                # Also save to SQL if storage provided (for historical archival)
                if storage:
                    if storage.save_body_metric(metric):
                        stats["sql_saved"] += 1

            except Exception as e:
                logger.error(f"Error syncing body metric: {e}")
                stats["errors"] += 1

        elapsed = time.time() - start_time
        logger.info(f"Body metrics sync complete in {elapsed:.1f}s")
        logger.info(f"  Fetched: {stats['fetched']}, Synced to Airtable: {stats['synced']}, SQL: {stats['sql_saved']}, Errors: {stats['errors']}")

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
    logger.info("\n1. Checking Airtable configuration...")
    from core.config import AirtableConfig
    is_valid, errors = AirtableConfig.validate()

    if not is_valid:
        logger.error("X Airtable configuration not valid:")
        for error in errors:
            logger.error(f"  - {error}")
        return False

    logger.info("+ Airtable configuration valid")

    # Check Airtable connection
    logger.info("\n2. Checking Airtable connection...")
    try:
        client = AirtableClient()
        # Try to get the tables to verify connection
        training_table = client.get_training_sessions_table()
        health_table = client.get_health_metrics_table()
        body_table = client.get_body_metrics_table()
        logger.info("  + Training Sessions table accessible")
        logger.info("  + Health Metrics table accessible")
        logger.info("  + Body Metrics table accessible")

    except Exception as e:
        logger.error(f"  X Airtable connection failed: {e}")
        return False

    # Check SQL database (optional, for historical archival)
    logger.info("\n3. Checking SQL database (optional, for archival)...")
    try:
        db = Database(Config.DATA_DB_PATH)
        is_valid, errors = db.verify_schema()

        if not is_valid:
            logger.warning("! Database schema invalid (optional for archival):")
            for error in errors:
                logger.warning(f"  - {error}")
            logger.warning("\nTo enable archival, run: python scripts/init_database.py")
        else:
            logger.info("+ Database schema valid")

            # Show current data counts
            counts = db.get_table_counts()
            logger.info(f"  Daily metrics: {counts['daily_metrics']}")
            logger.info(f"  Body metrics: {counts['body_metrics']}")

    except Exception as e:
        logger.warning(f"! Database not available (optional for archival): {e}")

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
    logger.info("  - Training Sessions: Airtable (with Day/Week links)")
    logger.info("  - Health Metrics: Airtable (with Day links)")
    logger.info("  - Body Metrics: Airtable (with Day links)")
    logger.info(f"  - History: {Config.SYNC_LOOKBACK_DAYS} days")
    logger.info("  - SQL archival: Optional (for >90 days)")
    logger.info("\nNext steps:")
    logger.info("  1. Run 'python orchestrators/sync_health.py' to sync data")
    logger.info("  2. View data in Airtable base")

    return True


def main():
    """Main sync orchestrator."""
    parser = argparse.ArgumentParser(
        description="Sync health data from Garmin to Airtable"
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
        help="Sync only workouts to Airtable Training Sessions",
    )
    parser.add_argument(
        "--metrics-only",
        action="store_true",
        help="Sync only daily metrics to Airtable Health Metrics",
    )
    parser.add_argument(
        "--body-only",
        action="store_true",
        help="Sync only body metrics to Airtable Body Metrics",
    )
    parser.add_argument(
        "--archive-to-sql",
        action="store_true",
        help="Also archive data to SQL database for historical analysis",
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
    logger.info(f"Training Sessions: Airtable (with Day/Week links)")
    logger.info(f"Health Metrics: Airtable (with Day links)")
    logger.info(f"Body Metrics: Airtable (with Day links)")

    if sync_start_date or sync_end_date:
        start_str = sync_start_date.strftime("%Y-%m-%d") if sync_start_date else "default"
        end_str = sync_end_date.strftime("%Y-%m-%d") if sync_end_date else "default"
        logger.info(f"Date Range: {start_str} to {end_str}")
    else:
        logger.info(f"History: {Config.SYNC_LOOKBACK_DAYS} days")

    if args.archive_to_sql:
        logger.info(f"SQL Archival: Enabled ({Config.DATA_DB_PATH})")

    if args.dry_run:
        logger.info("! DRY RUN MODE - No changes will be made")

    start_time = time.time()

    try:
        # Initialize clients
        garmin = GarminSync()
        airtable_client = AirtableClient()

        # Determine what to sync
        sync_all = not any([args.workouts_only, args.metrics_only, args.body_only])

        # Initialize SQL storage if archival is enabled
        sql_storage = None
        if args.archive_to_sql:
            db = Database(Config.DATA_DB_PATH)
            sql_storage = HealthStorage(db)

        # Sync workouts to Airtable
        workout_stats = {}
        if sync_all or args.workouts_only:
            state_manager = StateManager()
            airtable_sessions = AirtableTrainingSessionsSync(airtable_client)
            workout_stats = sync_workouts(garmin, airtable_sessions, state_manager, dry_run=args.dry_run, start_date=sync_start_date, end_date=sync_end_date)

        # Sync daily metrics to Airtable
        metrics_stats = {}
        if sync_all or args.metrics_only:
            airtable_health = AirtableHealthMetricsSync(airtable_client)
            metrics_stats = sync_daily_metrics(garmin, airtable_health, storage=sql_storage, dry_run=args.dry_run, start_date=sync_start_date, end_date=sync_end_date)

        # Sync body metrics to Airtable
        body_stats = {}
        if sync_all or args.body_only:
            airtable_body = AirtableBodyMetricsSync(airtable_client)
            body_stats = sync_body_metrics(garmin, airtable_body, storage=sql_storage, dry_run=args.dry_run, start_date=sync_start_date, end_date=sync_end_date)

        # Summary
        elapsed = time.time() - start_time
        logger.info("\n" + "=" * 60)
        logger.info(f"Health sync complete in {elapsed:.1f}s")
        logger.info("=" * 60)

        if not args.dry_run:
            # Show Airtable stats
            if sync_all or args.workouts_only:
                logger.info("\nAirtable Training Sessions:")
                logger.info(f"  Created: {workout_stats.get('created', 0)}")
                logger.info(f"  Updated: {workout_stats.get('updated', 0)}")

            if sync_all or args.metrics_only:
                logger.info("\nAirtable Health Metrics:")
                logger.info(f"  Synced: {metrics_stats.get('synced', 0)}")

            if sync_all or args.body_only:
                logger.info("\nAirtable Body Metrics:")
                logger.info(f"  Synced: {body_stats.get('synced', 0)}")

            # Show SQL stats if archival enabled
            if args.archive_to_sql and sql_storage:
                db = Database(Config.DATA_DB_PATH)
                counts = db.get_table_counts()
                logger.info("\nSQL Database (Archival):")
                logger.info(f"  Daily metrics: {counts['daily_metrics']} days")
                logger.info(f"  Body metrics: {counts['body_metrics']} entries")

            logger.info("\n+ Data synced successfully")
            logger.info("  - View in Airtable base")
            logger.info("  - Data linked to Day/Week tables for rollups")

    except Exception as e:
        logger.error(f"\nX Sync failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
