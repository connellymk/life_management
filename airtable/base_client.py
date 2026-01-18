"""
Base Airtable client for connecting to Airtable API.
"""

from pyairtable import Api
from core.config import AirtableConfig
import logging

logger = logging.getLogger(__name__)


class AirtableClient:
    """
    Base client for Airtable API operations.

    Provides connection management and table access for all Airtable operations.
    Uses Personal Access Token (PAT) for authentication (recommended by Airtable).
    """

    def __init__(self, access_token: str = None, base_id: str = None):
        """
        Initialize Airtable client.

        Args:
            access_token: Airtable Personal Access Token (optional, reads from config if not provided)
            base_id: Airtable base ID (optional, reads from config if not provided)
        """
        # Use Personal Access Token if available, fall back to legacy API Key
        self.access_token = (
            access_token
            or AirtableConfig.AIRTABLE_ACCESS_TOKEN
            or AirtableConfig.AIRTABLE_API_KEY
        )
        self.base_id = base_id or AirtableConfig.AIRTABLE_BASE_ID

        if not self.access_token or not self.base_id:
            raise ValueError(
                "Airtable Personal Access Token and base ID must be provided or set in environment variables. "
                "Get a token from https://airtable.com/create/tokens"
            )

        self.api = Api(self.access_token)
        logger.info(f"Initialized Airtable client for base {self.base_id}")

    def get_table(self, table_name: str):
        """
        Get a table object for the specified table name.

        Args:
            table_name: Name of the table in Airtable

        Returns:
            Table object from pyairtable
        """
        return self.api.table(self.base_id, table_name)

    def get_day_table(self):
        """Get the Day dimension table."""
        return self.get_table(AirtableConfig.AIRTABLE_DAY)

    def get_week_table(self):
        """Get the Week dimension table."""
        return self.get_table(AirtableConfig.AIRTABLE_WEEK)

    def get_calendar_events_table(self):
        """Get the Calendar Events table."""
        return self.get_table(AirtableConfig.AIRTABLE_CALENDAR_EVENTS)

    def get_tasks_table(self):
        """Get the Tasks table."""
        return self.get_table(AirtableConfig.AIRTABLE_TASKS)

    def get_projects_table(self):
        """Get the Projects table."""
        return self.get_table(AirtableConfig.AIRTABLE_PROJECTS)

    def get_classes_table(self):
        """Get the Classes table."""
        return self.get_table(AirtableConfig.AIRTABLE_CLASSES)

    def get_training_plans_table(self):
        """Get the Training Plans table."""
        return self.get_table(AirtableConfig.AIRTABLE_TRAINING_PLANS)

    def get_training_sessions_table(self):
        """Get the Training Sessions table."""
        return self.get_table(AirtableConfig.AIRTABLE_TRAINING_SESSIONS)

    def get_health_metrics_table(self):
        """Get the Health Metrics table."""
        return self.get_table(AirtableConfig.AIRTABLE_HEALTH_METRICS)

    def get_body_metrics_table(self):
        """Get the Body Metrics table."""
        return self.get_table(AirtableConfig.AIRTABLE_BODY_METRICS)

    def get_sync_logs_table(self):
        """Get the Sync Logs table."""
        return self.get_table(AirtableConfig.AIRTABLE_SYNC_LOGS)

    def get_day_record_id(self, day_value: str) -> str:
        """
        Look up the Airtable record ID for a Day table record by its Day field value.

        Args:
            day_value: Day field value in ISO format (e.g., "2026-01-17")

        Returns:
            str: Airtable record ID (e.g., "recXXXXXXXXXXXXXX")

        Raises:
            ValueError: If no matching Day record is found
        """
        day_table = self.get_day_table()
        # Use DATESTR to convert the Date field to string for comparison
        formula = f"DATESTR({{Day}}) = '{day_value}'"
        records = day_table.all(formula=formula, max_records=1)

        if not records:
            raise ValueError(f"No Day record found for {day_value}. Please ensure the Day table has a record with Day='{day_value}'")

        return records[0]['id']

    def get_week_record_id(self, week_value: str) -> str:
        """
        Look up the Airtable record ID for a Week table record by its Name/Week field value.

        Args:
            week_value: Week field value (e.g., "2-26")

        Returns:
            str: Airtable record ID (e.g., "recXXXXXXXXXXXXXX")

        Raises:
            ValueError: If no matching Week record is found
        """
        week_table = self.get_week_table()
        formula = f"{{Name}} = '{week_value}'"
        records = week_table.all(formula=formula)

        if not records:
            raise ValueError(f"No Week record found for {week_value}. Please ensure the Week table has a record with Name='{week_value}'")

        return records[0]['id']
