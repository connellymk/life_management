"""
Tests for the health sync orchestrator (orchestrators/sync_health.py).

Covers:
- sync_workouts: create, update, dry-run, error handling, state updates
- sync_daily_metrics: sync, dry-run, empty data, errors
- sync_body_metrics: sync, dry-run, empty data, errors
- health_check: success and failure paths
- main CLI: argument parsing and orchestration flow
"""

import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch, call

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrators.sync_health import (
    sync_workouts,
    sync_daily_metrics,
    sync_body_metrics,
    health_check,
    main,
)


# =========================================================================
# sync_workouts
# =========================================================================

class TestSyncWorkouts:
    """Tests for the sync_workouts function."""

    def test_creates_new_activities(
        self, mock_garmin, mock_notion_activities, mock_state_manager, sample_activities
    ):
        mock_garmin.get_activities.return_value = sample_activities
        mock_notion_activities.get_activity_by_external_id.return_value = None

        stats = sync_workouts(
            mock_garmin, mock_notion_activities, mock_state_manager
        )

        assert stats["fetched"] == 2
        assert stats["created"] == 2
        assert stats["updated"] == 0
        assert stats["errors"] == 0
        assert mock_notion_activities.create_activity.call_count == 2

    def test_updates_existing_activities(
        self, mock_garmin, mock_notion_activities, mock_state_manager, sample_activities
    ):
        mock_garmin.get_activities.return_value = sample_activities
        mock_notion_activities.get_activity_by_external_id.return_value = {
            "id": "existing-page-id"
        }

        stats = sync_workouts(
            mock_garmin, mock_notion_activities, mock_state_manager
        )

        assert stats["fetched"] == 2
        assert stats["created"] == 0
        assert stats["updated"] == 2
        assert mock_notion_activities.update_activity.call_count == 2

    def test_mix_of_create_and_update(
        self, mock_garmin, mock_notion_activities, mock_state_manager, sample_activities
    ):
        mock_garmin.get_activities.return_value = sample_activities
        # First activity exists, second is new
        mock_notion_activities.get_activity_by_external_id.side_effect = [
            {"id": "existing-page-id"},
            None,
        ]

        stats = sync_workouts(
            mock_garmin, mock_notion_activities, mock_state_manager
        )

        assert stats["created"] == 1
        assert stats["updated"] == 1

    def test_no_activities_found(
        self, mock_garmin, mock_notion_activities, mock_state_manager
    ):
        mock_garmin.get_activities.return_value = []

        stats = sync_workouts(
            mock_garmin, mock_notion_activities, mock_state_manager
        )

        assert stats["fetched"] == 0
        assert stats["created"] == 0
        assert stats["updated"] == 0
        mock_notion_activities.create_activity.assert_not_called()

    def test_dry_run_does_not_sync(
        self, mock_garmin, mock_notion_activities, mock_state_manager, sample_activities
    ):
        mock_garmin.get_activities.return_value = sample_activities

        stats = sync_workouts(
            mock_garmin, mock_notion_activities, mock_state_manager, dry_run=True
        )

        assert stats["fetched"] == 2
        assert stats["created"] == 0
        mock_notion_activities.create_activity.assert_not_called()
        mock_notion_activities.update_activity.assert_not_called()

    def test_passes_date_range_to_garmin(
        self, mock_garmin, mock_notion_activities, mock_state_manager
    ):
        mock_garmin.get_activities.return_value = []
        start = datetime(2026, 1, 1)
        end = datetime(2026, 1, 31)

        sync_workouts(
            mock_garmin, mock_notion_activities, mock_state_manager,
            start_date=start, end_date=end,
        )

        mock_garmin.get_activities.assert_called_once_with(
            start_date=start, end_date=end
        )

    def test_individual_activity_error_does_not_abort(
        self, mock_garmin, mock_notion_activities, mock_state_manager, sample_activities
    ):
        mock_garmin.get_activities.return_value = sample_activities
        mock_notion_activities.get_activity_by_external_id.return_value = None
        # First create succeeds, second raises
        mock_notion_activities.create_activity.side_effect = [
            {"id": "page-1"},
            Exception("Notion API error"),
        ]

        stats = sync_workouts(
            mock_garmin, mock_notion_activities, mock_state_manager
        )

        assert stats["created"] == 1
        assert stats["errors"] == 1

    def test_updates_state_on_success(
        self, mock_garmin, mock_notion_activities, mock_state_manager, sample_activities
    ):
        mock_garmin.get_activities.return_value = sample_activities
        mock_notion_activities.get_activity_by_external_id.return_value = None

        sync_workouts(mock_garmin, mock_notion_activities, mock_state_manager)

        mock_state_manager.update_sync_state.assert_called_once_with(
            "garmin_workouts", success=True
        )
        mock_state_manager.log_sync.assert_called_once()
        log_args = mock_state_manager.log_sync.call_args
        assert log_args[0][0] == "garmin_workouts"
        assert log_args[0][1] == "success"

    def test_updates_state_on_fetch_failure(
        self, mock_garmin, mock_notion_activities, mock_state_manager
    ):
        mock_garmin.get_activities.side_effect = Exception("Garmin API down")

        stats = sync_workouts(
            mock_garmin, mock_notion_activities, mock_state_manager
        )

        mock_state_manager.update_sync_state.assert_called_once()
        args, kwargs = mock_state_manager.update_sync_state.call_args
        assert args[0] == "garmin_workouts"
        assert kwargs["success"] is False
        assert "Garmin API down" in kwargs["error"]


