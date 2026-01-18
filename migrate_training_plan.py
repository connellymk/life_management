#!/usr/bin/env python3
"""
Migrate Beaverhead 100K training plan from Notion to Airtable.

This script:
1. Updates Airtable table schemas to match the training plan requirements
2. Updates Weekly Planning records with training goals
3. Exports data from Notion and imports to Airtable
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import requests

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pyairtable import Api
from core.config import Config
from core.utils import setup_logging

logger = setup_logging("migrate_training_plan")

# Table IDs from instructions
PLANNED_TRAINING_ACTIVITIES_TABLE_ID = "tblxSnGD6CS9ea0cM"
WEEKLY_PLANNING_TABLE_ID = "tbl2B7ecl7heYiKha"


def update_planned_training_activities_schema():
    """Update Planned Training Activities table schema."""
    logger.info("=" * 60)
    logger.info("Updating Planned Training Activities Table Schema")
    logger.info("=" * 60)

    try:
        token = Config.AIRTABLE_ACCESS_TOKEN
        base_id = Config.AIRTABLE_BASE_ID
        table_id = PLANNED_TRAINING_ACTIVITIES_TABLE_ID

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Get table schema
        schema_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
        response = requests.get(schema_url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to get schema: {response.status_code} - {response.text}")
            return False

        tables = response.json().get("tables", [])
        table = None
        for t in tables:
            if t["id"] == table_id:
                table = t
                break

        if not table:
            logger.error(f"Table {table_id} not found")
            return False

        logger.info(f"Found table: {table['name']} (ID: {table['id']})")

        # Get existing fields
        existing_fields = {field["name"]: field for field in table["fields"]}
        logger.info(f"\nExisting fields: {len(existing_fields)}")

        # Define required fields
        required_fields = {
            "Name": {"type": "singleLineText"},
            "Date": {"type": "date", "options": {"dateFormat": {"name": "iso"}}},
            "Week Number": {"type": "number", "options": {"precision": 0}},
            "Day of Week": {
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Monday"},
                        {"name": "Tuesday"},
                        {"name": "Wednesday"},
                        {"name": "Thursday"},
                        {"name": "Friday"},
                        {"name": "Saturday"},
                        {"name": "Sunday"},
                    ]
                },
            },
            "Status": {
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Planned"},
                        {"name": "Completed"},
                        {"name": "Skipped"},
                        {"name": "Modified"},
                        {"name": "Missed"},
                    ]
                },
            },
            "Workout Type": {
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Long Run"},
                        {"name": "Easy Run"},
                        {"name": "Tempo Run"},
                        {"name": "Hill Workout"},
                        {"name": "Intervals"},
                        {"name": "Recovery Run"},
                        {"name": "Strength Training"},
                        {"name": "Cross Training"},
                        {"name": "Rest Day"},
                    ]
                },
            },
            "Training Phase": {
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Base Building"},
                        {"name": "Build 1"},
                        {"name": "Build 2"},
                        {"name": "Peak"},
                        {"name": "Taper"},
                    ]
                },
            },
            "Priority": {
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Key Workout"},
                        {"name": "Important"},
                        {"name": "Standard"},
                        {"name": "Optional"},
                    ]
                },
            },
            "Focus Areas": {
                "type": "multipleSelects",
                "options": {
                    "choices": [
                        {"name": "Endurance"},
                        {"name": "Speed"},
                        {"name": "Hills"},
                        {"name": "Recovery"},
                        {"name": "Nutrition Practice"},
                        {"name": "Gear Testing"},
                        {"name": "Mental Training"},
                    ]
                },
            },
            "Workout Description": {"type": "multilineText"},
            "Planned Distance": {"type": "number", "options": {"precision": 2}},
            "Planned Duration": {"type": "number", "options": {"precision": 0}},
            "Planned Elevation Gain": {"type": "number", "options": {"precision": 0}},
            "Target Pace Effort": {"type": "singleLineText"},
            "Workout Notes": {"type": "multilineText"},
            "Weekly Mileage Target": {"type": "number", "options": {"precision": 1}},
            "Weekly Elevation Target": {"type": "number", "options": {"precision": 0}},
        }

        # Check which fields need to be created
        fields_to_create = []

        for field_name, field_spec in required_fields.items():
            if field_name not in existing_fields:
                fields_to_create.append({"name": field_name, **field_spec})
                logger.info(f"  Will create: {field_name} ({field_spec['type']})")
            else:
                # Check if field type matches
                existing_type = existing_fields[field_name]["type"]
                if existing_type != field_spec["type"]:
                    logger.warning(
                        f"  Field '{field_name}' exists but type mismatch: "
                        f"{existing_type} vs {field_spec['type']}"
                    )

        logger.info(f"\nFields to create: {len(fields_to_create)}")

        if not fields_to_create:
            logger.info("All required fields already exist")
            return True

        # Create fields via API
        create_field_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables/{table_id}/fields"
        success_count = 0
        error_count = 0

        logger.info("\nCreating fields...")
        for field in fields_to_create:
            response = requests.post(create_field_url, headers=headers, json=field)

            if response.status_code == 200:
                logger.info(f"  Created: {field['name']}")
                success_count += 1
            else:
                logger.error(f"  Failed to create '{field['name']}': {response.status_code} - {response.text}")
                error_count += 1

        logger.info(f"\nResults: {success_count} succeeded, {error_count} failed")
        return error_count == 0

    except Exception as e:
        logger.error(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def update_weekly_planning_schema():
    """Update Weekly Planning table schema."""
    logger.info("\n" + "=" * 60)
    logger.info("Updating Weekly Planning Table Schema")
    logger.info("=" * 60)

    try:
        token = Config.AIRTABLE_ACCESS_TOKEN
        base_id = Config.AIRTABLE_BASE_ID
        table_id = WEEKLY_PLANNING_TABLE_ID

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Get table schema
        schema_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
        response = requests.get(schema_url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to get schema: {response.status_code} - {response.text}")
            return False

        tables = response.json().get("tables", [])
        table = None
        for t in tables:
            if t["id"] == table_id:
                table = t
                break

        if not table:
            logger.error(f"Table {table_id} not found")
            return False

        logger.info(f"Found table: {table['name']} (ID: {table['id']})")

        # Get existing fields
        existing_fields = {field["name"]: field for field in table["fields"]}
        logger.info(f"\nExisting fields: {len(existing_fields)}")

        # Define required fields
        required_fields = {
            "Week Number": {"type": "number", "options": {"precision": 0}},
            "Week Starting": {"type": "date", "options": {"dateFormat": {"name": "iso"}}},
            "Week Ending": {"type": "date", "options": {"dateFormat": {"name": "iso"}}},
            "Training Phase": {
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Base Building"},
                        {"name": "Build 1"},
                        {"name": "Build 2"},
                        {"name": "Peak"},
                        {"name": "Taper"},
                    ]
                },
            },
            "Weekly Goals": {"type": "multilineText"},
            "Mileage Target": {"type": "number", "options": {"precision": 1}},
            "Elevation Target": {"type": "number", "options": {"precision": 0}},
            "Key Workouts": {"type": "multilineText"},
            "Weekly Reflection": {"type": "multilineText"},
            "Challenges": {"type": "multilineText"},
            "Wins": {"type": "multilineText"},
            "Energy Level": {"type": "rating", "options": {"max": 5, "color": "yellowBright", "icon": "star"}},
            "Recovery Quality": {"type": "rating", "options": {"max": 5, "color": "greenBright", "icon": "star"}},
            "Overall Rating": {"type": "rating", "options": {"max": 5, "color": "blueBright", "icon": "star"}},
            "Adjustments Made": {"type": "multilineText"},
            "Next Week Focus": {"type": "multilineText"},
            "Notes": {"type": "multilineText"},
        }

        # Check which fields need to be created
        fields_to_create = []

        for field_name, field_spec in required_fields.items():
            if field_name not in existing_fields:
                fields_to_create.append({"name": field_name, **field_spec})
                logger.info(f"  Will create: {field_name} ({field_spec['type']})")

        logger.info(f"\nFields to create: {len(fields_to_create)}")

        if not fields_to_create:
            logger.info("All required fields already exist")
            return True

        # Create fields via API
        create_field_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables/{table_id}/fields"
        success_count = 0
        error_count = 0

        logger.info("\nCreating fields...")
        for field in fields_to_create:
            response = requests.post(create_field_url, headers=headers, json=field)

            if response.status_code == 200:
                logger.info(f"  Created: {field['name']}")
                success_count += 1
            else:
                logger.error(f"  Failed to create '{field['name']}': {response.status_code} - {response.text}")
                error_count += 1

        logger.info(f"\nResults: {success_count} succeeded, {error_count} failed")
        return error_count == 0

    except Exception as e:
        logger.error(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def update_weekly_goals():
    """Update Weekly Planning records with training goals."""
    logger.info("\n" + "=" * 60)
    logger.info("Updating Weekly Planning Records with Goals")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        table = api.table(Config.AIRTABLE_BASE_ID, WEEKLY_PLANNING_TABLE_ID)

        # Fetch all records
        records = table.all()
        logger.info(f"Found {len(records)} weekly planning records")

        # Debug: Check what fields are actually in the first record
        if records:
            logger.info(f"\nSample record fields: {list(records[0]['fields'].keys())}")

        # Define goals by phase
        goals_by_phase = {
            "Base Building": "Build aerobic base with easy miles and cross-training. Focus on consistency and volume.",
            "Build 1": "Increase volume with hill repeats and back-to-back long runs. Focus on sustained efforts.",
            "Build 2": "Peak mileage weeks with long runs featuring significant elevation. Tempo and hill work.",
            "Peak": "Race simulation and confidence building. Practice race-day gear and nutrition strategy.",
            "Taper": "Reduce volume while maintaining intensity. Prioritize rest and mental preparation for race day.",
        }

        # Update each record
        updates = []
        for record in records:
            fields = record["fields"]

            # Try to get week number from existing fields
            week_number = fields.get("Week Number") or fields.get("Week")

            # If not found, try to extract from Name field (e.g., "Week 1", "W1", "1")
            if not week_number and "Name" in fields:
                name = fields["Name"]
                # Try to extract number from the name
                import re
                match = re.search(r'\d+', name)
                if match:
                    week_number = int(match.group())

            if not week_number:
                logger.warning(f"Skipping record {record['id']} - no week number found (Name: {fields.get('Name', 'N/A')})")
                continue

            # Determine phase based on week number
            training_phase = None
            if 1 <= week_number <= 8:
                training_phase = "Base Building"
            elif 9 <= week_number <= 14:
                training_phase = "Build 1"
            elif 15 <= week_number <= 20:
                training_phase = "Build 2"
            elif 21 <= week_number <= 22:
                training_phase = "Peak"
            elif 23 <= week_number <= 25:
                training_phase = "Taper"

            if training_phase and training_phase in goals_by_phase:
                goals = goals_by_phase[training_phase]
                update_fields = {
                    "Weekly Goals": goals,
                    "Week Number": week_number  # Also populate the Week Number field
                }

                # Only set Training Phase if the field exists and is not already set
                if "Training Phase" not in fields or not fields.get("Training Phase"):
                    update_fields["Training Phase"] = training_phase

                updates.append({
                    "id": record["id"],
                    "fields": update_fields
                })

        if updates:
            logger.info(f"\nUpdating {len(updates)} records with training goals...")

            # Batch update (max 10 records at a time)
            batch_size = 10
            for i in range(0, len(updates), batch_size):
                batch = updates[i:i + batch_size]
                table.batch_update(batch)
                logger.info(f"  ✓ Updated records {i+1}-{min(i+batch_size, len(updates))}")

            logger.info(f"\n✓ Successfully updated {len(updates)} weekly planning records")
        else:
            logger.info("\nNo records need updating")

        return True

    except Exception as e:
        logger.error(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("Training Plan Migration Script")
    logger.info("=" * 60)
    logger.info("\nThis script updates Airtable tables for the Beaverhead 100K training plan.\n")

    success = True

    # Step 1: Update Planned Training Activities schema
    logger.info("\nStep 1: Update Planned Training Activities Schema")
    if not update_planned_training_activities_schema():
        success = False

    # Step 2: Update Weekly Planning schema
    logger.info("\nStep 2: Update Weekly Planning Schema")
    if not update_weekly_planning_schema():
        success = False

    # Step 3: Update Weekly Goals
    logger.info("\nStep 3: Update Weekly Planning Goals")
    if not update_weekly_goals():
        success = False

    logger.info("\n" + "=" * 60)
    if success:
        logger.info("✓ Migration script complete!")
    else:
        logger.info("✗ Some steps failed")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
