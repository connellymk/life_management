"""
Unified configuration management for all integrations.
Loads from single .env file at project root.
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables from project root
BASE_DIR = Path(__file__).parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Base configuration class."""

    # Notion (shared across all integrations)
    NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")

    # Notion Database IDs
    NOTION_CALENDAR_DB_ID = os.getenv("NOTION_CALENDAR_DB_ID", "")
    NOTION_WORKOUTS_DB_ID = os.getenv("NOTION_WORKOUTS_DB_ID", "")
    NOTION_DAILY_METRICS_DB_ID = os.getenv("NOTION_DAILY_METRICS_DB_ID", "")
    NOTION_BODY_METRICS_DB_ID = os.getenv("NOTION_BODY_METRICS_DB_ID", "")

    # Google Calendar
    GOOGLE_CALENDAR_IDS = os.getenv("GOOGLE_CALENDAR_IDS", "primary").split(",")
    GOOGLE_CALENDAR_NAMES = os.getenv("GOOGLE_CALENDAR_NAMES", "Personal").split(",")
    GOOGLE_CLIENT_SECRET_PATH = os.getenv(
        "GOOGLE_CLIENT_SECRET_PATH", "credentials/google_client_secret.json"
    )
    GOOGLE_TOKEN_PATH = os.getenv(
        "GOOGLE_TOKEN_PATH", "credentials/google_token.json"
    )

    # Garmin
    GARMIN_EMAIL = os.getenv("GARMIN_EMAIL", "")
    GARMIN_PASSWORD = os.getenv("GARMIN_PASSWORD", "")

    # Sync settings
    SYNC_LOOKBACK_DAYS = int(os.getenv("SYNC_LOOKBACK_DAYS", "90"))
    SYNC_LOOKAHEAD_DAYS = int(os.getenv("SYNC_LOOKAHEAD_DAYS", "365"))
    UNIT_SYSTEM = os.getenv("UNIT_SYSTEM", "imperial").lower()

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_PATH = os.getenv("LOG_PATH", "logs/sync.log")
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "10485760"))
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # Base directory
    BASE_DIR = Path(__file__).parent.parent

    @classmethod
    def validate(cls) -> tuple[bool, List[str]]:
        """
        Validate configuration.

        Returns:
            tuple: (is_valid, list of error messages)
        """
        errors = []

        # Check Notion token
        if not cls.NOTION_TOKEN:
            errors.append("NOTION_TOKEN not set in .env file")
        elif not (cls.NOTION_TOKEN.startswith("secret_") or cls.NOTION_TOKEN.startswith("ntn_")):
            errors.append("NOTION_TOKEN should start with 'secret_' or 'ntn_'")

        return len(errors) == 0, errors


class GoogleCalendarConfig(Config):
    """Google Calendar specific configuration."""

    @classmethod
    def validate(cls) -> tuple[bool, List[str]]:
        """Validate Google Calendar configuration."""
        is_valid, errors = super().validate()

        if not cls.NOTION_CALENDAR_DB_ID:
            errors.append("NOTION_CALENDAR_DB_ID not set")

        if len(cls.GOOGLE_CALENDAR_IDS) != len(cls.GOOGLE_CALENDAR_NAMES):
            errors.append(
                f"Number of GOOGLE_CALENDAR_IDS ({len(cls.GOOGLE_CALENDAR_IDS)}) "
                f"doesn't match GOOGLE_CALENDAR_NAMES ({len(cls.GOOGLE_CALENDAR_NAMES)})"
            )

        return len(errors) == 0, errors


class GarminConfig(Config):
    """Garmin specific configuration."""

    @classmethod
    def validate(cls) -> tuple[bool, List[str]]:
        """Validate Garmin configuration."""
        is_valid, errors = super().validate()

        if not cls.GARMIN_EMAIL:
            errors.append("GARMIN_EMAIL not set")
        if not cls.GARMIN_PASSWORD:
            errors.append("GARMIN_PASSWORD not set")

        for db_id, name in [
            (cls.NOTION_WORKOUTS_DB_ID, "NOTION_WORKOUTS_DB_ID"),
            (cls.NOTION_DAILY_METRICS_DB_ID, "NOTION_DAILY_METRICS_DB_ID"),
            (cls.NOTION_BODY_METRICS_DB_ID, "NOTION_BODY_METRICS_DB_ID"),
        ]:
            if not db_id:
                errors.append(f"{name} not set")

        return len(errors) == 0, errors