# =========================================================================
# sync_daily_metrics
# =========================================================================

class TestSyncDailyMetrics:
    """Tests for the sync_daily_metrics function."""

    def test_syncs_all_metrics(
        self, mock_garmin, mock_notion_tracking, sample_daily_metrics
    ):
        mock_garmin.get_daily_metrics.return_value = sample_daily_metrics

        stats = sync_daily_metrics(mock_garmin, mock_notion_tracking)

        assert stats["fetched"] == 2
        assert stats["synced"] == 2
        assert stats["errors"] == 0
        assert mock_notion_tracking.sync_daily_metrics.call_count == 2

    def test_no_metrics_found(self, mock_garmin, mock_notion_tracking):
        mock_garmin.get_daily_metrics.return_value = []

        stats = sync_daily_metrics(mock_garmin, mock_notion_tracking)

        assert stats["fetched"] == 0
        assert stats["synced"] == 0
        mock_notion_tracking.sync_daily_metrics.assert_not_called()

    def test_dry_run_does_not_sync(
        self, mock_garmin, mock_notion_tracking, sample_daily_metrics
    ):
        mock_garmin.get_daily_metrics.return_value = sample_daily_metrics

        stats = sync_daily_metrics(
            mock_garmin, mock_notion_tracking, dry_run=True
        )

        assert stats["fetched"] == 2
        assert stats["synced"] == 0
        mock_notion_tracking.sync_daily_metrics.assert_not_called()

    def test_passes_date_range(self, mock_garmin, mock_notion_tracking):
        mock_garmin.get_daily_metrics.return_value = []
        start = datetime(2026, 1, 1)
        end = datetime(2026, 1, 31)

        sync_daily_metrics(
            mock_garmin, mock_notion_tracking,
            start_date=start, end_date=end,
        )

        mock_garmin.get_daily_metrics.assert_called_once_with(
            start_date=start, end_date=end
        )

    def test_individual_metric_error_does_not_abort(
        self, mock_garmin, mock_notion_tracking, sample_daily_metrics
    ):
        mock_garmin.get_daily_metrics.return_value = sample_daily_metrics
        mock_notion_tracking.sync_daily_metrics.side_effect = [
            {"id": "page-1"},
            Exception("Notion error"),
        ]

        stats = sync_daily_metrics(mock_garmin, mock_notion_tracking)

        assert stats["synced"] == 1
        assert stats["errors"] == 1

    def test_sync_returns_none_not_counted(
        self, mock_garmin, mock_notion_tracking, sample_daily_metrics
    ):
        mock_garmin.get_daily_metrics.return_value = sample_daily_metrics
        mock_notion_tracking.sync_daily_metrics.return_value = None

        stats = sync_daily_metrics(mock_garmin, mock_notion_tracking)

        assert stats["fetched"] == 2
        assert stats["synced"] == 0

    def test_garmin_fetch_failure(self, mock_garmin, mock_notion_tracking):
        mock_garmin.get_daily_metrics.side_effect = Exception("Connection error")

        stats = sync_daily_metrics(mock_garmin, mock_notion_tracking)

        assert stats["errors"] == 1
        mock_notion_tracking.sync_daily_metrics.assert_not_called()


