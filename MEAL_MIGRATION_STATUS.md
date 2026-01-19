# Meal System Migration Status

## Overview
Migration plan created for moving meal recipes, meal planning, and grocery system from Notion to Airtable.

---

## ✅ Completed Tasks

### 1. Migration Plan Created
- **File**: `MEAL_MIGRATION_PLAN.md`
- **Status**: Complete
- **Details**: Comprehensive plan with table schemas, field mappings, implementation scripts, and execution order

### 2. Airtable Table Schemas Setup
- **Script**: `setup_meal_schemas.py`
- **Status**: Complete ✅
- **Results**:
  - **Recipes Table**: 24 fields created (tbl0R6ndVQvvLzEoN)
  - **Meal Plans Table**: 8 fields created (tblXeRfKofAHtbt6e)
  - **Planned Meals Table**: 10 fields created (tblTAfTWjHWwjV30Y)
  - **Grocery Items Table**: 11 fields created (tblsqM5S4HfIFsDFD)

### 3. Discovery Script Created
- **Script**: `discover_meal_databases.py`
- **Status**: Created, ready to run after Notion access is granted

---

## 🔴 Blocked Tasks

### Notion Database Access Required

The following Notion databases need to be shared with your integration:

1. **Recipes Database**
   - URL: https://www.notion.so/556a9ac89c5e4113a4245936d319e522
   - Status: Not accessible ❌

2. **Meal Planning Database**
   - URL: https://www.notion.so/332af6a461e44cf598311cc6546bacaa
   - Status: Not accessible ❌

3. **Grocery List Database**
   - URL: https://www.notion.so/e0b69d97cfe34bf88ce0b7007bc5f406
   - Status: Not accessible ❌

**How to share databases with integration:**
1. Open each database in Notion
2. Click the "..." menu (top right)
3. Select "Connections"
4. Add your integration (the one with token: `ntn_388816407844...`)

---

## 📋 Pending Tasks

Once Notion databases are shared, the following scripts need to be created and run:

### 1. Discovery (Ready)
- [ ] Share Notion databases with integration
- [ ] Run `discover_meal_databases.py` to find actual data source IDs
- [ ] Update `MEAL_MIGRATION_PLAN.md` with discovered IDs

### 2. Migration Scripts to Create
- [ ] `migrate_recipes.py` - Export and import recipe data
- [ ] `migrate_meal_plans.py` - Export and import meal plans
- [ ] `migrate_planned_meals.py` - Export and import planned meals with links
- [ ] `migrate_grocery_items.py` - Export and import grocery items
- [ ] `verify_meal_migration.py` - Verify data integrity

### 3. Post-Migration
- [ ] Verify all records imported correctly
- [ ] Check relationship links (Day, Week, Recipe, Meal Plan)
- [ ] Review backup JSON files
- [ ] Configure Airtable views
- [ ] Set up any automations

---

## Table Schema Summary

### Recipes (24 fields)
- Basic info: Name, Category, Cuisine, Difficulty
- Timing: Prep Time, Cook Time, Total Time, Servings
- Content: Ingredients, Instructions, Notes, Tags
- Nutrition: Calories, Protein, Carbs, Fat, Fiber
- Metadata: Rating, Last Made, Source, Source URL, Image URL, Cost Per Serving, Active

### Meal Plans (8 fields)
- Basic info: Name, Start Date, End Date, Status
- Links: Week (to Week table)
- Planning: Notes, Grocery List Generated, Total Estimated Cost

### Planned Meals (10 fields)
- Basic info: Name, Date, Meal Type, Servings, Status
- Links: Day (to Day table), Meal Plan (to Meal Plans table), Recipe (to Recipes table)
- Metadata: Notes, Actual Cost

### Grocery Items (11 fields)
- Basic info: Name, Category, Quantity, Unit, Store
- Links: Meal Plan (to Meal Plans table), Recipe (to Recipes table)
- Shopping: Purchased, Estimated Cost, Actual Cost, Notes

---

## Next Steps

**Immediate action required:**
1. Share the three Notion databases with your integration
2. Run `python discover_meal_databases.py` to find database IDs
3. Once IDs are discovered, I can create the migration scripts

**After database access is granted:**
The migration will follow this order:
1. Recipes (foundation - no dependencies)
2. Meal Plans (links to Week table)
3. Planned Meals (links to Recipes, Meal Plans, Day)
4. Grocery Items (links to Recipes, Meal Plans)
5. Verification

---

## File References

- Migration Plan: `MEAL_MIGRATION_PLAN.md`
- Schema Setup: `setup_meal_schemas.py`
- Discovery: `discover_meal_databases.py`
- Environment: `.env` (table names configured)
- Status: `MEAL_MIGRATION_STATUS.md` (this file)

---

## Airtable Table IDs

For reference when creating migration scripts:

```python
RECIPES_TABLE_ID = "tbl0R6ndVQvvLzEoN"
MEAL_PLANS_TABLE_ID = "tblXeRfKofAHtbt6e"
PLANNED_MEALS_TABLE_ID = "tblTAfTWjHWwjV30Y"
GROCERY_ITEMS_TABLE_ID = "tblsqM5S4HfIFsDFD"
DAY_TABLE_ID = "tblHMwUnVg8bA1xoP"
WEEK_TABLE_ID = "tbl2B7ecl7heYiKha"
```

---

Last Updated: 2026-01-18
