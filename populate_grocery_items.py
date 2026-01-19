#!/usr/bin/env python3
"""
Populate Grocery Items table from recipe ingredients.

This script:
1. Reads recipes from Airtable
2. Parses ingredients from each recipe
3. Creates grocery items linked to recipes
4. Categorizes items by type
"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pyairtable import Api
from core.config import Config
from core.utils import setup_logging

logger = setup_logging("populate_grocery_items")

# Table IDs
RECIPES_TABLE_ID = "tbl0R6ndVQvvLzEoN"
GROCERY_ITEMS_TABLE_ID = "tblsqM5S4HfIFsDFD"

# Category mappings based on ingredient keywords
CATEGORY_KEYWORDS = {
    "Produce": [
        "zucchini", "carrots", "cucumber", "tomato", "onion", "garlic", "greens",
        "spinach", "kale", "lettuce", "celery", "bell pepper", "pepper", "avocado",
        "lemon", "lime", "apple", "banana", "berries", "fruit", "vegetable",
        "broccoli", "cauliflower", "potato", "sweet potato", "squash"
    ],
    "Meat & Seafood": [
        "turkey", "chicken", "beef", "pork", "salmon", "tuna", "shrimp",
        "ground turkey", "ground beef", "chicken breast", "fish", "meat"
    ],
    "Dairy & Eggs": [
        "eggs", "milk", "cheese", "yogurt", "butter", "cream", "sour cream",
        "cottage cheese", "ricotta", "mozzarella", "cheddar", "parmesan"
    ],
    "Pantry": [
        "flour", "almond flour", "coconut flour", "oats", "rice", "quinoa",
        "pasta", "bread", "oil", "olive oil", "coconut oil", "vinegar",
        "sauce", "tomato sauce", "broth", "stock", "beans", "lentils",
        "nuts", "almonds", "cashews", "walnuts", "peanuts", "seeds",
        "chia seeds", "flax seeds", "sesame seeds", "salt", "pepper",
        "spices", "herbs", "italian seasoning", "oregano", "basil", "thyme",
        "cumin", "paprika", "garlic powder", "onion powder", "cinnamon",
        "vanilla", "cocoa", "chocolate", "dates", "raisins", "dried",
        "honey", "maple syrup", "sugar", "almond butter", "peanut butter",
        "tahini", "mustard", "mayo", "ketchup", "soy sauce", "hot sauce"
    ],
    "Frozen": [
        "frozen", "ice cream", "frozen vegetables", "frozen fruit"
    ],
    "Beverages": [
        "water", "juice", "coffee", "tea", "soda", "milk", "almond milk",
        "coconut milk", "oat milk"
    ],
}

UNIT_MAPPINGS = {
    "lbs": "lb",
    "lb": "lb",
    "pounds": "lb",
    "pound": "lb",
    "oz": "oz",
    "ounces": "oz",
    "ounce": "oz",
    "kg": "kg",
    "g": "g",
    "grams": "g",
    "gram": "g",
    "cups": "cup",
    "cup": "cup",
    "c": "cup",
    "tbsp": "tbsp",
    "tablespoons": "tbsp",
    "tablespoon": "tbsp",
    "tsp": "tsp",
    "teaspoons": "tsp",
    "teaspoon": "tsp",
    "pints": "package",
    "pint": "package",
    "cloves": "whole",
    "clove": "whole",
    "bunches": "bunch",
    "bunch": "bunch",
}


def categorize_ingredient(ingredient_name):
    """Categorize an ingredient based on keywords."""
    ingredient_lower = ingredient_name.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in ingredient_lower:
                return category

    return "Other"


def parse_unit(quantity_str):
    """Parse quantity string to extract unit."""
    quantity_lower = quantity_str.lower().strip()

    for unit_variant, unit_standard in UNIT_MAPPINGS.items():
        if unit_variant in quantity_lower:
            return unit_standard

    # Default to whole if no unit found
    return "whole"


def parse_ingredient_line(line):
    """Parse an ingredient line to extract quantity, unit, and name."""
    # Remove bullet points and leading/trailing whitespace
    line = re.sub(r'^[�•\-\*]\s*', '', line).strip()

    if not line or line.startswith('#') or line.lower() in ['ingredients', 'protein:', 'base:', 'vegetables:', 'dressing:', 'optional:']:
        return None

    # Try to match pattern: "quantity unit ingredient"
    # Examples: "3 lbs ground turkey", "2 cups zucchini", "1/2 cup almond flour"
    match = re.match(r'^([\d\./\-]+(?:\s+[\d\./\-]+)?)\s+([a-zA-Z]+)?\s+(.+)$', line)

    if match:
        quantity = match.group(1).strip()
        unit = match.group(2).strip() if match.group(2) else ""
        name = match.group(3).strip()

        # Clean up the name (remove parenthetical notes, commas at end, etc.)
        name = re.sub(r'\([^)]+\)', '', name).strip()
        name = re.sub(r',\s*[a-z\s]+$', '', name).strip()

        # Get standard unit
        if unit:
            standard_unit = parse_unit(unit)
        else:
            standard_unit = "whole"

        return {
            "quantity": quantity,
            "unit": standard_unit,
            "name": name
        }

    # If no quantity, just return the item name
    return {
        "quantity": "1",
        "unit": "whole",
        "name": line
    }


def get_recipes_with_ingredients():
    """Fetch all recipes from Airtable."""
    logger.info("=" * 60)
    logger.info("Fetching Recipes from Airtable")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        table = api.table(Config.AIRTABLE_BASE_ID, RECIPES_TABLE_ID)

        records = table.all()
        logger.info(f"Found {len(records)} recipes")

        return records

    except Exception as e:
        logger.error(f"Error fetching recipes: {e}")
        import traceback
        traceback.print_exc()
        return []


def parse_recipe_ingredients(recipe_record):
    """Parse ingredients from a recipe record."""
    fields = recipe_record.get("fields", {})
    recipe_name = fields.get("Name", "Unknown")
    ingredients_text = fields.get("Ingredients", "")

    if not ingredients_text:
        logger.warning(f"No ingredients found for recipe: {recipe_name}")
        return []

    # Split by newlines
    lines = ingredients_text.split('\n')

    grocery_items = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        parsed = parse_ingredient_line(line)
        if parsed and parsed["name"]:
            # Categorize the ingredient
            category = categorize_ingredient(parsed["name"])

            grocery_items.append({
                "name": parsed["name"],
                "quantity": parsed["quantity"],
                "unit": parsed["unit"],
                "category": category,
                "recipe_id": recipe_record["id"],
                "recipe_name": recipe_name
            })

    return grocery_items


def create_grocery_items(grocery_items):
    """Create grocery items in Airtable."""
    logger.info("\n" + "=" * 60)
    logger.info("Creating Grocery Items")
    logger.info("=" * 60)

    try:
        api = Api(Config.AIRTABLE_ACCESS_TOKEN)
        table = api.table(Config.AIRTABLE_BASE_ID, GROCERY_ITEMS_TABLE_ID)

        # Prepare records for batch creation
        records_to_create = []

        for item in grocery_items:
            record = {
                "Name": item["name"],
                "Quantity": item["quantity"],
                "Unit": item["unit"],
                "Category": item["category"],
                "Recipe": [item["recipe_id"]],
                "Notes": f"From recipe: {item['recipe_name']}"
            }
            records_to_create.append(record)

        logger.info(f"\nCreating {len(records_to_create)} grocery items...")

        # Batch create (max 10 at a time)
        batch_size = 10
        created_count = 0
        failed_count = 0

        for i in range(0, len(records_to_create), batch_size):
            batch = records_to_create[i:i + batch_size]
            try:
                table.batch_create(batch)
                created_count += len(batch)
                logger.info(f"  Created items {i+1}-{min(i+batch_size, len(records_to_create))}")
            except Exception as e:
                logger.error(f"  Failed batch {i+1}-{min(i+batch_size, len(records_to_create))}: {e}")
                failed_count += len(batch)

        logger.info(f"\nResults:")
        logger.info(f"  Successfully created: {created_count}")
        logger.info(f"  Failed: {failed_count}")

        return created_count > 0

    except Exception as e:
        logger.error(f"Error creating grocery items: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("Populate Grocery Items from Recipes")
    logger.info("=" * 60)

    # Step 1: Fetch recipes
    recipes = get_recipes_with_ingredients()
    if not recipes:
        logger.error("No recipes found")
        return 1

    # Step 2: Parse ingredients from all recipes
    logger.info("\n" + "=" * 60)
    logger.info("Parsing Ingredients")
    logger.info("=" * 60)

    all_grocery_items = []
    for recipe in recipes:
        recipe_name = recipe.get("fields", {}).get("Name", "Unknown")
        logger.info(f"\nParsing: {recipe_name}")

        items = parse_recipe_ingredients(recipe)
        logger.info(f"  Found {len(items)} ingredients")

        all_grocery_items.extend(items)

    logger.info(f"\nTotal grocery items parsed: {len(all_grocery_items)}")

    # Show category breakdown
    category_counts = {}
    for item in all_grocery_items:
        category = item["category"]
        category_counts[category] = category_counts.get(category, 0) + 1

    logger.info("\nCategory breakdown:")
    for category, count in sorted(category_counts.items()):
        logger.info(f"  {category}: {count} items")

    # Step 3: Create grocery items in Airtable
    if not create_grocery_items(all_grocery_items):
        logger.error("Failed to create grocery items")
        return 1

    logger.info("\n" + "=" * 60)
    logger.info("Complete!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("1. Review grocery items in Airtable Grocery Items table")
    logger.info("2. Verify recipe links are correct")
    logger.info("3. Adjust categories if needed")
    logger.info("4. Check that units are parsed correctly")

    return 0


if __name__ == "__main__":
    sys.exit(main())
