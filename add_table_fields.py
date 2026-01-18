"""
Add fields to existing Airtable tables.

This script adds all necessary fields to tables that have already been created.
Run this after you've created the empty tables in Airtable.
"""

import requests
from core.config import AirtableConfig
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class FieldAdder:
    """Helper class to add fields to Airtable tables."""

    def __init__(self):
        self.access_token = AirtableConfig.AIRTABLE_ACCESS_TOKEN or AirtableConfig.AIRTABLE_API_KEY
        self.base_id = AirtableConfig.AIRTABLE_BASE_ID
        self.base_url = f"https://api.airtable.com/v0/meta/bases/{self.base_id}/tables"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        # Get table IDs
        self.table_ids = self._get_table_ids()

    def _get_table_ids(self):
        """Fetch all table IDs from the base."""
        response = requests.get(self.base_url, headers=self.headers)
        if response.status_code == 200:
            tables = response.json().get("tables", [])
            return {table["name"]: table["id"] for table in tables}
        else:
            logger.error(f"Failed to fetch tables: {response.text}")
            return {}

    def add_fields(self, table_name, fields):
        """Add fields to a table."""
        if table_name not in self.table_ids:
            logger.error(f"Table '{table_name}' not found in base")
            return False

        table_id = self.table_ids[table_name]
        url = f"{self.base_url}/{table_id}/fields"

        success_count = 0
        fail_count = 0

        for field in fields:
            response = requests.post(url, headers=self.headers, json=field)
            if response.status_code in (200, 201):
                logger.info(f"  + Added field: {field['name']}")
                success_count += 1
            else:
                logger.warning(f"  x Failed to add {field['name']}: {response.json().get('error', {}).get('message', response.text)}")
                fail_count += 1

        logger.info(f"  Summary: {success_count} added, {fail_count} failed\n")
        return fail_count == 0


def get_calendar_events_fields(day_table_id):
    """Get field definitions for Calendar Events table."""
    return [
        {
            "name": "Event ID",
            "type": "singleLineText",
            "description": "Unique event ID from calendar provider"
        },
        {
            "name": "Title",
            "type": "singleLineText",
            "description": "Event title/summary"
        },
        {
            "name": "Day",
            "type": "multipleRecordLinks",
            "options": {
                "linkedTableId": day_table_id,
                "prefersSingleRecordLink": True
            }
        },
        {
            "name": "Date",
            "type": "date",
            "options": {
                "dateFormat": {"name": "us"}
            }
        },
        {
            "name": "Start Time",
            "type": "dateTime",
            "options": {
                "dateFormat": {"name": "us"},
                "timeFormat": {"name": "12hour"},
                "timeZone": "client"
            }
        },
        {
            "name": "End Time",
            "type": "dateTime",
            "options": {
                "dateFormat": {"name": "us"},
                "timeFormat": {"name": "12hour"},
                "timeZone": "client"
            }
        },
        {
            "name": "Duration (min)",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "All Day",
            "type": "checkbox"
        },
        {
            "name": "Calendar",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "Personal"},
                    {"name": "School and Research"},
                    {"name": "Work"}
                ]
            }
        },
        {
            "name": "Location",
            "type": "singleLineText"
        },
        {
            "name": "Description",
            "type": "multilineText"
        },
        {
            "name": "Attendees",
            "type": "multilineText"
        },
        {
            "name": "Status",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "Confirmed"},
                    {"name": "Tentative"},
                    {"name": "Cancelled"}
                ]
            }
        },
        {
            "name": "Recurring",
            "type": "checkbox"
        },
        {
            "name": "Last Synced",
            "type": "dateTime",
            "options": {
                "dateFormat": {"name": "us"},
                "timeFormat": {"name": "12hour"},
                "timeZone": "client"
            }
        }
    ]