# =========================================================================
# sync_body_metrics
# =========================================================================

class TestSyncBodyMetrics:
    """Tests for the sync_body_metrics function."""

    def test_syncs_all_body_metrics(
        self, mock_garmin, mock_notion_tracking, sample_body_metrics
    ):
        mock_garmin.get_body_composition.return_value = sample_body_metrics

        stats = sync_body_metrics(mock_garmin, mock_notion_tracking)

        assert stats["fetched"] == 2
        assert stats["synced"] == 2
        assert stats["errors"] == 0
        assert mock_notion_tracking.sync_body_metrics.call_count == 2

    def test_no_body_metrics_found(self, mock_garmin, mock_notion_tracking):
        mock_garmin.get_body_composition.return_value = []

        stats = sync_body_metrics(mock_garmin, mock_notion_tracking)

        assert stats["fetched"] == 0
        assert stats["synced"] == 0

    def test_dry_run_does_not_sync(
        self, mock_garmin, mock_notion_tracking, sample_body_metrics
    ):
        mock_garmin.get_body_composition.return_value = sample_body_metrics

        stats = sync_body_metrics(
            mock_garmin, mock_notion_tracking, dry_run=True
        )

        assert stats["fetched"] == 2
        assert stats["synced"] == 0
        mock_notion_tracking.sync_body_metrics.assert_not_called()

    def test_passes_date_range(self, mock_garmin, mock_notion_tracking):
        mock_garmin.get_body_composition.return_value = []
        start = datetime(2026, 1, 1)
        end = datetime(2026, 1, 31)

        sync_body_metrics(
            mock_garmin, mock_notion_tracking,
            start_date=start, end_date=end,
        )

        mock_garmin.get_body_composition.assert_called_once_with(
            start_date=start, end_date=end
        )

    def test_individual_metric_error_does_not_abort(
        self, mock_garmin, mock_notion_tracking, sample_body_metrics
    ):
        mock_garmin.get_body_composition.return_value = sample_body_metrics
        mock_notion_tracking.sync_body_metrics.side_effect = [
            {"id": "page-1"},
            Exception("Notion error"),
        ]

        stats = sync_body_metrics(mock_garmin, mock_notion_tracking)

        assert stats["synced"] == 1
        assert stats["errors"] == 1

    def test_garmin_fetch_failure(self, mock_garmin, mock_notion_tracking):
        mock_garmin.get_body_composition.side_effect = Exception("Timeout")

        stats = sync_body_metrics(mock_garmin, mock_notion_tracking)

        assert stats["errors"] == 1


# =========================================================================
# health_check
# =========================================================================

