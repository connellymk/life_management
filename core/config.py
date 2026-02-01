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
    NOTION_CALENDAR_DB_ID = os.getenv("NOTION_CALENDAR_DB_ID", "2e890d86-c150-801e-87d3-000b40a2b7f7")
    NOTION_WORKOUTS_DB_ID = os.getenv("NOTION_WORKOUTS_DB_ID", "")
    NOTION_DAILY_TRACKING_DB_ID = os.getenv("NOTION_DAILY_TRACKING_DB_ID", "")
    # Daily Tracking doubles as the Day dimension table for cross-database relations
    NOTION_DAY_DB_ID = os.getenv("NOTION_DAILY_TRACKING_DB_ID", "")

    # Google Calendar
    GOOGLE_CALENDAR_IDS = os.getenv("GOOGLE_CALENDAR_IDS", "primary").split(",")
    GOOGLE_CALENDAR_NAMES = os.getenv("GOOGLE_CALENDAR_NAMES", "Personal").split(",")
    GOOGLE_CLIENT_SECRET_PATH = os.getenv(
        "GOOGLE_CLIENT_SECRET_PATH", "credentials/google_client_secret.json"
    )
    GOOGLE_TOKEN_PATH = os.getenv(
        "GOOGLE_TOKEN_PATH", "credentials/google_token.json"
    )
    GOOGLE_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

    # Garmin
    GARMIN_EMAIL = os.getenv("GARMIN_EMAIL", "")
    GARMIN_PASSWORD = os.getenv("GARMIN_PASSWORD", "")

    # Plaid
    PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID", "")
    PLAID_SECRET = os.getenv("PLAID_SECRET", "")
    PLAID_ENVIRONMENT = os.getenv("PLAID_ENVIRONMENT", "sandbox")

    # Financial Database IDs
    NOTION_ACCOUNTS_DB_ID = os.getenv("NOTION_ACCOUNTS_DB_ID", "")
    NOTION_TRANSACTIONS_DB_ID = os.getenv("NOTION_TRANSACTIONS_DB_ID", "")
    NOTION_BALANCES_DB_ID = os.getenv("NOTION_BALANCES_DB_ID", "")
    NOTION_INVESTMENTS_DB_ID = os.getenv("NOTION_INVESTMENTS_DB_ID", "")
    NOTION_BILLS_DB_ID = os.getenv("NOTION_BILLS_DB_ID", "")

    # Sync settings
    PLAID_TRANSACTION_DAYS = int(os.getenv("PLAID_TRANSACTION_DAYS", "30"))
    SYNC_LOOKBACK_DAYS = int(os.getenv("SYNC_LOOKBACK_DAYS", "90"))
    SYNC_LOOKAHEAD_DAYS = int(os.getenv("SYNC_LOOKAHEAD_DAYS", "365"))
    UNIT_SYSTEM = os.getenv("UNIT_SYSTEM", "imperial").lower()

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_PATH = os.getenv("LOG_PATH", "logs/sync.log")
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "10485760"))
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # Database
    DATA_DB_PATH = os.getenv("DATA_DB_PATH", "data.db")

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
        errors = []

        # Check Notion token
        if not cls.NOTION_TOKEN:
            errors.append("NOTION_TOKEN not set in .env file")
        elif not (cls.NOTION_TOKEN.startswith("secret_") or cls.NOTION_TOKEN.startswith("ntn_")):
            errors.append("NOTION_TOKEN should start with 'secret_' or 'ntn_'")

        # Check Garmin credentials
        if not cls.GARMIN_EMAIL:
            errors.append("GARMIN_EMAIL not set")
        if not cls.GARMIN_PASSWORD:
            errors.append("GARMIN_PASSWORD not set")

        # Check Notion database IDs
        if not cls.NOTION_WORKOUTS_DB_ID:
            errors.append("NOTION_WORKOUTS_DB_ID not set")
        if not cls.NOTION_DAILY_TRACKING_DB_ID:
            errors.append("NOTION_DAILY_TRACKING_DB_ID not set")

        return len(errors) == 0, errors


class PlaidConfig(Config):
    """Plaid specific configuration."""

    @classmethod
    def validate(cls) -> tuple[bool, List[str]]:
        """Validate Plaid configuration."""
        is_valid, errors = super().validate()

        if not cls.PLAID_CLIENT_ID:
            errors.append("PLAID_CLIENT_ID not set")
        if not cls.PLAID_SECRET:
            errors.append("PLAID_SECRET not set")

        if cls.PLAID_ENVIRONMENT not in ["sandbox", "development", "production"]:
            errors.append(
                f"PLAID_ENVIRONMENT must be 'sandbox', 'development', or 'production' (got '{cls.PLAID_ENVIRONMENT}')"
            )

        for db_id, name in [
            (cls.NOTION_ACCOUNTS_DB_ID, "NOTION_ACCOUNTS_DB_ID"),
            (cls.NOTION_TRANSACTIONS_DB_ID, "NOTION_TRANSACTIONS_DB_ID"),
            (cls.NOTION_BALANCES_DB_ID, "NOTION_BALANCES_DB_ID"),
            (cls.NOTION_INVESTMENTS_DB_ID, "NOTION_INVESTMENTS_DB_ID"),
            (cls.NOTION_BILLS_DB_ID, "NOTION_BILLS_DB_ID"),
        ]:
            if not db_id:
                errors.append(f"{name} not set")

        return len(errors) == 0, errors
