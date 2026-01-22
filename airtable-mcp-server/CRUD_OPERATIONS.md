# Airtable MCP Server - CRUD Operations Guide

**Date:** January 21, 2026
**Version:** 2.0

## Overview

The Airtable MCP server now supports full CRUD (Create, Read, Update, Delete) operations for key tables in your personal planning system. This guide documents all available create, update, and delete functions.

## Available Operations

### Tasks

#### Create Task
```typescript
create_task({
  name: "Complete project proposal",
  category: "Work"  // optional
})
```

**Parameters:**
- `name` (required): Task name
- `category` (optional): Task category

**Returns:** Created record with ID and all fields

#### Update Task
```typescript
update_task({
  record_id: "recXXXXXXXXXXXXX",
  name: "Updated task name",  // optional
  category: "Personal Project"  // optional
})
```

**Parameters:**
- `record_id` (required): Airtable record ID
- `name` (optional): New task name
- `category` (optional): New category

**Returns:** Updated record with ID and all fields

#### Delete Task
```typescript
delete_task({
  record_id: "recXXXXXXXXXXXXX"
})
```

**Parameters:**
- `record_id` (required): Airtable record ID

**Returns:** Success message with deleted record ID

---

### Planned Meals

#### Create Planned Meal
```typescript
create_planned_meal({
  name: "Grilled Chicken Salad",
  date: "2026-01-25",
  meal_type: "Lunch",  // optional: Breakfast, Lunch, Dinner, Snack
  recipe_ids: ["recYYYYYYYYYYYYY"],  // optional: array of recipe IDs
  servings: 1,  // optional
  status: "Planned",  // optional: Planned, Prepared, Eaten
  notes: "Extra protein for post-workout"  // optional
})
```

**Parameters:**
- `name` (required): Meal name
- `date` (required): Date in YYYY-MM-DD format
- `meal_type` (optional): Breakfast, Lunch, Dinner, or Snack
- `recipe_ids` (optional): Array of recipe record IDs to link
- `servings` (optional): Number of servings
- `status` (optional): Planned, Prepared, or Eaten
- `notes` (optional): Additional notes

**Automatic Behavior:**
- Automatically links to Day record for the specified date (if it exists)

**Returns:** Created record with ID and all fields

#### Update Planned Meal
```typescript
update_planned_meal({
  record_id: "recXXXXXXXXXXXXX",
  name: "Updated meal name",  // optional
  date: "2026-01-26",  // optional
  meal_type: "Dinner",  // optional
  recipe_ids: ["recYYYYYYYYYYYYY", "recZZZZZZZZZZZZZ"],  // optional
  servings: 2,  // optional
  status: "Prepared",  // optional
  notes: "Made ahead of time"  // optional
})
```

**Parameters:**
- `record_id` (required): Airtable record ID
- All other parameters optional (only update what you specify)

**Automatic Behavior:**
- If date is updated, automatically updates Day link

**Returns:** Updated record with ID and all fields

#### Delete Planned Meal
```typescript
delete_planned_meal({
  record_id: "recXXXXXXXXXXXXX"
})
```

**Parameters:**
- `record_id` (required): Airtable record ID

**Returns:** Success message with deleted record ID

---

### Calendar Events

#### Create Calendar Event
```typescript
create_calendar_event({
  name: "Team Meeting",
  date: "2026-01-25",
  start_time: "2026-01-25T14:00:00.000Z",  // optional, ISO 8601 format
  end_time: "2026-01-25T15:00:00.000Z",  // optional, ISO 8601 format
  location: "Conference Room A",  // optional
  description: "Quarterly planning meeting",  // optional
  calendar: "Work",  // optional: Personal, School and Research, Work, etc.
  all_day: false  // optional, default false
})
```

**Parameters:**
- `name` (required): Event name
- `date` (required): Date in YYYY-MM-DD format
- `start_time` (optional): Start time in ISO 8601 format
- `end_time` (optional): End time in ISO 8601 format
- `location` (optional): Event location
- `description` (optional): Event description
- `calendar` (optional): Calendar name
- `all_day` (optional): Boolean for all-day events

**Automatic Behavior:**
- Automatically sets Title field same as Name
- Automatically links to Day record for the specified date (if it exists)

**Returns:** Created record with ID and all fields

#### Update Calendar Event
```typescript
update_calendar_event({
  record_id: "recXXXXXXXXXXXXX",
  name: "Updated event name",  // optional
  date: "2026-01-26",  // optional
  start_time: "2026-01-26T15:00:00.000Z",  // optional
  end_time: "2026-01-26T16:00:00.000Z",  // optional
  location: "Virtual - Zoom",  // optional
  description: "Updated description",  // optional
  calendar: "Personal",  // optional
  all_day: true  // optional
})
```

