# MCP Server Function Tests

This document contains test commands and expected behaviors for all MCP server functions.

## Test Date: 2026-01-21

## Test 1: get_today_overview

**Command:**
```
Use the Airtable MCP get_today_overview function
```

**Expected Result:**
- Returns today's date (2026-01-21)
- Lists all calendar events for today sorted by start time
- Shows any tasks (Tasks table is currently empty)
- Shows training plans linked to today's Day record
- Shows training sessions linked to today's Day record
- Shows planned meals for today
- Shows health metrics for today (if available)

**Success Criteria:**
- No field name errors
- All sections return data or empty arrays (no crashes)
- Dates are in YYYY-MM-DD format

---

## Test 2: get_week_overview (current week)

**Command:**
```
Use the Airtable MCP get_week_overview function with week_offset: 0
```

**Expected Result:**
- Returns week_start and week_end dates for current week (Monday to Sunday)
- Groups calendar events by date
- Lists all tasks
- Shows training plans for the week
- Shows training sessions for the week
- Groups planned meals by date
- Includes summary with total counts

**Success Criteria:**
- No field name errors
- Date grouping works correctly
- Summary counts are accurate
- Week starts on Monday

---

## Test 3: get_complete_schedule (single day)

**Command:**
```
Use the Airtable MCP get_complete_schedule function with start_date: "2026-01-21"
```

**Expected Result:**
- Returns complete data for 2026-01-21
- Includes:
  - Date and weekday
  - All calendar events sorted by time
  - Training plans for the day
  - Training sessions for the day
  - Planned meals for the day
  - Health metrics for the day

**Success Criteria:**
- All data retrieved in single call
- No field name errors
- Comprehensive daily view

---

## Test 4: get_complete_schedule (date range)

**Command:**
```
Use the Airtable MCP get_complete_schedule function with start_date: "2026-01-20" and end_date: "2026-01-26"
```

**Expected Result:**
- Returns array of day objects, one for each date
- Each day includes all data types
- Days are sorted chronologically

**Success Criteria:**
- Multiple days returned
- Each day has complete data
- Chronological ordering

---

## Test 5: get_calendar_events

**Command:**
```
Use the Airtable MCP get_calendar_events function with start_date: "2026-01-20" and end_date: "2026-01-26"
```

**Expected Result:**
- Returns calendar events for the week
- Sorted by Date, then Start Time
- Includes all event fields (Name, Title, Location, etc.)

**Success Criteria:**
- Correct filtering by date range
- Proper sorting
- No field name errors

---

## Test 6: get_tasks

**Command:**
```
Use the Airtable MCP get_tasks function with limit: 50
```

**Expected Result:**
- Returns up to 50 tasks
- Currently, Tasks table is empty, so should return empty array or empty objects

**Success Criteria:**
- No crashes
- Handles empty table gracefully

---

## Test 7: get_training_sessions

**Command:**
```
Use the Airtable MCP get_training_sessions function with start_date: "2026-01-01" and end_date: "2026-01-15"
```

**Expected Result:**
- Returns training sessions linked to Day records in the date range
- Includes Activity Type, Name, Duration, Training Effect, etc.
- Properly filters by Day record linkage

**Success Criteria:**
- Correct date filtering via Day records
- All training session fields included
- No field name errors

---

## Test 8: get_training_plans

**Command:**
```
Use the Airtable MCP get_training_plans function with start_date: "2026-05-26" and end_date: "2026-06-02"
```

**Expected Result:**
- Returns training plans linked to Day records in the date range
- Includes Workout Type, Description, Status, Priority, etc.
- Properly filters by Day record linkage

**Success Criteria:**
- Correct date filtering via Day records
- All training plan fields included
- No field name errors

---

## Test 9: get_health_metrics

**Command:**
```
Use the Airtable MCP get_health_metrics function with start_date: "2026-01-01" and end_date: "2026-01-07"
```

**Expected Result:**
- Returns health metrics records where Name field is in date range
- Includes Steps, Resting HR, Sleep Score, Active Calories, etc.
- Sorted by Name (date) ascending

**Success Criteria:**
- Correct filtering by Name field (date format)
- Proper sorting
- All health metric fields included

---

## Test 10: get_planned_meals

**Command:**
```
Use the Airtable MCP get_planned_meals function with start_date: "2026-01-20" and end_date: "2026-01-26"
```

**Expected Result:**
- Returns planned meals for the week
- Includes Name, Date, Meal Type, Recipe link, Servings, Status
- Sorted by Date

**Success Criteria:**
- Correct date filtering
- Proper sorting
- All meal fields included

---

## Test 11: get_recipes

**Command:**
```
Use the Airtable MCP get_recipes function with search: "salmon" and limit: 10
```

**Expected Result:**
- Returns recipes where Name contains "salmon" (case-insensitive)
- Maximum 10 results
- Includes recipe details (Ingredients, Instructions, Nutrition, etc.)

**Success Criteria:**
- Case-insensitive search works
- Limit is respected
- All recipe fields included

---

## Test 12: get_projects

**Command:**
```
Use the Airtable MCP get_projects function with limit: 50
```

**Expected Result:**
- Returns up to 50 projects
- Includes Name, Status, Classes link, Due Date link

**Success Criteria:**
- Correct field retrieval
- No field name errors
- Linked records shown as arrays

---

## Test 13: get_classes

**Command:**
```
Use the Airtable MCP get_classes function
```

**Expected Result:**
- Returns all classes
- Includes Class, Description, Semester, Grade, Credits, etc.

**Success Criteria:**
- All classes returned
- All fields included
- No errors

---

## Common Issues to Check

### Field Name Issues (FIXED)
- ✅ Calendar Events: Uses `{Date}` field correctly
- ✅ Calendar Events: Uses `{Start Time}` for sorting
- ✅ Training Plans: Filters by `{Day}` linked records
- ✅ Training Sessions: Filters by `{Day}` linked records
- ✅ Health Metrics: Uses `{Name}` field (which is in date format)
- ✅ Planned Meals: Uses `{Date}` field correctly
- ✅ Tasks: Currently empty table, handled gracefully

### Date Filtering
- ✅ Day table: Uses `{Day}` field for date matching
- ✅ Date comparisons use YYYY-MM-DD format
- ✅ Linked record filtering uses SEARCH() and ARRAYJOIN()

### New Features Added
- ✅ `get_complete_schedule`: Unified data retrieval function
- ✅ `get_training_plans`: New function for training plans
- ✅ Improved `get_week_overview`: Now groups by date and includes summary
- ✅ Better date range filtering for training sessions and plans

---

## Testing Checklist

- [ ] Test 1: get_today_overview
- [ ] Test 2: get_week_overview (current week)
- [ ] Test 3: get_complete_schedule (single day)
- [ ] Test 4: get_complete_schedule (date range)
- [ ] Test 5: get_calendar_events
- [ ] Test 6: get_tasks
- [ ] Test 7: get_training_sessions
- [ ] Test 8: get_training_plans
- [ ] Test 9: get_health_metrics
- [ ] Test 10: get_planned_meals
- [ ] Test 11: get_recipes
- [ ] Test 12: get_projects
- [ ] Test 13: get_classes

---

## Notes

- All tests should complete without "Unknown field name" errors
- Empty results are okay if no data exists for that date/criteria
- The Tasks table is currently empty (no fields), so task-related tests will return empty arrays
