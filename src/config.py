"""
Configuration management for Calendar Sync
Loads and validates environment variables
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for Calendar Sync system"""

    # Project paths
    BASE_DIR = Path(__file__).parent.parent
    CREDENTIALS_DIR = BASE_DIR / "credentials"
    LOGS_DIR = BASE_DIR / "logs"

    # Ensure directories exist
    CREDENTIALS_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)

    # === Google Calendar Configuration ===
    GOOGLE_CLIENT_SECRET_PATH = os.getenv(
        "GOOGLE_CLIENT_SECRET_PATH", "credentials/google_client_secret.json"
    )
    GOOGLE_TOKEN_PATH = os.getenv(
        "GOOGLE_TOKEN_PATH", "credentials/google_token.json"
    )
    GOOGLE_CALENDAR_IDS = os.getenv("GOOGLE_CALENDAR_IDS", "primary").split(",")
    GOOGLE_CALENDAR_NAMES = os.getenv("GOOGLE_CALENDAR_NAMES", "Personal").split(",")

    # Google Calendar API scopes
    GOOGLE_SCOPES = [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events.readonly",
    ]

    # === Notion Configuration ===
    NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
    NOTION_CALENDAR_DB_ID = os.getenv("NOTION_CALENDAR_DB_ID", "")
    NOTION_TRAINING_DB_ID = os.getenv("NOTION_TRAINING_DB_ID", "")
    NOTION_TASKS_DB_ID = os.getenv("NOTION_TASKS_DB_ID", "")

    # === Microsoft Graph Configuration (Future) ===
    MS_CLIENT_ID = os.getenv("MS_CLIENT_ID", "")
    MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET", "")
    MS_TENANT_ID = os.getenv("MS_TENANT_ID", "")
    MS_TOKEN_PATH = os.getenv("MS_TOKEN_PATH", "credentials/ms_token.json")
    MS_CALENDAR_NAMES = os.getenv("MS_CALENDAR_NAMES", "").split(",")

    # === Strava Configuration (Future) ===
    STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID", "")
    STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET", "")
    STRAVA_TOKEN_PATH = os.getenv("STRAVA_TOKEN_PATH", "credentials/strava_token.json")

    # === Sync Configuration ===
    SYNC_LOOKBACK_DAYS = int(os.getenv("SYNC_LOOKBACK_DAYS", "7"))
    SYNC_LOOKAHEAD_DAYS = int(os.getenv("SYNC_LOOKAHEAD_DAYS", "90"))
    SYNC_INTERVAL_MINUTES = int(os.getenv("SYNC_INTERVAL_MINUTES", "15"))

    # === Logging Configuration ===
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_PATH = os.getenv("LOG_PATH", "logs/sync.log")
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # === Notifications Configuration (Optional) ===
    NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "")
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

    @classmethod
    def validate(cls) -> List[str]:
        """
        Validate configuration and return list of errors

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check required Google Calendar settings
        if not os.path.exists(cls.BASE_DIR / cls.GOOGLE_CLIENT_SECRET_PATH):
            errors.append(
                f"Google client secret file not found at {cls.GOOGLE_CLIENT_SECRET_PATH}"
            )

        # Check required Notion settings
        if not cls.NOTION_TOKEN:
            errors.append("NOTION_TOKEN not set in .env file")
        elif not cls.NOTION_TOKEN.startswith("secret_"):
            errors.append("NOTION_TOKEN should start with 'secret_'")

        if not cls.NOTION_CALENDAR_DB_ID:
            errors.append("NOTION_CALENDAR_DB_ID not set in .env file")

        # Verify calendar IDs and names match
        if len(cls.GOOGLE_CALENDAR_IDS) != len(cls.GOOGLE_CALENDAR_NAMES):
            errors.append(
                f"Number of GOOGLE_CALENDAR_IDS ({len(cls.GOOGLE_CALENDAR_IDS)}) "
                f"doesn't match GOOGLE_CALENDAR_NAMES ({len(cls.GOOGLE_CALENDAR_NAMES)})"
            )

        return errors

    @classmethod
    def print_config(cls):
        """Print current configuration (hiding secrets)"""
        print("=== Current Configuration ===\n")

        print("Google Calendar:")
        print(f"  Calendar IDs: {cls.GOOGLE_CALENDAR_IDS}")
        print(f"  Calendar Names: {cls.GOOGLE_CALENDAR_NAMES}")
        print(f"  Token Path: {cls.GOOGLE_TOKEN_PATH}")

        print("\nNotion:")
        notion_token_preview = (
            f"{cls.NOTION_TOKEN[:10]}...{cls.NOTION_TOKEN[-4:]}"
            if cls.NOTION_TOKEN
            else "Not set"
        )
        print(f"  Token: {notion_token_preview}")
        print(f"  Calendar DB ID: {cls.NOTION_CALENDAR_DB_ID}")

        print("\nSync Settings:")
        print(f"  Lookback: {cls.SYNC_LOOKBACK_DAYS} days")
        print(f"  Lookahead: {cls.SYNC_LOOKAHEAD_DAYS} days")
        print(f"  Interval: {cls.SYNC_INTERVAL_MINUTES} minutes")

        print("\nLogging:")
        print(f"  Level: {cls.LOG_LEVEL}")
        print(f"  Path: {cls.LOG_PATH}")
        print()


# Singleton instance
config = Config()


if __name__ == "__main__":
    # Allow running this file directly to check configuration
    print("Validating configuration...\n")
    errors = Config.validate()

    if errors:
        print("❌ Configuration errors found:\n")
        for error in errors:
            print(f"  - {error}")
        exit(1)
    else:
        print("✓ Configuration is valid!\n")
        Config.print_config()
