"""
Tests for the calendar sync orchestrator (orchestrators/sync_calendar.py).

Covers:
- sync_google_calendars: single/multi calendar, dry-run, errors, auth failure
- print_sync_summary: all output branches
- main CLI: argument parsing, health-check, date range, error flows
"""

import sys
from io import StringIO
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrators.sync_calendar import (
    sync_google_calendars,
    print_sync_summary,
    main,
)


# =========================================================================
# sync_google_calendars
# =========================================================================

class TestSyncGoogleCalendars:
    """Tests for the sync_google_calendars function."""

    @patch("orchestrators.sync_calendar.GoogleCalendarSync")
    @patch("orchestrators.sync_calendar.Config")
    def test_syncs_single_calendar(
        self, mock_config, mock_google_cls,
        mock_notion_calendar, mock_state_manager, sample_calendar_sync_stats,
    ):
        mock_config.GOOGLE_CALENDAR_IDS = ["primary"]
        mock_config.GOOGLE_CALENDAR_NAMES = ["Personal"]

        mock_google = MagicMock()
        mock_google.authenticate.return_value = True
        mock_google.sync_calendar_to_notion.return_value = sample_calendar_sync_stats
        mock_google_cls.return_value = mock_google

        stats = sync_google_calendars(mock_notion_calendar, mock_state_manager)

        assert stats["success"] is True
        assert stats["calendars_synced"] == 1
        assert stats["total_events_fetched"] == 5
        assert stats["total_events_created"] == 3
        assert stats["total_events_updated"] == 2
        assert stats["total_errors"] == 0
        assert len(stats["calendar_details"]) == 1

    @patch("orchestrators.sync_calendar.GoogleCalendarSync")
    @patch("orchestrators.sync_calendar.Config")
    def test_syncs_multiple_calendars(
        self, mock_config, mock_google_cls,
        mock_notion_calendar, mock_state_manager, sample_calendar_sync_stats,
    ):
        mock_config.GOOGLE_CALENDAR_IDS = ["primary", "work@group.calendar.google.com"]
        mock_config.GOOGLE_CALENDAR_NAMES = ["Personal", "Work"]

        work_stats = dict(sample_calendar_sync_stats)
        work_stats["calendar_name"] = "Work"
        work_stats["events_fetched"] = 10
        work_stats["events_created"] = 8
        work_stats["events_updated"] = 1
        work_stats["events_deleted"] = 1

        mock_google = MagicMock()
        mock_google.authenticate.return_value = True
        mock_google.sync_calendar_to_notion.side_effect = [
            sample_calendar_sync_stats,
            work_stats,
        ]
        mock_google_cls.return_value = mock_google

        stats = sync_google_calendars(mock_notion_calendar, mock_state_manager)

        assert stats["calendars_synced"] == 2
        assert stats["total_events_fetched"] == 15
        assert stats["total_events_created"] == 11
        assert stats["total_events_deleted"] == 1
        assert len(stats["calendar_details"]) == 2

    @patch("orchestrators.sync_calendar.GoogleCalendarSync")
    @patch("orchestrators.sync_calendar.Config")
    def test_auth_failure_returns_error(
        self, mock_config, mock_google_cls,
        mock_notion_calendar, mock_state_manager,
    ):
        mock_config.GOOGLE_CALENDAR_IDS = ["primary"]
        mock_config.GOOGLE_CALENDAR_NAMES = ["Personal"]

        mock_google = MagicMock()
        mock_google.authenticate.return_value = False
        mock_google_cls.return_value = mock_google

        stats = sync_google_calendars(mock_notion_calendar, mock_state_manager)

        assert stats["success"] is False
        assert "Authentication failed" in stats.get("error", "")

    @patch("orchestrators.sync_calendar.GoogleCalendarSync")
    @patch("orchestrators.sync_calendar.Config")
    def test_dry_run_forwarded(
        self, mock_config, mock_google_cls,
        mock_notion_calendar, mock_state_manager,
    ):
        mock_config.GOOGLE_CALENDAR_IDS = ["primary"]
        mock_config.GOOGLE_CALENDAR_NAMES = ["Personal"]

        mock_google = MagicMock()
        mock_google.authenticate.return_value = True
        mock_google.sync_calendar_to_notion.return_value = {
            "calendar_name": "Personal",
            "events_fetched": 3,
            "events_created": 0,
            "events_updated": 0,
            "events_deleted": 0,
            "events_skipped": 0,
            "errors": 0,
            "incremental": False,
            "new_sync_token": None,
        }
        mock_google_cls.return_value = mock_google

        sync_google_calendars(
            mock_notion_calendar, mock_state_manager, dry_run=True
        )

        _, kwargs = mock_google.sync_calendar_to_notion.call_args
        assert kwargs["dry_run"] is True

    @patch("orchestrators.sync_calendar.GoogleCalendarSync")
    @patch("orchestrators.sync_calendar.Config")
    def test_date_range_forwarded(
        self, mock_config, mock_google_cls,
        mock_notion_calendar, mock_state_manager,
    ):
        mock_config.GOOGLE_CALENDAR_IDS = ["primary"]
        mock_config.GOOGLE_CALENDAR_NAMES = ["Personal"]

        mock_google = MagicMock()
        mock_google.authenticate.return_value = True
        mock_google.sync_calendar_to_notion.return_value = {
            "calendar_name": "Personal",
            "events_fetched": 0,
            "events_created": 0,
            "events_updated": 0,
            "events_deleted": 0,
            "events_skipped": 0,
            "errors": 0,
            "incremental": False,
            "new_sync_token": None,
        }
        mock_google_cls.return_value = mock_google

        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 12, 31, tzinfo=timezone.utc)

        sync_google_calendars(
            mock_notion_calendar, mock_state_manager,
            start_date=start, end_date=end,
        )

        _, kwargs = mock_google.sync_calendar_to_notion.call_args
        assert kwargs["start_date"] == start
        assert kwargs["end_date"] == end

    @patch("orchestrators.sync_calendar.GoogleCalendarSync")
    @patch("orchestrators.sync_calendar.Config")
    def test_calendar_sync_exception_counted_as_error(
        self, mock_config, mock_google_cls,
        mock_notion_calendar, mock_state_manager,
    ):
        mock_config.GOOGLE_CALENDAR_IDS = ["primary", "work"]
        mock_config.GOOGLE_CALENDAR_NAMES = ["Personal", "Work"]

        mock_google = MagicMock()
        mock_google.authenticate.return_value = True
        # First calendar succeeds, second throws
        mock_google.sync_calendar_to_notion.side_effect = [
            {
                "calendar_name": "Personal",
                "events_fetched": 3,
                "events_created": 3,
                "events_updated": 0,
                "events_deleted": 0,
                "events_skipped": 0,
                "errors": 0,
                "incremental": False,
                "new_sync_token": None,
            },
            Exception("Google API quota exceeded"),
        ]
        mock_google_cls.return_value = mock_google

        stats = sync_google_calendars(mock_notion_calendar, mock_state_manager)

        assert stats["calendars_synced"] == 1
        assert stats["total_errors"] == 1
        assert stats["total_events_created"] == 3

    @patch("orchestrators.sync_calendar.GoogleCalendarSync")
    @patch("orchestrators.sync_calendar.Config")
    def test_strips_whitespace_from_calendar_ids(
        self, mock_config, mock_google_cls,
        mock_notion_calendar, mock_state_manager,
    ):
        mock_config.GOOGLE_CALENDAR_IDS = [" primary "]
        mock_config.GOOGLE_CALENDAR_NAMES = [" Personal "]

        mock_google = MagicMock()
        mock_google.authenticate.return_value = True
        mock_google.sync_calendar_to_notion.return_value = {
            "calendar_name": "Personal",
            "events_fetched": 0,
            "events_created": 0,
            "events_updated": 0,
            "events_deleted": 0,
            "events_skipped": 0,
            "errors": 0,
            "incremental": False,
            "new_sync_token": None,
        }
        mock_google_cls.return_value = mock_google

        sync_google_calendars(mock_notion_calendar, mock_state_manager)

        call_args, call_kwargs = mock_google.sync_calendar_to_notion.call_args
        assert call_kwargs["calendar_id"] == "primary"
        assert call_kwargs["calendar_name"] == "Personal"


