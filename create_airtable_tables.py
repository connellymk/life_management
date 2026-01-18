"""
Script to create Airtable data tables with proper schema.

This script creates the core data tables needed for the personal assistant:
- Calendar Events
- Training Sessions
- Health Metrics
- Body Metrics
- Training Plans

Each table includes links to Day/Week dimension tables and proper field types.
"""

from pyairtable import Api
from core.config import AirtableConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_calendar_events_table(api: Api, base_id: str):
    """Create Calendar Events table."""
    logger.info("Creating Calendar Events table...")

    table_schema = {
        "name": "Calendar Events",
        "description": "Events from Google Calendar and Microsoft Calendar",
        "fields": [
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
                    "linkedTableId": "Day",
                    "prefersSingleRecordLink": True
                },
                "description": "Link to Day table"
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
                "options": {
                    "precision": 0
                },
                "description": "Duration in minutes"
            },
            {
                "name": "All Day",
                "type": "checkbox",
                "description": "Is this an all-day event?"
            },
            {
                "name": "Calendar",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Personal", "color": "blueLight2"},
                        {"name": "School and Research", "color": "greenLight2"},
                        {"name": "Work", "color": "orangeLight2"}
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
                "type": "multilineText",
                "description": "Comma-separated list of attendees"
            },
            {
                "name": "Status",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Confirmed", "color": "greenLight2"},
                        {"name": "Tentative", "color": "yellowLight2"},
                        {"name": "Cancelled", "color": "redLight2"}
                    ]
                }
            },
            {
                "name": "Recurring",
                "type": "checkbox",
                "description": "Is this a recurring event?"
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
    }

    try:
        base = api.base(base_id)
        table = base.create_table(table_schema["name"], table_schema["fields"])
        logger.info(f"✓ Created Calendar Events table")
        return table
    except Exception as e:
        logger.error(f"✗ Failed to create Calendar Events table: {e}")
        return None


def create_training_sessions_table(api: Api, base_id: str):
    """Create Training Sessions table."""
    logger.info("Creating Training Sessions table...")

    table_schema = {
        "name": "Training Sessions",
        "description": "Workouts and training sessions from Garmin/Strava",
        "fields": [
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
                    "linkedTableId": "Day",
                    "prefersSingleRecordLink": True
                }
            },
            {
                "name": "Week",
                "type": "multipleRecordLinks",
                "options": {
                    "linkedTableId": "Week",
                    "prefersSingleRecordLink": True
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
                        {"name": "Running", "color": "redLight2"},
                        {"name": "Cycling", "color": "blueLight2"},
                        {"name": "Swimming", "color": "cyanLight2"},
                        {"name": "Strength", "color": "orangeLight2"},
                        {"name": "Hiking", "color": "greenLight2"},
                        {"name": "Walking", "color": "grayLight2"},
                        {"name": "Other", "color": "purpleLight2"}
                    ]
                }
            },
            {
                "name": "Duration (min)",
                "type": "number",
                "options": {
                    "precision": 0
                }
            },
            {
                "name": "Distance (mi)",
                "type": "number",
                "options": {
                    "precision": 2
                }
            },
            {
                "name": "Elevation Gain (ft)",
                "type": "number",
                "options": {
                    "precision": 0
                }
            },
            {
                "name": "Avg HR",
                "type": "number",
                "options": {
                    "precision": 0
                }
            },
            {
                "name": "Max HR",
                "type": "number",
                "options": {
                    "precision": 0
                }
            },
            {
                "name": "Avg Pace (min/mi)",
                "type": "singleLineText",
                "description": "Average pace as MM:SS"
            },
            {
                "name": "Calories",
                "type": "number",
                "options": {
                    "precision": 0
                }
            },
            {
                "name": "Training Effect",
                "type": "number",
                "options": {
                    "precision": 1
                }
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
                        {"name": "Garmin", "color": "blueLight2"},
                        {"name": "Strava", "color": "orangeLight2"},
                        {"name": "Manual", "color": "grayLight2"}
                    ]
                }
            }
        ]
    }

    try:
        base = api.base(base_id)
        table = base.create_table(table_schema["name"], table_schema["fields"])
        logger.info(f"✓ Created Training Sessions table")
        return table
    except Exception as e:
        logger.error(f"✗ Failed to create Training Sessions table: {e}")
        return None


