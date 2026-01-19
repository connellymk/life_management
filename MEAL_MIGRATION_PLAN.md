# Meal System Migration Plan: Notion → Airtable

## Overview
Migrate the meal recipes, meal planning, and grocery system from Notion to Airtable, creating necessary table structures and importing all data.

---

## Environment Configuration

### Airtable
- **Base ID**: `appKYFUTDs7tDg4Wr` (same base)
- **Recipes Table**: `AIRTABLE_RECIPES` (from .env)
- **Meal Plans Table**: `AIRTABLE_MEAL_PLANS` (from .env)
- **Planned Meals Table**: `AIRTABLE_PLANNED_MEALS` (from .env)
- **Grocery Items Table**: `AIRTABLE_GROCERY_ITEMS` (from .env)

### Notion Database URLs
- **Recipes**: `https://www.notion.so/556a9ac89c5e4113a4245936d319e522?v=c926f1cc86e947d58602a11c77e3a278`
- **Meal Planning**: `https://www.notion.so/332af6a461e44cf598311cc6546bacaa?v=06ca48ddb1d24b69a83d93b11476c62d`
- **Grocery List**: `https://www.notion.so/e0b69d97cfe34bf88ce0b7007bc5f406?v=6f462e9dadb64c329e50b8411481246d`

---

## Discovery Phase

### Step 1: Identify Notion Data Source IDs

Run discovery script to find actual data source IDs:

```python
# Search for meal-related databases
notion.search(filter={"property": "object", "value": "data_source"})
```

Expected databases:
- Recipes (name might be "Recipes", "Recipe Database", etc.)
- Meal Planning / Meal Plans
- Grocery List / Grocery Items

### Step 2: Analyze Notion Schema

For each database, fetch schema to understand:
- Property names and types
- Multi-select options
- Number formats
- Date formats
- Relation fields between databases

---

## Table Schemas

### Table 1: Recipes

**Purpose**: Store recipe information including ingredients, instructions, and nutritional data

| Field Name | Type | Options | Description |
|------------|------|---------|-------------|
| Name | singleLineText | (primary) | Recipe name |
| Category | singleSelect | choices: Breakfast, Lunch, Dinner, Snack, Dessert, Beverage | Meal category |
| Cuisine | singleSelect | choices: American, Italian, Mexican, Asian, Mediterranean, Indian, Other | Cuisine type |
| Prep Time | number | precision: 0 | Preparation time in minutes |
| Cook Time | number | precision: 0 | Cooking time in minutes |
| Total Time | number | precision: 0 | Total time in minutes (auto-calculated) |
| Servings | number | precision: 0 | Number of servings |
| Difficulty | singleSelect | choices: Easy, Medium, Hard | Recipe difficulty |
| Ingredients | multilineText | | List of ingredients with quantities |
| Instructions | multilineText | | Step-by-step cooking instructions |
| Notes | multilineText | | Additional notes, substitutions |
| Tags | multipleSelects | choices: Healthy, Quick, Budget-Friendly, Meal Prep, Freezer-Friendly, One-Pot, Slow Cooker, Instant Pot, Vegetarian, Vegan, Gluten-Free, Dairy-Free, Low-Carb, High-Protein | Recipe tags |
| Calories | number | precision: 0 | Calories per serving |
| Protein | number | precision: 1 | Protein in grams per serving |
| Carbs | number | precision: 1 | Carbohydrates in grams per serving |
| Fat | number | precision: 1 | Fat in grams per serving |
| Fiber | number | precision: 1 | Fiber in grams per serving |
| Rating | rating | max: 5 | Personal recipe rating |
| Last Made | date | dateFormat: "iso" | Last time recipe was made |
| Source | singleLineText | | Recipe source (website, book, etc.) |
| Source URL | url | | Link to original recipe |
| Image URL | url | | Link to recipe image |
| Cost Per Serving | number | precision: 2 | Estimated cost per serving |
| Active | checkbox | | Whether recipe is in active rotation |

### Table 2: Meal Plans

**Purpose**: Weekly or monthly meal planning structure

