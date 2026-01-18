"""
Restructure Training Plans table to match Training Sessions for planned vs actual comparison.
Also add Training Plan field to Week table.
"""

import requests
from core.config import AirtableConfig
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def delete_fields(base_url, headers, table_id, field_names):
    """Delete fields from a table."""
    # First, get current fields
    response = requests.get(f"{base_url}/{table_id}", headers=headers)
    if response.status_code != 200:
        return False

    fields = response.json().get("fields", [])
    field_ids_to_delete = [f["id"] for f in fields if f["name"] in field_names]

    for field_id in field_ids_to_delete:
        url = f"{base_url}/{table_id}/fields/{field_id}"
        response = requests.delete(url, headers=headers)
        if response.status_code == 200:
            logger.info(f"  - Deleted field ID: {field_id}")
        else:
            logger.warning(f"  x Failed to delete field: {response.text}")


def add_field(base_url, headers, table_id, field_config):
    """Add a field to a table."""
    url = f"{base_url}/{table_id}/fields"
    response = requests.post(url, headers=headers, json=field_config)

    if response.status_code in (200, 201):
        logger.info(f"  + Added field: {field_config['name']}")
        return True
    else:
        error_msg = response.json().get('error', {}).get('message', response.text)
        logger.warning(f"  x Failed to add {field_config['name']}: {error_msg}")
        return False


def main():
    print("=" * 60)
    print("RESTRUCTURE TRAINING PLANS TABLE")
    print("=" * 60)
    print()

    access_token = AirtableConfig.AIRTABLE_ACCESS_TOKEN or AirtableConfig.AIRTABLE_API_KEY
    base_id = AirtableConfig.AIRTABLE_BASE_ID
    base_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Get table IDs
    response = requests.get(base_url, headers=headers)
    if response.status_code != 200:
        logger.error(f"Failed to fetch tables: {response.text}")
        return

    tables = {table["name"]: table["id"] for table in response.json().get("tables", [])}

    day_table_id = tables.get("Day")
    week_table_id = tables.get("Week")
    training_plans_table_id = tables.get("Training Plans")

    if not training_plans_table_id:
        logger.error("Training Plans table not found!")
        return

    logger.info("Step 1: Clearing old fields from Training Plans table...")
    logger.info("(You may see errors if fields don't exist - that's OK)")
    print()

    # Fields to remove (old structure)
    old_fields = [
        "Plan Name", "Race/Event", "Event Date", "Start Week", "End Week",
        "Total Weeks", "Current Phase", "Weekly Mileage Target", "Key Workouts",
        "Priority", "Status", "Notes"
    ]

    delete_fields(base_url, headers, training_plans_table_id, old_fields)
    print()

    logger.info("Step 2: Adding new fields to Training Plans table...")
    print()

    # New fields that mirror Training Sessions
    new_fields = [
        {
            "name": "Planned Activity",
            "type": "singleLineText",
            "description": "Name of planned activity"
        },
        {
            "name": "Day",
            "type": "multipleRecordLinks",
            "options": {
                "linkedTableId": day_table_id
            }
        },
        {
            "name": "Week",
            "type": "multipleRecordLinks",
            "options": {
                "linkedTableId": week_table_id
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
            "name": "Planned Activity Type",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "Running"},
                    {"name": "Cycling"},
                    {"name": "Swimming"},
                    {"name": "Strength"},
                    {"name": "Hiking"},
                    {"name": "Walking"},
                    {"name": "Rest"},
                    {"name": "Cross Training"},
                    {"name": "Other"}
                ]
            }
        },
        {
            "name": "Planned Duration (min)",
            "type": "number",
            "options": {"precision": 0}
        },
        {
            "name": "Planned Distance (mi)",
            "type": "number",
            "options": {"precision": 2}
        },
        {
            "name": "Planned Pace (min/mi)",
            "type": "singleLineText",
            "description": "Target pace as MM:SS"
        },
        {
            "name": "Workout Type",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "Easy"},
                    {"name": "Long Run"},
                    {"name": "Tempo"},
                    {"name": "Interval"},
                    {"name": "Hill Repeats"},
                    {"name": "Recovery"},
                    {"name": "Race"},
                    {"name": "Strength"},
                    {"name": "Rest"}
                ]
            },
            "description": "Type of workout (easy, tempo, intervals, etc.)"
        },
        {
            "name": "Intensity",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "Low"},
                    {"name": "Medium"},
                    {"name": "High"}
                ]
            }
        },
        {
            "name": "Description",
            "type": "multilineText",
            "description": "Workout description and notes"
        },
        {
            "name": "Completed",
            "type": "checkbox",
            "options": {
                "icon": "check",
                "color": "greenBright"
            }
        },
        {
            "name": "Actual Activity",
            "type": "multipleRecordLinks",
            "options": {
                "linkedTableId": tables.get("Training Sessions")
            },
            "description": "Link to actual completed training session"
        },
        {
            "name": "Race/Event",
            "type": "singleLineText",
            "description": "If this is for a specific race/event"
        },
        {
            "name": "Priority",
            "type": "singleSelect",
            "options": {
                "choices": [
                    {"name": "A Race"},
                    {"name": "B Race"},
                    {"name": "C Race"},
                    {"name": "Training"}
                ]
            }
        }
    ]

    for field in new_fields:
        add_field(base_url, headers, training_plans_table_id, field)

    print()
    logger.info("Step 3: Adding 'Training Plan' field to Week table...")
    print()

    # Add Training Plan field to Week table
    add_field(base_url, headers, week_table_id, {
        "name": "Training Plan",
        "type": "multilineText",
        "description": "Weekly training plan overview and goals"
    })

    print()
    print("=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print()
    print("Updated structure:")
    print("- Training Plans: Now stores individual planned activities")
    print("- Week table: Now has 'Training Plan' field for weekly overview")
    print("- Can compare planned vs actual by linking Training Plans -> Training Sessions")
    print()


if __name__ == "__main__":
    main()
