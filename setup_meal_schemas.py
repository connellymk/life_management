#!/usr/bin/env python3
"""
Setup Airtable table schemas for meal system migration.

This script creates/updates fields in the following tables:
1. Recipes
2. Meal Plans
3. Planned Meals
4. Grocery Items
"""

import sys
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).parent))

from pyairtable import Api
from core.config import Config
from core.utils import setup_logging

logger = setup_logging("setup_meal_schemas")

# Table IDs (to be discovered)
# We'll need to find these from the base schema
WEEK_TABLE_ID = "tbl2B7ecl7heYiKha"  # From training plan migration
DAY_TABLE_ID = "tblHMwUnVg8bA1xoP"   # From training plan migration


def get_table_id_by_name(table_name):
    """Get table ID by table name."""
    try:
        token = Config.AIRTABLE_ACCESS_TOKEN
        base_id = Config.AIRTABLE_BASE_ID

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        schema_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
        response = requests.get(schema_url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to get schema: {response.status_code} - {response.text}")
            return None

        tables = response.json().get("tables", [])
        for table in tables:
            if table["name"] == table_name:
                return table["id"]

        logger.error(f"Table '{table_name}' not found")
        return None

    except Exception as e:
        logger.error(f"Error getting table ID: {e}")
        return None


def update_recipes_schema():
    """Update Recipes table schema."""
    logger.info("=" * 60)
    logger.info("Updating Recipes Table Schema")
    logger.info("=" * 60)

    try:
        table_id = get_table_id_by_name(Config.AIRTABLE_RECIPES)
        if not table_id:
            return False

        logger.info(f"Table ID: {table_id}")

        token = Config.AIRTABLE_ACCESS_TOKEN
        base_id = Config.AIRTABLE_BASE_ID

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Get existing fields
        schema_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
        response = requests.get(schema_url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to get schema: {response.status_code}")
            return False

        tables = response.json().get("tables", [])
        table = next((t for t in tables if t["id"] == table_id), None)

        if not table:
            logger.error("Table not found in schema")
            return False

        existing_fields = {field["name"]: field for field in table["fields"]}
        logger.info(f"Existing fields: {len(existing_fields)}")

        # Define required fields
        required_fields = {
            "Name": {"type": "singleLineText"},
            "Category": {
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Breakfast"},
                        {"name": "Lunch"},
                        {"name": "Dinner"},
                        {"name": "Snack"},
                        {"name": "Dessert"},
                        {"name": "Beverage"}
                    ]
                }
            },
            "Cuisine": {
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "American"},
                        {"name": "Italian"},
                        {"name": "Mexican"},
                        {"name": "Asian"},
                        {"name": "Mediterranean"},
                        {"name": "Indian"},
                        {"name": "Other"}
                    ]
                }
            },
            "Prep Time": {"type": "number", "options": {"precision": 0}},
            "Cook Time": {"type": "number", "options": {"precision": 0}},
            "Total Time": {"type": "number", "options": {"precision": 0}},
            "Servings": {"type": "number", "options": {"precision": 0}},
            "Difficulty": {
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Easy"},
                        {"name": "Medium"},
                        {"name": "Hard"}
                    ]
                }
            },
            "Ingredients": {"type": "multilineText"},
            "Instructions": {"type": "multilineText"},
            "Notes": {"type": "multilineText"},
            "Tags": {
                "type": "multipleSelects",
                "options": {
                    "choices": [
                        {"name": "Healthy"},
                        {"name": "Quick"},
                        {"name": "Budget-Friendly"},
                        {"name": "Meal Prep"},
                        {"name": "Freezer-Friendly"},
                        {"name": "One-Pot"},
                        {"name": "Slow Cooker"},
                        {"name": "Instant Pot"},
                        {"name": "Vegetarian"},
                        {"name": "Vegan"},
                        {"name": "Gluten-Free"},
                        {"name": "Dairy-Free"},
                        {"name": "Low-Carb"},
                        {"name": "High-Protein"}
                    ]
                }
            },
            "Calories": {"type": "number", "options": {"precision": 0}},
            "Protein": {"type": "number", "options": {"precision": 1}},
            "Carbs": {"type": "number", "options": {"precision": 1}},
            "Fat": {"type": "number", "options": {"precision": 1}},
            "Fiber": {"type": "number", "options": {"precision": 1}},
            "Rating": {"type": "rating", "options": {"max": 5, "color": "yellowBright", "icon": "star"}},
            "Last Made": {"type": "date", "options": {"dateFormat": {"name": "iso"}}},
            "Source": {"type": "singleLineText"},
            "Source URL": {"type": "url"},
            "Image URL": {"type": "url"},
            "Cost Per Serving": {"type": "number", "options": {"precision": 2}},
            "Active": {"type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
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

        # Create fields
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
                logger.error(f"  Failed '{field['name']}': {response.status_code} - {response.text}")
                error_count += 1

        logger.info(f"\nResults: {success_count} succeeded, {error_count} failed")
        return error_count == 0

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def update_meal_plans_schema():
    """Update Meal Plans table schema."""
    logger.info("\n" + "=" * 60)
    logger.info("Updating Meal Plans Table Schema")
    logger.info("=" * 60)

    try:
        table_id = get_table_id_by_name(Config.AIRTABLE_MEAL_PLANS)
        if not table_id:
            return False

        logger.info(f"Table ID: {table_id}")

        token = Config.AIRTABLE_ACCESS_TOKEN
        base_id = Config.AIRTABLE_BASE_ID

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Get existing fields
        schema_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
        response = requests.get(schema_url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to get schema: {response.status_code}")
            return False

        tables = response.json().get("tables", [])
        table = next((t for t in tables if t["id"] == table_id), None)

        if not table:
            logger.error("Table not found in schema")
            return False

        existing_fields = {field["name"]: field for field in table["fields"]}
        logger.info(f"Existing fields: {len(existing_fields)}")

        # Define required fields
        required_fields = {
            "Name": {"type": "singleLineText"},
            "Start Date": {"type": "date", "options": {"dateFormat": {"name": "iso"}}},
            "End Date": {"type": "date", "options": {"dateFormat": {"name": "iso"}}},
            "Week": {
                "type": "multipleRecordLinks",
                "options": {"linkedTableId": WEEK_TABLE_ID}
            },
            "Status": {
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Planning"},
                        {"name": "Active"},
                        {"name": "Completed"}
                    ]
                }
            },
            "Notes": {"type": "multilineText"},
            "Grocery List Generated": {"type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
            "Total Estimated Cost": {"type": "number", "options": {"precision": 2}},
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

        # Create fields
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
                logger.error(f"  Failed '{field['name']}': {response.status_code} - {response.text}")
                error_count += 1

        logger.info(f"\nResults: {success_count} succeeded, {error_count} failed")
        return error_count == 0

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def update_planned_meals_schema():
    """Update Planned Meals table schema."""
    logger.info("\n" + "=" * 60)
    logger.info("Updating Planned Meals Table Schema")
    logger.info("=" * 60)

    try:
        table_id = get_table_id_by_name(Config.AIRTABLE_PLANNED_MEALS)
        recipes_table_id = get_table_id_by_name(Config.AIRTABLE_RECIPES)
        meal_plans_table_id = get_table_id_by_name(Config.AIRTABLE_MEAL_PLANS)

        if not all([table_id, recipes_table_id, meal_plans_table_id]):
            logger.error("Failed to find required table IDs")
            return False

        logger.info(f"Table ID: {table_id}")
        logger.info(f"Recipes Table ID: {recipes_table_id}")
        logger.info(f"Meal Plans Table ID: {meal_plans_table_id}")
        logger.info(f"Day Table ID: {DAY_TABLE_ID}")

        token = Config.AIRTABLE_ACCESS_TOKEN
        base_id = Config.AIRTABLE_BASE_ID

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Get existing fields
        schema_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
        response = requests.get(schema_url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to get schema: {response.status_code}")
            return False

        tables = response.json().get("tables", [])
        table = next((t for t in tables if t["id"] == table_id), None)

        if not table:
            logger.error("Table not found in schema")
            return False

        existing_fields = {field["name"]: field for field in table["fields"]}
        logger.info(f"Existing fields: {len(existing_fields)}")

        # Define required fields
        required_fields = {
            "Name": {"type": "singleLineText"},
            "Date": {"type": "date", "options": {"dateFormat": {"name": "iso"}}},
            "Day": {
                "type": "multipleRecordLinks",
                "options": {"linkedTableId": DAY_TABLE_ID}
            },
            "Meal Plan": {
                "type": "multipleRecordLinks",
                "options": {"linkedTableId": meal_plans_table_id}
            },
            "Meal Type": {
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Breakfast"},
                        {"name": "Lunch"},
                        {"name": "Dinner"},
                        {"name": "Snack"}
                    ]
                }
            },
            "Recipe": {
                "type": "multipleRecordLinks",
                "options": {"linkedTableId": recipes_table_id}
            },
            "Servings": {"type": "number", "options": {"precision": 0}},
            "Status": {
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Planned"},
                        {"name": "Prepared"},
                        {"name": "Skipped"}
                    ]
                }
            },
            "Notes": {"type": "multilineText"},
            "Actual Cost": {"type": "number", "options": {"precision": 2}},
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

        # Create fields
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
                logger.error(f"  Failed '{field['name']}': {response.status_code} - {response.text}")
                error_count += 1

        logger.info(f"\nResults: {success_count} succeeded, {error_count} failed")
        return error_count == 0

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def update_grocery_items_schema():
    """Update Grocery Items table schema."""
    logger.info("\n" + "=" * 60)
    logger.info("Updating Grocery Items Table Schema")
    logger.info("=" * 60)

    try:
        table_id = get_table_id_by_name(Config.AIRTABLE_GROCERY_ITEMS)
        recipes_table_id = get_table_id_by_name(Config.AIRTABLE_RECIPES)
        meal_plans_table_id = get_table_id_by_name(Config.AIRTABLE_MEAL_PLANS)

        if not all([table_id, recipes_table_id, meal_plans_table_id]):
            logger.error("Failed to find required table IDs")
            return False

        logger.info(f"Table ID: {table_id}")

        token = Config.AIRTABLE_ACCESS_TOKEN
        base_id = Config.AIRTABLE_BASE_ID

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Get existing fields
        schema_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
        response = requests.get(schema_url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to get schema: {response.status_code}")
            return False

        tables = response.json().get("tables", [])
        table = next((t for t in tables if t["id"] == table_id), None)

        if not table:
            logger.error("Table not found in schema")
            return False

        existing_fields = {field["name"]: field for field in table["fields"]}
        logger.info(f"Existing fields: {len(existing_fields)}")

        # Define required fields
        required_fields = {
            "Name": {"type": "singleLineText"},
            "Category": {
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Produce"},
                        {"name": "Meat & Seafood"},
                        {"name": "Dairy & Eggs"},
                        {"name": "Bakery"},
                        {"name": "Pantry"},
                        {"name": "Frozen"},
                        {"name": "Beverages"},
                        {"name": "Snacks"},
                        {"name": "Other"}
                    ]
                }
            },
            "Quantity": {"type": "singleLineText"},
            "Unit": {
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "lb"},
                        {"name": "oz"},
                        {"name": "kg"},
                        {"name": "g"},
                        {"name": "cup"},
                        {"name": "tbsp"},
                        {"name": "tsp"},
                        {"name": "whole"},
                        {"name": "bunch"},
                        {"name": "package"},
                        {"name": "can"},
                        {"name": "bottle"}
                    ]
                }
            },
            "Meal Plan": {
                "type": "multipleRecordLinks",
                "options": {"linkedTableId": meal_plans_table_id}
            },
            "Recipe": {
                "type": "multipleRecordLinks",
                "options": {"linkedTableId": recipes_table_id}
            },
            "Store": {
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Grocery Store"},
                        {"name": "Farmers Market"},
                        {"name": "Bulk Store"},
                        {"name": "Specialty Store"},
                        {"name": "Online"}
                    ]
                }
            },
            "Purchased": {"type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
            "Estimated Cost": {"type": "number", "options": {"precision": 2}},
            "Actual Cost": {"type": "number", "options": {"precision": 2}},
            "Notes": {"type": "singleLineText"},
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

        # Create fields
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
                logger.error(f"  Failed '{field['name']}': {response.status_code} - {response.text}")
                error_count += 1

        logger.info(f"\nResults: {success_count} succeeded, {error_count} failed")
        return error_count == 0

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("Meal System Schema Setup")
    logger.info("=" * 60)

    success = True

    # Update Recipes
    if not update_recipes_schema():
        logger.error("Failed to update Recipes schema")
        success = False

    # Update Meal Plans
    if not update_meal_plans_schema():
        logger.error("Failed to update Meal Plans schema")
        success = False

    # Update Planned Meals
    if not update_planned_meals_schema():
        logger.error("Failed to update Planned Meals schema")
        success = False

    # Update Grocery Items
    if not update_grocery_items_schema():
        logger.error("Failed to update Grocery Items schema")
        success = False

    logger.info("\n" + "=" * 60)
    if success:
        logger.info("Schema Setup Complete!")
        logger.info("=" * 60)
        logger.info("\nNext steps:")
        logger.info("1. Share meal databases with Notion integration")
        logger.info("2. Run discover_meal_databases.py to find database IDs")
        logger.info("3. Run migration scripts to import data")
    else:
        logger.info("Some schema updates failed")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