# =========================================================================
# print_sync_summary
# =========================================================================

class TestPrintSyncSummary:
    """Tests for the print_sync_summary function."""

    def test_success_output(self, capsys):
        stats = {
            "success": True,
            "calendars_synced": 1,
            "total_events_fetched": 10,
            "total_events_created": 5,
            "total_events_updated": 3,
            "total_events_deleted": 1,
            "total_events_skipped": 1,
            "total_errors": 0,
            "calendar_details": [
                {
                    "calendar_name": "Personal",
                    "events_fetched": 10,
                    "events_created": 5,
                    "events_updated": 3,
                    "events_deleted": 1,
                    "events_skipped": 1,
                    "errors": 0,
                },
            ],
        }

        print_sync_summary(stats, duration=5.0)

        captured = capsys.readouterr()
        assert "SYNC SUMMARY" in captured.out
        assert "Calendars synced: 1" in captured.out
        assert "Events created: 5" in captured.out
        assert "completed successfully" in captured.out

    def test_dry_run_output(self, capsys):
        stats = {
            "success": True,
            "calendars_synced": 1,
            "total_events_fetched": 10,
            "total_events_created": 0,
            "total_events_updated": 0,
            "total_events_deleted": 0,
            "total_events_skipped": 0,
            "total_errors": 0,
            "calendar_details": [],
        }

        print_sync_summary(stats, duration=2.0, dry_run=True)

        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out
        # In dry run, created/updated/deleted counts should not appear
        assert "Events created:" not in captured.out

    def test_failure_output(self, capsys):
        stats = {"success": False, "error": "Auth failed"}

        print_sync_summary(stats, duration=0.5)

        captured = capsys.readouterr()
        assert "Auth failed" in captured.out

    def test_errors_shown_in_output(self, capsys):
        stats = {
            "success": True,
            "calendars_synced": 1,
            "total_events_fetched": 5,
            "total_events_created": 3,
            "total_events_updated": 0,
            "total_events_deleted": 0,
            "total_events_skipped": 0,
            "total_errors": 2,
            "calendar_details": [
                {
                    "calendar_name": "Personal",
                    "events_fetched": 5,
                    "events_created": 3,
                    "events_updated": 0,
                    "events_deleted": 0,
                    "events_skipped": 0,
                    "errors": 2,
                },
            ],
        }

        print_sync_summary(stats, duration=3.0)

        captured = capsys.readouterr()
        assert "Errors: 2" in captured.out
        assert "with errors" in captured.out