| Field Name | Type | Options | Description |
|------------|------|---------|-------------|
| Name | singleLineText | (primary) | Meal plan name (e.g., "Week of Jan 20, 2026") |
| Start Date | date | dateFormat: "iso" | Plan start date |
| End Date | date | dateFormat: "iso" | Plan end date |
| Week | multipleRecordLinks | links to: Week table (tblHMwUnVg8bA1xoP) | Link to existing week record |
| Status | singleSelect | choices: Planning, Active, Completed | Plan status |
| Notes | multilineText | | Planning notes |
| Grocery List Generated | checkbox | | Whether grocery list was created |
| Total Estimated Cost | number | precision: 2 | Total cost for the plan |

### Table 3: Planned Meals

**Purpose**: Individual meals within meal plans

| Field Name | Type | Options | Description |
|------------|------|---------|-------------|
| Name | singleLineText | (primary) | Meal name (auto-generated from recipe) |
| Date | date | dateFormat: "iso" | Meal date |
| Day | linkedRecords | links to: Day table | Link to day record |
| Meal Plan | linkedRecords | links to: Meal Plans | Link to meal plan |
| Meal Type | singleSelect | choices: Breakfast, Lunch, Dinner, Snack | Type of meal |
| Recipe | linkedRecords | links to: Recipes | Link to recipe |
| Servings | number | precision: 0 | Number of servings to prepare |
| Status | singleSelect | choices: Planned, Prepared, Skipped | Meal status |
| Notes | multilineText | | Meal-specific notes |
| Actual Cost | number | precision: 2 | Actual cost if tracked |

### Table 4: Grocery Items

**Purpose**: Grocery shopping list items

| Field Name | Type | Options | Description |
|------------|------|---------|-------------|
| Name | singleLineText | (primary) | Item name |
| Category | singleSelect | choices: Produce, Meat & Seafood, Dairy & Eggs, Bakery, Pantry, Frozen, Beverages, Snacks, Other | Grocery category |
| Quantity | singleLineText | | Quantity needed |
| Unit | singleSelect | choices: lb, oz, kg, g, cup, tbsp, tsp, whole, bunch, package, can, bottle | Measurement unit |
| Meal Plan | linkedRecords | links to: Meal Plans | Associated meal plan |
| Recipe | linkedRecords | links to: Recipes | Associated recipe |
| Store | singleSelect | choices: Grocery Store, Farmers Market, Bulk Store, Specialty Store, Online | Where to buy |
| Purchased | checkbox | | Whether item was purchased |
| Estimated Cost | number | precision: 2 | Expected cost |
| Actual Cost | number | precision: 2 | Actual cost paid |
| Notes | singleLineText | | Item notes |

---

## Data Migration Strategy

### Phase 1: Schema Setup (Automated)

1. **Discover Notion data source IDs** for all three databases
2. **Fetch existing Airtable table schemas**
3. **Create missing fields** in Airtable tables via API
4. **Verify schema compatibility**

### Phase 2: Data Export from Notion (Automated)

1. **Export Recipes**
   - Query all recipe pages
   - Extract properties
   - Fetch page content for ingredients/instructions
   - Expected: 20-100+ recipes

2. **Export Meal Plans**
   - Query all meal plan records
   - Extract date ranges and metadata
   - Expected: Variable based on usage

3. **Export Planned Meals**
   - Query all planned meal records
   - Extract meal assignments
   - Expected: 50-500+ meals

4. **Export Grocery Items**
   - Query all grocery list items
   - Extract shopping data
   - Expected: Variable based on current lists

### Phase 3: Data Transformation

**Recipe Transformation**:
- Map Notion properties to Airtable fields
- Extract ingredients from page content or property
- Extract instructions from page content
- Handle multi-select tags
- Parse nutritional information
- Default rating to null if not set

**Meal Plan Transformation**:
- Extract date ranges
- Calculate week associations
- Map status values

**Planned Meals Transformation**:
- Link to recipes (will need recipe name → Airtable ID mapping)
- Link to meal plans (will need plan name → Airtable ID mapping)
- Link to Day table records by date
- Map meal types

**Grocery Items Transformation**:
- Categorize items
- Link to meal plans and recipes
- Handle quantity/unit parsing

### Phase 4: Data Import to Airtable (Automated)

Import order (important for relationships):
1. **Recipes** (no dependencies)
2. **Meal Plans** (links to Week table)
3. **Planned Meals** (links to Recipes, Meal Plans, Day)
4. **Grocery Items** (links to Recipes, Meal Plans)