def get_training_sessions_fields(day_table_id, week_table_id):
    """Get field definitions for Training Sessions table."""
    return [
        {
            "name": "Activity ID",
            "type": "singleLineText",
            "description": "Unique activity ID from provider"
        },
        {
            "name": "Activity Name",
            "type": "singleLineText"
        },
        {
            "name": "Day",
            "type": "multipleRecordLinks",
            "options": {
                "linkedTableId": day_table_id,
                "prefersSingleRecordLink": True
            }
        },
        {
            "name": "Week",
            "type": "multipleRecordLinks",
            "options": {
                "linkedTableId": week_table_id,
                "prefersSingleRecordLink": True
            }
        },
        {
            "name": "Date",
            "type": "date",
            "options": {
                "dateFormat": {"name": "us"}
            }
        },
        {
            "name": "Start Time",
            "type": "dateTime",
            "options": {
                "dateFormat": {"name": "us"},
                "timeFormat": {"name": "12hour"},
                "timeZone": "client"
            }
        },
        {
            "name": "Activity Type",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "Running"},
                    {"name": "Cycling"},
                    {"name": "Swimming"},
                    {"name": "Strength"},
                    {"name": "Hiking"},
                    {"name": "Walking"},
                    {"name": "Other"}
                ]
            }
        },
        {
            "name": "Duration (min)",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Distance (mi)",
            "type": "number",
            "options": {"precision": 2}
        },
        {
            "name": "Elevation Gain (ft)",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Avg HR",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Max HR",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Avg Pace (min/mi)",
            "type": "singleLineText"
        },
        {
            "name": "Calories",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Training Effect",
            "type": "number",
            "options": {"precision": 1}
        },
        {
            "name": "Notes",
            "type": "multilineText"
        },
        {
            "name": "Source",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "Garmin"},
                    {"name": "Strava"},
                    {"name": "Manual"}
                ]
            }
        },
        {
            "name": "Last Synced",
            "type": "dateTime",
            "options": {
                "dateFormat": {"name": "us"},
                "timeFormat": {"name": "12hour"},
                "timeZone": "client"
            }
        }
    ]


def get_health_metrics_fields(day_table_id):
    """Get field definitions for Health Metrics table."""
    return [
        {
            "name": "Day",
            "type": "multipleRecordLinks",
            "options": {
                "linkedTableId": day_table_id,
                "prefersSingleRecordLink": True
            },
            "description": "Primary field - one record per day"
        },
        {
            "name": "Date",
            "type": "date",
            "options": {
                "dateFormat": {"name": "us"}
            }
        },
        {
            "name": "Resting HR",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "HRV",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Steps",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Floors Climbed",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Active Calories",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Total Calories",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Sleep Duration (hr)",
            "type": "number",
            "options": {"precision": 1}
        },
        {
            "name": "Sleep Score",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Deep Sleep (min)",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "REM Sleep (min)",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Light Sleep (min)",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Stress Level",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Body Battery",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "VO2 Max",
            "type": "number",
            "options": {"precision": 1}
        },
        {
            "name": "Hydration (oz)",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Last Synced",
            "type": "dateTime",
            "options": {
                "dateFormat": {"name": "us"},
                "timeFormat": {"name": "12hour"},
                "timeZone": "client"
            }
        }
    ]