**Parameters:**
- `record_id` (required): Airtable record ID
- All other parameters optional (only update what you specify)

**Automatic Behavior:**
- If name is updated, Title is also updated
- If date is updated, automatically updates Day link

**Returns:** Updated record with ID and all fields

#### Delete Calendar Event
```typescript
delete_calendar_event({
  record_id: "recXXXXXXXXXXXXX"
})
```

**Parameters:**
- `record_id` (required): Airtable record ID

**Returns:** Success message with deleted record ID

---

### Recipes

#### Create Recipe
```typescript
create_recipe({
  name: "Mediterranean Quinoa Bowl"
})
```

**Parameters:**
- `name` (required): Recipe name

**Note:** The recipe table may have additional fields (ingredients, instructions, etc.) that can only be edited in Airtable directly. This function creates the basic recipe record.

**Returns:** Created record with ID and all fields

#### Update Recipe
```typescript
update_recipe({
  record_id: "recXXXXXXXXXXXXX",
  name: "Updated recipe name"
})
```

**Parameters:**
- `record_id` (required): Airtable record ID
- `name` (optional): New recipe name

**Returns:** Updated record with ID and all fields

#### Delete Recipe
```typescript
delete_recipe({
  record_id: "recXXXXXXXXXXXXX"
})
```

**Parameters:**
- `record_id` (required): Airtable record ID

**Warning:** Deleting a recipe may affect planned meals that reference it. Consider checking for linked meals before deleting.

**Returns:** Success message with deleted record ID

---

## Usage Examples

### Example 1: Plan a Week of Meals

```typescript
// First, search for existing recipes
get_recipes({ search: "chicken" })

// Create meal for Monday
create_planned_meal({
  name: "Grilled Chicken with Vegetables",
  date: "2026-01-27",
  meal_type: "Dinner",
  recipe_ids: ["recABC123"],
  servings: 1,
  status: "Planned"
})

// Create meal for Tuesday
create_planned_meal({
  name: "Chicken Salad (Leftover)",
  date: "2026-01-28",
  meal_type: "Lunch",
  servings: 1,
  status: "Planned",
  notes: "Using leftover chicken from Monday"
})
```

### Example 2: Update Task Status

```typescript
// First, get all tasks to find the one to update
get_tasks({ limit: 20 })

// Update the task
update_task({
  record_id: "recXYZ789",
  category: "Completed"
})
```

### Example 3: Schedule a Recurring Event

```typescript
// Create event for this week
create_calendar_event({
  name: "Weekly Team Standup",
  date: "2026-01-27",
  start_time: "2026-01-27T09:00:00.000Z",
  end_time: "2026-01-27T09:30:00.000Z",
  location: "Virtual - Teams",
  calendar: "Work"
})

// Create for next week
create_calendar_event({
  name: "Weekly Team Standup",
  date: "2026-02-03",
  start_time: "2026-02-03T09:00:00.000Z",
  end_time: "2026-02-03T09:30:00.000Z",
  location: "Virtual - Teams",
  calendar: "Work"
})
```

### Example 4: Create Recipe and Plan Meal

```typescript
// Create a new recipe
create_recipe({
  name: "Spicy Thai Noodles"
})
// Returns: { id: "recNEW123", fields: { Name: "Spicy Thai Noodles" } }

// Plan a meal using the new recipe
create_planned_meal({
  name: "Spicy Thai Noodles",
  date: "2026-01-29",
  meal_type: "Dinner",
  recipe_ids: ["recNEW123"],
  servings: 2
})
```

### Example 5: Meal Prep Workflow

```typescript
// 1. Get this week's planned meals
get_planned_meals({
  start_date: "2026-01-27",
  end_date: "2026-02-02"
})

// 2. Update meals to "Prepared" as you prep them
update_planned_meal({
  record_id: "recMEAL1",
  status: "Prepared"
})

update_planned_meal({
  record_id: "recMEAL2",
  status: "Prepared"
})

// 3. Add a last-minute snack
create_planned_meal({
  name: "Protein Shake",
  date: "2026-01-27",
  meal_type: "Snack",
  servings: 1,
  status: "Prepared"
})
```

---

## Getting Record IDs

To update or delete records, you need their record IDs. You can get these by using the read functions:

```typescript
// Get tasks and their IDs
get_tasks({ limit: 50 })

// Get calendar events for a date range
get_calendar_events({
  start_date: "2026-01-27",
  end_date: "2026-02-02"
})

// Get planned meals
get_planned_meals({
  start_date: "2026-01-27",
  end_date: "2026-02-02"
})

// Search recipes
get_recipes({ search: "chicken" })
```