Use batch operations (10 records per batch) with error handling.

### Phase 5: Link Creation (Automated)

After initial import, create relationships:
1. Link Planned Meals → Recipes (by recipe name matching)
2. Link Planned Meals → Meal Plans (by plan name matching)
3. Link Planned Meals → Day (by date matching)
4. Link Meal Plans → Week (by date range)
5. Link Grocery Items → Recipes (by recipe reference)
6. Link Grocery Items → Meal Plans (by plan reference)

---

## Field Mapping Details

### Recipes: Notion → Airtable

| Notion Property | Notion Type | Airtable Field | Transformation Notes |
|-----------------|-------------|----------------|---------------------|
| Name | title | Name | Direct copy |
| Category | select | Category | Map to valid options |
| Cuisine | select | Cuisine | Map to valid options |
| Prep Time | number | Prep Time | Direct copy |
| Cook Time | number | Cook Time | Direct copy |
| Servings | number | Servings | Direct copy |
| Difficulty | select | Difficulty | Map to valid options |
| Ingredients | rich_text or page content | Ingredients | Extract from page blocks or property |
| Instructions | page content | Instructions | Extract from page blocks |
| Notes | rich_text | Notes | Concatenate text |
| Tags | multi_select | Tags | Map array of tags |
| Calories | number | Calories | Direct copy |
| Protein | number | Protein | Direct copy |
| Carbs | number | Carbs | Direct copy |
| Fat | number | Fat | Direct copy |
| Rating | number or select | Rating | Convert to 1-5 scale |
| Last Made | date | Last Made | Extract start date |
| Source | rich_text | Source | Direct copy |
| Source URL | url | Source URL | Direct copy |

### Meal Plans: Notion → Airtable

| Notion Property | Notion Type | Airtable Field | Transformation Notes |
|-----------------|-------------|----------------|---------------------|
| Name | title | Name | Direct copy |
| Start Date | date | Start Date | Extract start |
| End Date | date | End Date | Extract end or calculate |
| Status | select | Status | Map to valid options |
| Notes | rich_text | Notes | Concatenate text |

### Planned Meals: Notion → Airtable

| Notion Property | Notion Type | Airtable Field | Transformation Notes |
|-----------------|-------------|----------------|---------------------|
| Name | title | Name | Direct copy |
| Date | date | Date | Extract start date |
| Meal Type | select | Meal Type | Map to valid options |
| Recipe | relation | Recipe | Link after recipes imported |
| Servings | number | Servings | Direct copy |
| Status | select | Status | Map to valid options |
| Notes | rich_text | Notes | Concatenate text |

### Grocery Items: Notion → Airtable

| Notion Property | Notion Type | Airtable Field | Transformation Notes |
|-----------------|-------------|----------------|---------------------|
| Name | title | Name | Direct copy |
| Category | select | Category | Map to valid options |
| Quantity | rich_text or number | Quantity | Parse to string |
| Unit | select | Unit | Map to valid options |
| Purchased | checkbox | Purchased | Direct copy |
| Notes | rich_text | Notes | Concatenate text |

---

## Implementation Scripts

### Script 1: `discover_meal_databases.py`
- Search Notion for meal-related databases
- Output data source IDs
- Display schemas

### Script 2: `setup_meal_schemas.py`
- Create/update Airtable table schemas
- Add missing fields
- Verify field types

### Script 3: `migrate_recipes.py`
- Export recipes from Notion
- Transform data
- Import to Airtable Recipes table
- Create backup JSON

### Script 4: `migrate_meal_plans.py`
- Export meal plans from Notion
- Transform data
- Import to Airtable Meal Plans table
- Create Week associations
- Create backup JSON

### Script 5: `migrate_planned_meals.py`
- Export planned meals from Notion
- Transform data
- Import to Airtable Planned Meals table
- Link to Recipes, Meal Plans, and Days
- Create backup JSON

### Script 6: `migrate_grocery_items.py`
- Export grocery items from Notion
- Transform data
- Import to Airtable Grocery Items table
- Link to Recipes and Meal Plans
- Create backup JSON

### Script 7: `verify_meal_migration.py`
- Verify record counts
- Check field populations
- Validate relationships
- Generate migration report

---

## Execution Order