def create_health_metrics_table(api: Api, base_id: str):
    """Create Health Metrics table."""
    logger.info("Creating Health Metrics table...")

    table_schema = {
        "name": "Health Metrics",
        "description": "Daily health metrics from Garmin",
        "fields": [
            {
                "name": "Day",
                "type": "multipleRecordLinks",
                "options": {
                    "linkedTableId": "Day",
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
                "options": {
                    "precision": 0
                },
                "description": "Resting heart rate (bpm)"
            },
            {
                "name": "HRV",
                "type": "number",
                "options": {
                    "precision": 0
                },
                "description": "Heart rate variability"
            },
            {
                "name": "Steps",
                "type": "number",
                "options": {
                    "precision": 0
                }
            },
            {
                "name": "Floors Climbed",
                "type": "number",
                "options": {
                    "precision": 0
                }
            },
            {
                "name": "Active Calories",
                "type": "number",
                "options": {
                    "precision": 0
                }
            },
            {
                "name": "Total Calories",
                "type": "number",
                "options": {
                    "precision": 0
                }
            },
            {
                "name": "Sleep Duration (hr)",
                "type": "number",
                "options": {
                    "precision": 1
                }
            },
            {
                "name": "Sleep Score",
                "type": "number",
                "options": {
                    "precision": 0
                }
            },
            {
                "name": "Deep Sleep (min)",
                "type": "number",
                "options": {
                    "precision": 0
                }
            },
            {
                "name": "REM Sleep (min)",
                "type": "number",
                "options": {
                    "precision": 0
                }
            },
            {
                "name": "Light Sleep (min)",
                "type": "number",
                "options": {
                    "precision": 0
                }
            },
            {
                "name": "Stress Level",
                "type": "number",
                "options": {
                    "precision": 0
                },
                "description": "Average stress level (0-100)"
            },
            {
                "name": "Body Battery",
                "type": "number",
                "options": {
                    "precision": 0
                },
                "description": "Energy level (0-100)"
            },
            {
                "name": "VO2 Max",
                "type": "number",
                "options": {
                    "precision": 1
                }
            },
            {
                "name": "Hydration (oz)",
                "type": "number",
                "options": {
                    "precision": 0
                }
            }
        ]
    }

    try:
        base = api.base(base_id)
        table = base.create_table(table_schema["name"], table_schema["fields"])
        logger.info(f"✓ Created Health Metrics table")
        return table
    except Exception as e:
        logger.error(f"✗ Failed to create Health Metrics table: {e}")
        return None


def create_body_metrics_table(api: Api, base_id: str):
    """Create Body Metrics table."""
    logger.info("Creating Body Metrics table...")

    table_schema = {
        "name": "Body Metrics",
        "description": "Body composition and weight measurements",
        "fields": [
            {
                "name": "Day",
                "type": "multipleRecordLinks",
                "options": {
                    "linkedTableId": "Day",
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
                "options": {
                    "precision": 1
                }
            },
            {
                "name": "Body Fat %",
                "type": "number",
                "options": {
                    "precision": 1
                }
            },
            {
                "name": "Muscle Mass (lbs)",
                "type": "number",
                "options": {
                    "precision": 1
                }
            },
            {
                "name": "BMI",
                "type": "number",
                "options": {
                    "precision": 1
                }
            },
            {
                "name": "Bone Mass (lbs)",
                "type": "number",
                "options": {
                    "precision": 1
                }
            },
            {
                "name": "Water %",
                "type": "number",
                "options": {
                    "precision": 1
                }
            },
            {
                "name": "Source",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Garmin Scale", "color": "blueLight2"},
                        {"name": "Manual", "color": "grayLight2"}
                    ]
                }
            },
            {
                "name": "Notes",
                "type": "multilineText"
            }
        ]
    }

    try:
        base = api.base(base_id)
        table = base.create_table(table_schema["name"], table_schema["fields"])
        logger.info(f"✓ Created Body Metrics table")
        return table
    except Exception as e:
        logger.error(f"✗ Failed to create Body Metrics table: {e}")
        return None