class TestHealthCheck:
    """Tests for the health_check function."""

    @patch("orchestrators.sync_health.GarminSync")
    @patch("orchestrators.sync_health.NotionDailyTrackingSync")
    @patch("orchestrators.sync_health.NotionActivitiesSync")
    @patch("orchestrators.sync_health.Config")
    def test_health_check_passes(
        self, mock_config, mock_activities_cls, mock_tracking_cls, mock_garmin_cls
    ):
        mock_config.validate.return_value = (True, [])
        mock_config.NOTION_WORKOUTS_DB_ID = "db-1"
        mock_config.NOTION_DAILY_TRACKING_DB_ID = "db-2"
        mock_config.SYNC_LOOKBACK_DAYS = 90

        mock_garmin_instance = MagicMock()
        mock_garmin_instance.authenticate.return_value = True
        mock_garmin_cls.return_value = mock_garmin_instance

        result = health_check()

        assert result is True

    @patch("orchestrators.sync_health.Config")
    def test_health_check_fails_on_invalid_config(self, mock_config):
        mock_config.validate.return_value = (False, ["GARMIN_EMAIL not set"])

        result = health_check()

        assert result is False

    @patch("orchestrators.sync_health.NotionActivitiesSync")
    @patch("orchestrators.sync_health.Config")
    def test_health_check_fails_on_notion_error(
        self, mock_config, mock_activities_cls
    ):
        mock_config.validate.return_value = (True, [])
        mock_activities_cls.side_effect = Exception("Notion connection failed")

        result = health_check()

        assert result is False

    @patch("orchestrators.sync_health.GarminSync")
    @patch("orchestrators.sync_health.NotionDailyTrackingSync")
    @patch("orchestrators.sync_health.NotionActivitiesSync")
    @patch("orchestrators.sync_health.Config")
    def test_health_check_fails_on_garmin_auth_failure(
        self, mock_config, mock_activities_cls, mock_tracking_cls, mock_garmin_cls
    ):
        mock_config.validate.return_value = (True, [])
        mock_config.NOTION_WORKOUTS_DB_ID = "db-1"
        mock_config.NOTION_DAILY_TRACKING_DB_ID = "db-2"

        mock_garmin_instance = MagicMock()
        mock_garmin_instance.authenticate.return_value = False
        mock_garmin_cls.return_value = mock_garmin_instance

        result = health_check()

        assert result is False


# =========================================================================
# main (CLI entrypoint)
# =========================================================================