def get_body_metrics_fields(day_table_id):
    """Get field definitions for Body Metrics table."""
    return [
        {
            "name": "Measurement ID",
            "type": "singleLineText",
            "description": "Auto-generated or timestamp"
        },
        {
            "name": "Day",
            "type": "multipleRecordLinks",
            "options": {
                "linkedTableId": day_table_id,
                "prefersSingleRecordLink": True
            }
        },
        {
            "name": "Date",
            "type": "date",
            "options": {
                "dateFormat": {"name": "us"}
            }
        },
        {
            "name": "Weight (lbs)",
            "type": "number",
            "options": {"precision": 1}
        },
        {
            "name": "Body Fat %",
            "type": "number",
            "options": {"precision": 1}
        },
        {
            "name": "Muscle Mass (lbs)",
            "type": "number",
            "options": {"precision": 1}
        },
        {
            "name": "BMI",
            "type": "number",
            "options": {"precision": 1}
        },
        {
            "name": "Bone Mass (lbs)",
            "type": "number",
            "options": {"precision": 1}
        },
        {
            "name": "Water %",
            "type": "number",
            "options": {"precision": 1}
        },
        {
            "name": "Source",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "Garmin Scale"},
                    {"name": "Manual"}
                ]
            }
        },
        {
            "name": "Notes",
            "type": "multilineText"
        },
        {
            "name": "Last Synced",
            "type": "dateTime",
            "options": {
                "dateFormat": {"name": "us"},
                "timeFormat": {"name": "12hour"},
                "timeZone": "client"
            }
        }
    ]


def get_training_plans_fields(week_table_id):
    """Get field definitions for Training Plans table."""
    return [
        {
            "name": "Plan Name",
            "type": "singleLineText",
            "description": "Name of training plan"
        },
        {
            "name": "Race/Event",
            "type": "singleLineText"
        },
        {
            "name": "Event Date",
            "type": "date",
            "options": {
                "dateFormat": {"name": "us"}
            }
        },
        {
            "name": "Start Week",
            "type": "multipleRecordLinks",
            "options": {
                "linkedTableId": week_table_id,
                "prefersSingleRecordLink": True
            }
        },
        {
            "name": "End Week",
            "type": "multipleRecordLinks",
            "options": {
                "linkedTableId": week_table_id,
                "prefersSingleRecordLink": True
            }
        },
        {
            "name": "Total Weeks",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Current Phase",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "Base Building"},
                    {"name": "Build"},
                    {"name": "Peak"},
                    {"name": "Taper"},
                    {"name": "Recovery"},
                    {"name": "Completed"}
                ]
            }
        },
        {
            "name": "Weekly Mileage Target",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Key Workouts",
            "type": "multilineText"
        },
        {
            "name": "Priority",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "A Race"},
                    {"name": "B Race"},
                    {"name": "C Race"}
                ]
            }
        },
        {
            "name": "Status",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "Active"},
                    {"name": "Planned"},
                    {"name": "Completed"},
                    {"name": "Abandoned"}
                ]
            }
        },
        {
            "name": "Notes",
            "type": "multilineText"
        }
    ]


def main():
    print("=" * 60)
    print("AIRTABLE FIELD ADDITION SCRIPT")
    print("=" * 60)
    print()

    adder = FieldAdder()

    # Get Day and Week table IDs
    day_table_id = adder.table_ids.get("Day")
    week_table_id = adder.table_ids.get("Week")

    if not day_table_id or not week_table_id:
        logger.error("Day and/or Week table not found in base!")
        logger.error(f"Available tables: {list(adder.table_ids.keys())}")
        return

    logger.info(f"Found Day table: {day_table_id}")
    logger.info(f"Found Week table: {week_table_id}")
    logger.info("")

    # Define which tables to process
    table_configs = [
        ("Calendar Events", get_calendar_events_fields(day_table_id)),
        ("Training Sessions", get_training_sessions_fields(day_table_id, week_table_id)),
        ("Health Metrics", get_health_metrics_fields(day_table_id)),
        ("Body Metrics", get_body_metrics_fields(day_table_id)),
        ("Training Plans", get_training_plans_fields(week_table_id))
    ]

    # Process each table
    for table_name, fields in table_configs:
        if table_name in adder.table_ids:
            logger.info(f"Adding fields to '{table_name}'...")
            adder.add_fields(table_name, fields)
        else:
            logger.warning(f"Table '{table_name}' not found - skipping\n")

    print("=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review the tables in Airtable to verify fields were added")
    print("2. Adjust field order or add any custom fields as needed")
    print("3. Test syncing data from Google Calendar and Garmin")
    print()


if __name__ == "__main__":
    main()