def create_training_plans_table(api: Api, base_id: str):
    """Create Training Plans table."""
    logger.info("Creating Training Plans table...")

    table_schema = {
        "name": "Training Plans",
        "description": "Multi-week training plans with phases and goals",
        "fields": [
            {
                "name": "Plan Name",
                "type": "singleLineText",
                "description": "Name of training plan"
            },
            {
                "name": "Race/Event",
                "type": "singleLineText",
                "description": "Target race or event"
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
                    "linkedTableId": "Week",
                    "prefersSingleRecordLink": True
                }
            },
            {
                "name": "End Week",
                "type": "multipleRecordLinks",
                "options": {
                    "linkedTableId": "Week",
                    "prefersSingleRecordLink": True
                }
            },
            {
                "name": "Total Weeks",
                "type": "number",
                "options": {
                    "precision": 0
                }
            },
            {
                "name": "Current Phase",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Base Building", "color": "blueLight2"},
                        {"name": "Build", "color": "greenLight2"},
                        {"name": "Peak", "color": "yellowLight2"},
                        {"name": "Taper", "color": "orangeLight2"},
                        {"name": "Recovery", "color": "purpleLight2"},
                        {"name": "Completed", "color": "grayLight2"}
                    ]
                }
            },
            {
                "name": "Weekly Mileage Target",
                "type": "number",
                "options": {
                    "precision": 0
                },
                "description": "Target weekly mileage"
            },
            {
                "name": "Key Workouts",
                "type": "multilineText",
                "description": "Description of key weekly workouts"
            },
            {
                "name": "Priority",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "A Race", "color": "redLight2"},
                        {"name": "B Race", "color": "yellowLight2"},
                        {"name": "C Race", "color": "greenLight2"}
                    ]
                }
            },
            {
                "name": "Status",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Active", "color": "greenLight2"},
                        {"name": "Planned", "color": "blueLight2"},
                        {"name": "Completed", "color": "grayLight2"},
                        {"name": "Abandoned", "color": "redLight2"}
                    ]
                }
            },
            {
                "name": "Notes",
                "type": "multilineText"
            }
        ]
    }

    try:
        base = api.base(base_id)
        table = base.create_table(table_schema["name"], table_schema["fields"])
        logger.info(f"✓ Created Training Plans table")
        return table
    except Exception as e:
        logger.error(f"✗ Failed to create Training Plans table: {e}")
        return None


def main():
    """Create all data tables in Airtable base."""
    print("=" * 60)
    print("AIRTABLE TABLE CREATION SCRIPT")
    print("=" * 60)
    print()

    # Initialize API client
    access_token = AirtableConfig.AIRTABLE_ACCESS_TOKEN or AirtableConfig.AIRTABLE_API_KEY
    base_id = AirtableConfig.AIRTABLE_BASE_ID

    if not access_token or not base_id:
        print("ERROR: Airtable credentials not configured in .env file")
        return

    api = Api(access_token)

    print(f"Base ID: {base_id}")
    print(f"Creating tables with links to Day and Week dimension tables...")
    print()

    # Create tables
    tables_created = []
    tables_failed = []

    # Calendar Events
    result = create_calendar_events_table(api, base_id)
    if result:
        tables_created.append("Calendar Events")
    else:
        tables_failed.append("Calendar Events")

    # Training Sessions
    result = create_training_sessions_table(api, base_id)
    if result:
        tables_created.append("Training Sessions")
    else:
        tables_failed.append("Training Sessions")

    # Health Metrics
    result = create_health_metrics_table(api, base_id)
    if result:
        tables_created.append("Health Metrics")
    else:
        tables_failed.append("Health Metrics")

    # Body Metrics
    result = create_body_metrics_table(api, base_id)
    if result:
        tables_created.append("Body Metrics")
    else:
        tables_failed.append("Body Metrics")

    # Training Plans
    result = create_training_plans_table(api, base_id)
    if result:
        tables_created.append("Training Plans")
    else:
        tables_failed.append("Training Plans")

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✓ Created: {len(tables_created)} tables")
    for table in tables_created:
        print(f"  - {table}")

    if tables_failed:
        print(f"\n✗ Failed: {len(tables_failed)} tables")
        for table in tables_failed:
            print(f"  - {table}")

    print()
    print("Next steps:")
    print("1. Review the created tables in your Airtable base")
    print("2. Adjust field types or add custom fields as needed")
    print("3. Grant your Personal Access Token permission to these tables")
    print("4. Test syncing data from Google Calendar and Garmin")
    print()


if __name__ == "__main__":
    main()