# =========================================================================
# main (CLI entrypoint)
# =========================================================================

class TestMain:
    """Tests for the main CLI orchestrator."""

    @patch("orchestrators.sync_calendar.sync_google_calendars")
    @patch("orchestrators.sync_calendar.NotionCalendarSync")
    @patch("orchestrators.sync_calendar.NotionDailyTrackingSync")
    @patch("orchestrators.sync_calendar.StateManager")
    @patch("orchestrators.sync_calendar.Config")
    def test_normal_sync_flow(
        self, mock_config, mock_state_cls, mock_tracking_cls,
        mock_notion_cls, mock_sync_fn,
    ):
        mock_config.validate.return_value = (True, [])
        mock_config.NOTION_DAILY_TRACKING_DB_ID = "tracking-db-id"
        mock_sync_fn.return_value = {
            "success": True,
            "calendars_synced": 1,
            "total_events_fetched": 3,
            "total_events_created": 2,
            "total_events_updated": 1,
            "total_events_deleted": 0,
            "total_events_skipped": 0,
            "total_errors": 0,
            "calendar_details": [],
        }

        with patch("sys.argv", ["sync_calendar.py"]):
            result = main()

        assert result == 0
        mock_sync_fn.assert_called_once()

    @patch("orchestrators.sync_calendar.Config")
    def test_invalid_config_returns_1(self, mock_config):
        mock_config.validate.return_value = (False, ["NOTION_TOKEN not set"])

        with patch("sys.argv", ["sync_calendar.py"]):
            result = main()

        assert result == 1

    @patch("orchestrators.sync_calendar.sync_google_calendars")
    @patch("orchestrators.sync_calendar.NotionCalendarSync")
    @patch("orchestrators.sync_calendar.NotionDailyTrackingSync")
    @patch("orchestrators.sync_calendar.StateManager")
    @patch("orchestrators.sync_calendar.Config")
    def test_date_range_parsing(
        self, mock_config, mock_state_cls, mock_tracking_cls,
        mock_notion_cls, mock_sync_fn,
    ):
        mock_config.validate.return_value = (True, [])
        mock_config.NOTION_DAILY_TRACKING_DB_ID = "db-id"
        mock_sync_fn.return_value = {
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

        with patch("sys.argv", [
            "sync_calendar.py",
            "--start-date", "2026-06-01",
            "--end-date", "2026-06-30",
        ]):
            result = main()

        assert result == 0
        _, kwargs = mock_sync_fn.call_args
        assert kwargs["start_date"].year == 2026
        assert kwargs["start_date"].month == 6
        assert kwargs["start_date"].day == 1
        assert kwargs["end_date"].month == 6
        assert kwargs["end_date"].day == 30

    @patch("orchestrators.sync_calendar.Config")
    def test_invalid_date_format_returns_1(self, mock_config):
        mock_config.validate.return_value = (True, [])

        with patch("sys.argv", [
            "sync_calendar.py", "--start-date", "not-a-date"
        ]):
            result = main()

        assert result == 1

    @patch("orchestrators.sync_calendar.Config")
    def test_start_after_end_returns_1(self, mock_config):
        mock_config.validate.return_value = (True, [])

        with patch("sys.argv", [
            "sync_calendar.py",
            "--start-date", "2026-12-31",
            "--end-date", "2026-01-01",
        ]):
            result = main()

        assert result == 1

    @patch("orchestrators.sync_calendar.GoogleCalendarSync")
    @patch("orchestrators.sync_calendar.NotionDailyTrackingSync")
    @patch("orchestrators.sync_calendar.NotionCalendarSync")
    @patch("orchestrators.sync_calendar.Config")
    def test_health_check_passes(
        self, mock_config, mock_notion_cls, mock_tracking_cls, mock_google_cls,
    ):
        mock_config.validate.return_value = (True, [])
        mock_config.NOTION_DAILY_TRACKING_DB_ID = "db-id"

        mock_notion_instance = MagicMock()
        mock_notion_cls.return_value = mock_notion_instance

        mock_google_instance = MagicMock()
        mock_google_instance.authenticate.return_value = True
        mock_google_cls.return_value = mock_google_instance

        with patch("sys.argv", ["sync_calendar.py", "--health-check"]):
            result = main()

        assert result == 0

    @patch("orchestrators.sync_calendar.Config")
    def test_health_check_fails_on_invalid_config(self, mock_config):
        mock_config.validate.return_value = (
            False, ["NOTION_TOKEN not set"]
        )

        with patch("sys.argv", ["sync_calendar.py", "--health-check"]):
            result = main()

        assert result == 1

    @patch("orchestrators.sync_calendar.NotionCalendarSync")
    @patch("orchestrators.sync_calendar.Config")
    def test_health_check_fails_on_notion_error(
        self, mock_config, mock_notion_cls,
    ):
        mock_config.validate.return_value = (True, [])
        mock_notion_cls.side_effect = Exception("Connection refused")

        with patch("sys.argv", ["sync_calendar.py", "--health-check"]):
            result = main()

        assert result == 1

    @patch("orchestrators.sync_calendar.sync_google_calendars")
    @patch("orchestrators.sync_calendar.NotionCalendarSync")
    @patch("orchestrators.sync_calendar.NotionDailyTrackingSync")
    @patch("orchestrators.sync_calendar.StateManager")
    @patch("orchestrators.sync_calendar.Config")
    def test_sync_failure_returns_1(
        self, mock_config, mock_state_cls, mock_tracking_cls,
        mock_notion_cls, mock_sync_fn,
    ):
        mock_config.validate.return_value = (True, [])
        mock_config.NOTION_DAILY_TRACKING_DB_ID = "db-id"
        mock_sync_fn.return_value = {
            "success": False,
            "error": "Something went wrong",
        }

        with patch("sys.argv", ["sync_calendar.py"]):
            result = main()

        assert result == 1

    @patch("orchestrators.sync_calendar.sync_google_calendars")
    @patch("orchestrators.sync_calendar.NotionCalendarSync")
    @patch("orchestrators.sync_calendar.NotionDailyTrackingSync")
    @patch("orchestrators.sync_calendar.StateManager")
    @patch("orchestrators.sync_calendar.Config")
    def test_dry_run_forwarded_to_sync(
        self, mock_config, mock_state_cls, mock_tracking_cls,
        mock_notion_cls, mock_sync_fn,
    ):
        mock_config.validate.return_value = (True, [])
        mock_config.NOTION_DAILY_TRACKING_DB_ID = "db-id"
        mock_sync_fn.return_value = {
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

        with patch("sys.argv", ["sync_calendar.py", "--dry-run"]):
            main()

        _, kwargs = mock_sync_fn.call_args
        assert kwargs["dry_run"] is True

    @patch("orchestrators.sync_calendar.StateManager")
    @patch("orchestrators.sync_calendar.Config")
    def test_state_manager_init_failure_returns_1(
        self, mock_config, mock_state_cls,
    ):
        mock_config.validate.return_value = (True, [])
        mock_state_cls.side_effect = Exception("DB locked")

        with patch("sys.argv", ["sync_calendar.py"]):
            result = main()

        assert result == 1

    @patch("orchestrators.sync_calendar.sync_google_calendars")
    @patch("orchestrators.sync_calendar.NotionCalendarSync")
    @patch("orchestrators.sync_calendar.NotionDailyTrackingSync")
    @patch("orchestrators.sync_calendar.StateManager")
    @patch("orchestrators.sync_calendar.Config")
    def test_daily_tracking_init_failure_continues(
        self, mock_config, mock_state_cls, mock_tracking_cls,
        mock_notion_cls, mock_sync_fn,
    ):
        """If Daily Tracking DB is unavailable, sync continues without Day relations."""
        mock_config.validate.return_value = (True, [])
        mock_config.NOTION_DAILY_TRACKING_DB_ID = "db-id"
        mock_tracking_cls.side_effect = Exception("Tracking DB not found")
        mock_sync_fn.return_value = {
            "success": True,
            "calendars_synced": 1,
            "total_events_fetched": 3,
            "total_events_created": 3,
            "total_events_updated": 0,
            "total_events_deleted": 0,
            "total_events_skipped": 0,
            "total_errors": 0,
            "calendar_details": [],
        }

        with patch("sys.argv", ["sync_calendar.py"]):
            result = main()

        # Should still succeed — daily tracking is optional
        assert result == 0
        # NotionCalendarSync should be initialized with daily_tracking_sync=None
        mock_notion_cls.assert_called_once_with(daily_tracking_sync=None)

    @patch("orchestrators.sync_calendar.sync_google_calendars")
    @patch("orchestrators.sync_calendar.NotionCalendarSync")
    @patch("orchestrators.sync_calendar.NotionDailyTrackingSync")
    @patch("orchestrators.sync_calendar.StateManager")
    @patch("orchestrators.sync_calendar.Config")
    def test_no_daily_tracking_db_configured(
        self, mock_config, mock_state_cls, mock_tracking_cls,
        mock_notion_cls, mock_sync_fn,
    ):
        """When NOTION_DAILY_TRACKING_DB_ID is empty, skip Daily Tracking init."""
        mock_config.validate.return_value = (True, [])
        mock_config.NOTION_DAILY_TRACKING_DB_ID = ""
        mock_sync_fn.return_value = {
            "success": True,
            "calendars_synced": 1,
            "total_events_fetched": 0,
            "total_events_created": 0,
            "total_events_updated": 0,
            "total_events_deleted": 0,
            "total_events_skipped": 0,
            "total_errors": 0,
            "calendar_details": [],
        }

        with patch("sys.argv", ["sync_calendar.py"]):
            result = main()

        assert result == 0
        mock_tracking_cls.assert_not_called()