1. **Discovery**: Run `discover_meal_databases.py` to find data source IDs
2. **Schema Setup**: Run `setup_meal_schemas.py` to prepare Airtable tables
3. **Migrate Recipes**: Run `migrate_recipes.py` (foundation data)
4. **Migrate Meal Plans**: Run `migrate_meal_plans.py`
5. **Migrate Planned Meals**: Run `migrate_planned_meals.py` (requires Recipes + Meal Plans)
6. **Migrate Grocery Items**: Run `migrate_grocery_items.py` (requires Recipes + Meal Plans)
7. **Verification**: Run `verify_meal_migration.py`

---

## Data Validation

### Required Fields
- **Recipes**: Name
- **Meal Plans**: Name, Start Date
- **Planned Meals**: Name, Date, Meal Type
- **Grocery Items**: Name

### Optional Fields
All other fields can be null/empty

### Relationship Validation
- Verify all Planned Meals link to valid Recipes
- Verify all Planned Meals link to valid Meal Plans
- Verify all Planned Meals link to valid Days
- Verify Grocery Items link correctly

---

## Success Criteria

- ✅ All Airtable table schemas updated with required fields
- ✅ All recipes imported successfully
- ✅ All meal plans imported successfully
- ✅ All planned meals imported with proper links
- ✅ All grocery items imported with proper links
- ✅ Backup JSON files created for all data
- ✅ Verification report shows 100% data integrity
- ✅ No data loss from Notion export

---

## Special Considerations

### Ingredients Handling
Recipes may store ingredients in different ways:
- As a Notion property (rich_text or multi_select)
- As page content (blocks)
- Need to check both and prefer page content for detail

### Instructions Handling
Recipe instructions likely stored as page content blocks:
- Fetch all blocks from recipe pages
- Parse paragraph, numbered list, and bulleted list blocks
- Reconstruct as formatted text

### Recipe-Meal Linking
Planned Meals reference Recipes:
- After importing Recipes, create name → Airtable ID mapping
- Use this to populate Recipe links when importing Planned Meals

### Date-Based Linking
Planned Meals link to Day table:
- Use existing Day table records
- Match by date string
- Same approach as Training Plans migration

### Grocery List Generation
Grocery items may be auto-generated from meal plans:
- Some may be manual additions
- Preserve all relationships during migration

---

## Error Handling

For each script:
1. **Validation Errors**: Log validation failures but continue
2. **API Errors**: Retry with exponential backoff
3. **Missing Data**: Log warnings for null required fields
4. **Link Failures**: Log failed relationship creations
5. **Backup**: Save progress before each major operation

---

## Post-Migration Tasks

### Manual Airtable Configuration
1. **Create Views**:
   - Recipes: By Category, By Cuisine, Favorites, Quick Meals
   - Meal Plans: Active Plans, By Week, By Month
   - Planned Meals: By Date, By Meal Type, This Week
   - Grocery Items: By Category, Unpurchased, By Store

2. **Setup Formulas** (if needed):
   - Recipe Total Time = Prep Time + Cook Time
   - Meal Plan cost rollups from Planned Meals
   - Grocery list totals

3. **Configure Automations** (optional):
   - Auto-generate grocery lists from meal plans
   - Send weekly meal plan reminders
   - Update recipe "Last Made" when meal completed

4. **Test Relationships**:
   - Verify recipe links work in Planned Meals
   - Check Day links display correctly
   - Test filtering and sorting

---

## Rollback Plan

If migration fails:
1. Delete imported records from Airtable (use filters by creation date)
2. Restore from backup JSON files
3. Review error logs
4. Fix issues in scripts
5. Re-run migration

---

## Estimated Timeline

- Discovery: 5-10 minutes
- Schema Setup: 10-15 minutes
- Recipe Migration: 10-30 minutes (depends on count + content)
- Meal Plan Migration: 5-10 minutes
- Planned Meals Migration: 10-20 minutes
- Grocery Items Migration: 5-10 minutes
- Verification: 5 minutes
- **Total: ~1-2 hours** (mostly automated)

---

## Notes

- Notion page content extraction is API-intensive
- Consider rate limiting between requests
- Recipe ingredients/instructions may require custom parsing logic
- Some recipes may not have all nutritional data - handle nulls gracefully
- Grocery items may have duplicate names - this is OK
- Keep backup JSON files for future reference