All read functions return records with their IDs in the format `recXXXXXXXXXXXXX`.

---

## Error Handling

All operations return errors in a consistent format:

```json
{
  "error": "Error message here",
  "details": "Additional error details if available"
}
```

### Common Errors

1. **Invalid record ID**
   - Error: "Record not found"
   - Solution: Verify the record ID exists using a get function

2. **Invalid date format**
   - Error: "Invalid date format"
   - Solution: Use YYYY-MM-DD format (e.g., "2026-01-27")

3. **Invalid field value**
   - Error: "Unknown field name" or "Invalid value"
   - Solution: Check FIELD_MAPPING.md for valid field names and types

4. **Missing required field**
   - Error: "Missing required field"
   - Solution: Ensure all required parameters are provided

5. **Permission denied**
   - Error: "You are not authorized to perform this operation"
   - Solution: Check API key permissions in Airtable

---

## Best Practices

### 1. Verify Before Delete

Always retrieve and verify records before deleting:

```typescript
// Get the record first
get_tasks({ limit: 100 })

// Review the output, then delete
delete_task({ record_id: "recXXX" })
```

### 2. Batch Operations

For multiple operations, group them logically:

```typescript
// Plan all breakfast meals for the week
create_planned_meal({ name: "Oatmeal", date: "2026-01-27", meal_type: "Breakfast" })
create_planned_meal({ name: "Smoothie", date: "2026-01-28", meal_type: "Breakfast" })
create_planned_meal({ name: "Eggs", date: "2026-01-29", meal_type: "Breakfast" })
```

### 3. Use Descriptive Names

Make names clear and searchable:

```typescript
// Good
create_task({ name: "Review Q1 budget report", category: "Work" })

// Less helpful
create_task({ name: "Review", category: "Work" })
```

### 4. Link to Recipes

When planning meals, link to recipe records for consistency:

```typescript
// First, find the recipe
get_recipes({ search: "salmon" })

// Then link it
create_planned_meal({
  name: "Baked Salmon with Vegetables",
  date: "2026-01-27",
  recipe_ids: ["recSALMON123"],
  meal_type: "Dinner"
})
```

### 5. Update Status as You Go

Keep your data current by updating statuses:

```typescript
// When you prepare a meal
update_planned_meal({
  record_id: "recMEAL1",
  status: "Prepared"
})

// When you complete a task
update_task({
  record_id: "recTASK1",
  category: "Completed"  // If you add a Status field later
})
```

### 6. Use Notes for Context

Add notes to provide context for future reference:

```typescript
create_planned_meal({
  name: "High Protein Bowl",
  date: "2026-01-27",
  meal_type: "Lunch",
  notes: "Post-workout meal - double protein portion"
})
```

---

## Future Enhancements

### Planned Additions

1. **Training Plans/Sessions CRUD**
   - Create/update/delete training plans
   - Link to Day records
   - Set activity type, duration, etc.

2. **Health Metrics CRUD**
   - Log sleep, steps, heart rate
   - Update daily metrics

3. **Projects CRUD** (once permissions are resolved)
   - Create and manage projects
   - Link tasks to projects

4. **Batch Operations**
   - Create multiple records at once
   - Bulk update operations

5. **Search and Filter**
   - Advanced search across all tables
   - Filter by multiple criteria

---

## Restart Required

After rebuilding the MCP server, you must restart Claude Code for the new functions to be available:

1. Close Claude Code completely
2. Reopen Claude Code
3. The new CRUD functions will now be available

---

## Testing Checklist

Test each operation to ensure it works:

### Tasks
- [ ] Create a new task
- [ ] Update task name and category
- [ ] Delete a task

### Planned Meals
- [ ] Create a meal without recipe link
- [ ] Create a meal with recipe link
- [ ] Update meal status
- [ ] Delete a meal

### Calendar Events
- [ ] Create an all-day event
- [ ] Create a timed event with start/end
- [ ] Update event location
- [ ] Delete an event

### Recipes
- [ ] Create a new recipe
- [ ] Update recipe name
- [ ] Delete a recipe

---

## Summary

You now have full CRUD capabilities for:
- ✅ Tasks
- ✅ Planned Meals
- ✅ Calendar Events
- ✅ Recipes

These operations enable comprehensive management of your personal planning system directly through Claude Code. Combined with the existing read functions, you can now:

- Plan your entire week
- Track tasks and projects
- Schedule events and meetings
- Manage meal planning and prep
- Organize recipes

**Next Step:** Restart Claude Code to start using these new functions!