class TestMain:
    """Tests for the main CLI orchestrator."""

    @patch("orchestrators.sync_health.StateManager")
    @patch("orchestrators.sync_health.NotionActivitiesSync")
    @patch("orchestrators.sync_health.NotionDailyTrackingSync")
    @patch("orchestrators.sync_health.GarminSync")
    @patch("orchestrators.sync_health.Config")
    def test_full_sync_runs_all_three(
        self, mock_config, mock_garmin_cls, mock_tracking_cls,
        mock_activities_cls, mock_state_cls
    ):
        mock_config.validate.return_value = (True, [])
        mock_config.SYNC_LOOKBACK_DAYS = 90

        mock_garmin = MagicMock()
        mock_garmin.get_activities.return_value = []
        mock_garmin.get_daily_metrics.return_value = []
        mock_garmin.get_body_composition.return_value = []
        mock_garmin_cls.return_value = mock_garmin

        with patch("sys.argv", ["sync_health.py"]):
            main()

        mock_garmin.get_activities.assert_called_once()
        mock_garmin.get_daily_metrics.assert_called_once()
        mock_garmin.get_body_composition.assert_called_once()

    @patch("orchestrators.sync_health.StateManager")
    @patch("orchestrators.sync_health.NotionActivitiesSync")
    @patch("orchestrators.sync_health.NotionDailyTrackingSync")
    @patch("orchestrators.sync_health.GarminSync")
    @patch("orchestrators.sync_health.Config")
    def test_workouts_only_flag(
        self, mock_config, mock_garmin_cls, mock_tracking_cls,
        mock_activities_cls, mock_state_cls
    ):
        mock_config.validate.return_value = (True, [])
        mock_config.SYNC_LOOKBACK_DAYS = 90

        mock_garmin = MagicMock()
        mock_garmin.get_activities.return_value = []
        mock_garmin_cls.return_value = mock_garmin

        with patch("sys.argv", ["sync_health.py", "--workouts-only"]):
            main()

        mock_garmin.get_activities.assert_called_once()
        mock_garmin.get_daily_metrics.assert_not_called()
        mock_garmin.get_body_composition.assert_not_called()

    @patch("orchestrators.sync_health.StateManager")
    @patch("orchestrators.sync_health.NotionActivitiesSync")
    @patch("orchestrators.sync_health.NotionDailyTrackingSync")
    @patch("orchestrators.sync_health.GarminSync")
    @patch("orchestrators.sync_health.Config")
    def test_metrics_only_flag(
        self, mock_config, mock_garmin_cls, mock_tracking_cls,
        mock_activities_cls, mock_state_cls
    ):
        mock_config.validate.return_value = (True, [])
        mock_config.SYNC_LOOKBACK_DAYS = 90

        mock_garmin = MagicMock()
        mock_garmin.get_daily_metrics.return_value = []
        mock_garmin_cls.return_value = mock_garmin

        with patch("sys.argv", ["sync_health.py", "--metrics-only"]):
            main()

        mock_garmin.get_activities.assert_not_called()
        mock_garmin.get_daily_metrics.assert_called_once()
        mock_garmin.get_body_composition.assert_not_called()

    @patch("orchestrators.sync_health.StateManager")
    @patch("orchestrators.sync_health.NotionActivitiesSync")
    @patch("orchestrators.sync_health.NotionDailyTrackingSync")
    @patch("orchestrators.sync_health.GarminSync")
    @patch("orchestrators.sync_health.Config")
    def test_body_only_flag(
        self, mock_config, mock_garmin_cls, mock_tracking_cls,
        mock_activities_cls, mock_state_cls
    ):
        mock_config.validate.return_value = (True, [])
        mock_config.SYNC_LOOKBACK_DAYS = 90

        mock_garmin = MagicMock()
        mock_garmin.get_body_composition.return_value = []
        mock_garmin_cls.return_value = mock_garmin

        with patch("sys.argv", ["sync_health.py", "--body-only"]):
            main()

        mock_garmin.get_activities.assert_not_called()
        mock_garmin.get_daily_metrics.assert_not_called()
        mock_garmin.get_body_composition.assert_called_once()

    @patch("orchestrators.sync_health.StateManager")
    @patch("orchestrators.sync_health.NotionActivitiesSync")
    @patch("orchestrators.sync_health.NotionDailyTrackingSync")
    @patch("orchestrators.sync_health.GarminSync")
    @patch("orchestrators.sync_health.Config")
    def test_date_range_passed_through(
        self, mock_config, mock_garmin_cls, mock_tracking_cls,
        mock_activities_cls, mock_state_cls
    ):
        mock_config.validate.return_value = (True, [])
        mock_config.SYNC_LOOKBACK_DAYS = 90

        mock_garmin = MagicMock()
        mock_garmin.get_activities.return_value = []
        mock_garmin.get_daily_metrics.return_value = []
        mock_garmin.get_body_composition.return_value = []
        mock_garmin_cls.return_value = mock_garmin

        with patch("sys.argv", [
            "sync_health.py",
            "--start-date", "2026-01-01",
            "--end-date", "2026-01-31",
        ]):
            main()

        # Verify date args were parsed and forwarded
        call_kwargs = mock_garmin.get_activities.call_args
        assert call_kwargs[1]["start_date"] == datetime(2026, 1, 1)
        assert call_kwargs[1]["end_date"] == datetime(2026, 1, 31)

    @patch("orchestrators.sync_health.health_check")
    def test_health_check_flag(self, mock_hc):
        mock_hc.return_value = True

        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["sync_health.py", "--health-check"]):
                main()

        assert exc_info.value.code == 0
        mock_hc.assert_called_once()

    @patch("orchestrators.sync_health.health_check")
    def test_health_check_flag_failure_exits_1(self, mock_hc):
        mock_hc.return_value = False

        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["sync_health.py", "--health-check"]):
                main()

        assert exc_info.value.code == 1
