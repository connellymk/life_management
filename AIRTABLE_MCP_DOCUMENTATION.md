# Airtable MCP Server Documentation

**Version:** 1.0.0
**Last Updated:** January 21, 2026

## Overview

The Airtable Planning MCP Server provides comprehensive access to your personal planning and productivity data stored in Airtable. It integrates calendar events, tasks, training plans/sessions, health metrics, meal planning, and academic information.

## Table of Contents

- [Setup](#setup)
- [Available Functions](#available-functions)
- [Field Name Reference](#field-name-reference)
- [Common Use Cases](#common-use-cases)
- [Troubleshooting](#troubleshooting)

---

## Setup

### Environment Variables

Required in your `.env` file:

```bash
AIRTABLE_ACCESS_TOKEN=your_personal_access_token
AIRTABLE_BASE_ID=your_base_id
```

### Installation

1. Navigate to the MCP server directory:
   ```bash
   cd airtable-mcp-server
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build the server:
   ```bash
   npm run build
   ```

4. The server runs via the Claude CLI integration (configured in your MCP settings)

---

## Available Functions

### 1. get_today_overview

**Description:** Get a comprehensive overview of today's activities, tasks, training, meals, and health metrics.

**Parameters:** None

**Returns:**
```json
{
  "date": "2026-01-21",
  "day_record_id": "recXXXXXXXXXXXXXX",
  "calendar_events": [...],
  "tasks": [...],
  "training_plans": [...],
  "training_sessions": [...],
  "meals": [...],
  "health": {...}
}
```

**Example Usage:**
```
Get my overview for today
```

---

### 2. get_week_overview

**Description:** Get an overview of the current week with all planned activities, grouped by date.

**Parameters:**
- `week_offset` (number, optional): Weeks from current week (0 = current, 1 = next, -1 = last). Default: 0

**Returns:**
```json
{
  "week_start": "2026-01-19",
  "week_end": "2026-01-25",
  "days": {
    "2026-01-20": {
      "calendar_events": [...],
      "planned_meals": [...]
    },
    ...
  },
  "tasks": [...],
  "training_plans": [...],
  "training_sessions": [...],
  "summary": {
    "total_events": 15,
    "total_tasks": 8,
    "total_training_plans": 7,
    "total_training_sessions": 3,
    "total_meals": 21
  }
}
```

**Example Usage:**
```
Show me my week overview
What's planned for next week? (week_offset: 1)
```

---

### 3. get_complete_schedule

**Description:** Get a complete schedule for a specific date or date range with all data in a single call. This is the most comprehensive function.

**Parameters:**
- `start_date` (string, optional): Start date in YYYY-MM-DD format. Default: today
- `end_date` (string, optional): End date in YYYY-MM-DD format. Default: start_date

**Returns:**
```json
{
  "date_range": {
    "start": "2026-01-21",
    "end": "2026-01-21"
  },
  "days": [
    {
      "date": "2026-01-21",
      "weekday": "Wednesday",
      "calendar_events": [...],
      "training_plans": [...],
      "training_sessions": [...],
      "meals": [...],
      "health_metrics": {...}
    }
  ]
}
```

**Example Usage:**
```
Get my complete schedule for tomorrow
Show me everything planned for January 20-26
```

---

### 4. get_calendar_events

**Description:** Get calendar events for a specific date range.

**Parameters:**
- `start_date` (string, optional): Start date in YYYY-MM-DD format. Default: today
- `end_date` (string, optional): End date in YYYY-MM-DD format. Default: start_date

**Returns:** Array of calendar event records sorted by date and start time.

**Event Fields:**
- `Name`: Event name
- `Title`: Event title
- `Date`: Date in YYYY-MM-DD format
- `Start Time`: ISO datetime
- `End Time`: ISO datetime
- `Duration (min)`: Duration in minutes
- `Location`: Event location (if any)
- `Calendar`: Calendar source (Personal, Work, School, etc.)
- `Status`: Confirmed, Tentative, Cancelled
- `All Day`: Boolean
- `Recurring`: Boolean
- `Attendees`: Comma-separated list of emails

**Example Usage:**
```
What events do I have this week?
Show me my calendar for next Monday
```

---

### 5. get_tasks

**Description:** Get all tasks from the Tasks table.

**Parameters:**
- `limit` (number, optional): Maximum number of tasks to return. Default: 100

**Returns:** Array of task records.

**Note:** The Tasks table is currently empty (no fields configured). Once fields are added, this function will return task data.

**Example Usage:**
```
Show me my tasks
What are my top priority tasks?
```

---

### 6. get_training_sessions

**Description:** Get training sessions (actual workouts completed) for a date range.

**Parameters:**
- `start_date` (string, optional): Start date in YYYY-MM-DD format. Default: today
- `end_date` (string, optional): End date in YYYY-MM-DD format. Default: 7 days from start

**Returns:** Array of training session records linked to Day records in the range.

**Training Session Fields:**
- `Name`: Session name (e.g., "Bozeman Trail Running")
- `Activity Type`: Type of activity (Running, Hiking, Cycling, etc.)
- `Start Time`: ISO datetime
- `Moving Duration (min)`: Duration in minutes
- `Activity Training Load`: Training load score
- `Aerobic Training Effect`: Aerobic impact (0-5 scale)
- `Anaerobic Training Effect`: Anaerobic impact (0-5 scale)
- `Avg Moving Speed (mph)`: Average speed
- `Avg Grade Adjusted Speed (mph)`: Speed adjusted for elevation
- `Body Battery Change`: Impact on body battery (-/+)
- `Source`: Data source (e.g., Garmin)
- `Garmin URL`: Link to activity on Garmin Connect

**Example Usage:**
```
Show me my workouts from last week
What training did I complete this month?
```

---

### 7. get_training_plans

**Description:** Get training plans (planned workouts) for a date range.

**Parameters:**
- `start_date` (string, optional): Start date in YYYY-MM-DD format. Default: today
- `end_date` (string, optional): End date in YYYY-MM-DD format. Default: 7 days from start

**Returns:** Array of training plan records linked to Day records in the range.

**Training Plan Fields:**
- `Name`: Plan name (e.g., "Week 3 - Monday: Rest")
- `Workout Type`: Type (Rest, Easy Run, Long Run, etc.)
- `Status`: Planned, Completed, Skipped
- `Workout Description`: Detailed description
- `Workout Detail`: Brief detail
- `Priority`: Important, Critical, Optional
- `Training Phase`: Base Building, Build 1, Build 2, Taper
- `Target Pace Effort`: Target pace or effort level
- `Focus Areas`: Array of focus areas (Recovery, Endurance, etc.)
- `Planned Distance`: Planned distance (if applicable)
- `Planned Duration`: Planned duration (if applicable)
- `Planned Elevation Gain`: Planned elevation (if applicable)

**Example Usage:**
```
What training do I have planned for this week?
Show me my workout plan for next month
```

---

### 8. get_health_metrics

**Description:** Get health metrics (sleep, steps, heart rate, etc.) for a date range.

**Parameters:**
- `start_date` (string, optional): Start date in YYYY-MM-DD format. Default: today
- `end_date` (string, optional): End date in YYYY-MM-DD format. Default: start_date

**Returns:** Array of health metric records sorted by date.

**Health Metric Fields:**
- `Name`: Date in YYYY-MM-DD format (primary field)
- `Resting HR`: Resting heart rate (bpm)
- `Steps`: Daily step count
- `Floors Climbed`: Floors climbed equivalent
- `Active Calories`: Active calories burned
- `Total Calories`: Total calories burned
- `Stress Level`: Average stress level (0-100)
- `Body Battery`: Body battery level (0-100)
- `Intensity Minutes`: Total intensity minutes
- `Moderate Intensity Minutes`: Moderate intensity minutes
- `Vigorous Intensity Minutes`: Vigorous intensity minutes
- `Sleep Duration`: Sleep duration (hours)
- `Sleep Score`: Sleep quality score (0-100)

**Example Usage:**
```
How did I sleep last week?
Show me my step count for this month
What was my stress level yesterday?
```

---

### 9. get_planned_meals

**Description:** Get planned meals for a date range.

**Parameters:**
- `start_date` (string, optional): Start date in YYYY-MM-DD format. Default: today
- `end_date` (string, optional): End date in YYYY-MM-DD format. Default: 7 days from start

**Returns:** Array of planned meal records sorted by date.

**Planned Meal Fields:**
- `Name`: Meal name
- `Date`: Date in YYYY-MM-DD format
- `Meal Type`: Breakfast, Lunch, Dinner, Snack
- `Recipe`: Linked recipe record
- `Servings`: Number of servings
- `Status`: Planned, Prepared, Consumed, Skipped

**Example Usage:**
```
What meals do I have planned for this week?
Show me my meal prep for next week
```

---

### 10. get_recipes

**Description:** Search for recipes by name.

**Parameters:**
- `search` (string, optional): Search term for recipe name (case-insensitive)
- `limit` (number, optional): Maximum recipes to return. Default: 20

**Returns:** Array of recipe records.

**Recipe Fields:**
- `Name`: Recipe name
- `Category`: Breakfast, Lunch, Dinner, Snack
- `Prep Time`: Prep time in minutes
- `Cook Time`: Cook time in minutes
- `Total Time`: Total time in minutes
- `Servings`: Number of servings
- `Ingredients`: Full ingredient list
- `Instructions`: Step-by-step instructions
- `Tags`: Array of tags (Gluten-Free, Dairy-Free, High-Protein, etc.)
- `Calories`: Calories per serving
- `Protein`: Protein grams per serving
- `Carbs`: Carbs grams per serving
- `Fat`: Fat grams per serving

**Example Usage:**
```
Find recipes with salmon
Show me high-protein breakfast recipes
```

---

### 11. get_projects

**Description:** Get all projects and their details.

**Parameters:**
- `limit` (number, optional): Maximum projects to return. Default: 100

**Returns:** Array of project records.

**Project Fields:**
- `Name`: Project name
- `Status`: To Do, In Progress, Done
- `Classes`: Linked class records
- `Due Date`: Linked Day records for due date

**Example Usage:**
```
Show me my class projects
What projects are due soon?
```

---

### 12. get_classes

**Description:** Get class information and schedules.

**Parameters:** None

**Returns:** Array of class records.

**Class Fields:**
- `Class`: Class code (e.g., "CSCI 540")
- `Description`: Class description
- `Semester`: Semester code (e.g., "F25")
- `Credits`: Credit hours
- `Grade`: Letter grade
- `Class Type`: Core, Elective, etc.
- `Domain`: Subject domain
- `Prerequisites`: Linked prerequisite classes

**Example Usage:**
```
What classes am I taking?
Show me my courses for this semester
```

---

## Field Name Reference

### Critical Field Names

Use these exact field names in Airtable formulas and queries:

#### Calendar Events Table
- `Date` - Date in YYYY-MM-DD format
- `Start Time` - ISO datetime
- `End Time` - ISO datetime
- `Name` - Event name
- `Title` - Event title
- `Location` - Location (nullable)
- `Calendar` - Calendar source
- `Status` - Event status
- `All Day` - Boolean
- `Day` - Linked to Day table

#### Training Plans Table
- `Name` - Plan name
- `Day` - Linked to Day table (array)
- `Workout Type` - Type of workout
- `Status` - Plan status
- `Workout Description` - Full description
- `Priority` - Importance level
- `Training Phase` - Phase of training

#### Training Sessions Table
- `Name` - Session name
- `Day` - Linked to Day table (array)
- `Activity Type` - Type of activity
- `Start Time` - ISO datetime
- `Moving Duration (min)` - Duration
- `Training Effect` - Overall training effect

#### Health Metrics Table
- `Name` - Date in YYYY-MM-DD format (primary field)
- `Resting HR` - Heart rate
- `Steps` - Step count
- `Body Battery` - Battery level
- `Sleep Score` - Sleep quality

#### Planned Meals Table
- `Date` - Date in YYYY-MM-DD format
- `Day` - Linked to Day table (array)
- `Name` - Meal name
- `Meal Type` - Type of meal
- `Recipe` - Linked recipe
- `Status` - Meal status

#### Day Table
- `Day` - Date in YYYY-MM-DD format (primary field)
- `Weekday` - Day of week
- `Week_id` - Week identifier
- `week` - Linked to Week table

---

## Common Use Cases

### Daily Planning

**Use Case:** Start your day with a complete overview

**Functions to Use:**
1. `get_today_overview` - Get everything for today
2. `get_calendar_events` - Check specific event details

**Example:**
```
Give me my overview for today
What's my first meeting?
```

### Weekly Planning

**Use Case:** Plan your week ahead

**Functions to Use:**
1. `get_week_overview` - Get weekly summary
2. `get_complete_schedule` - Get detailed daily breakdown
3. `get_training_plans` - Check workout schedule
4. `get_planned_meals` - Review meal prep

**Example:**
```
Show me my week overview
What training do I have planned this week?
What meals should I prep?
```

### Training Analysis

**Use Case:** Review training progress

**Functions to Use:**
1. `get_training_sessions` - See completed workouts
2. `get_training_plans` - Compare to planned workouts
3. `get_health_metrics` - Check recovery metrics

**Example:**
```
How much did I train last week?
Compare my planned vs actual training
How's my recovery looking?
```

### Meal Planning

**Use Case:** Plan and prep meals

**Functions to Use:**
1. `get_planned_meals` - Check meal schedule
2. `get_recipes` - Find recipe ideas
3. `get_complete_schedule` - See meals in context of training

**Example:**
```
What meals are planned for next week?
Find a high-protein dinner recipe
What should I eat before my long run tomorrow?
```

---

## Troubleshooting

### Common Errors

#### "Unknown field name" errors
**Cause:** Using incorrect field names in queries
**Solution:** Refer to the Field Name Reference above. Field names are case-sensitive and must match exactly (including spaces).

#### "Could not find table" errors
**Cause:** Table doesn't exist in the Airtable base
**Solution:** Verify the table exists and the AIRTABLE_BASE_ID is correct.

#### Empty results when data exists
**Cause:** Date format mismatch or incorrect field names
**Solution:** Ensure dates are in YYYY-MM-DD format and field names match the schema.

#### "No Day records found" errors
**Cause:** Day table doesn't have records for the requested date range
**Solution:** Ensure Day records exist for the dates you're querying. The Day table must be populated with date records.

### Best Practices

1. **Date Formats:** Always use YYYY-MM-DD format for dates
2. **Linked Records:** Remember that Training Sessions and Plans filter via Day record linkage
3. **Error Handling:** Functions return error messages in the response; check for `_error` fields
4. **Performance:** Use `get_complete_schedule` for comprehensive data instead of multiple calls
5. **Empty Tables:** Tasks table is currently empty; add fields as needed

### Getting Help

If you encounter issues:

1. Check the AIRTABLE_SCHEMA.md file for current table structure
2. Review AIRTABLE_FIELD_MAPPING.md for exact field names
3. Test with the test_mcp_functions.md test suite
4. Verify your .env file has correct credentials

---

## Updates and Changes

### Version 1.0.0 (January 21, 2026)

**Major Updates:**
- ✅ Fixed all field name mismatches
- ✅ Added `get_complete_schedule` function for unified data retrieval
- ✅ Added `get_training_plans` function
- ✅ Improved `get_week_overview` with date grouping and summaries
- ✅ Fixed Training Sessions and Plans filtering by Day records
- ✅ Fixed Health Metrics filtering by Name field (date format)
- ✅ Added comprehensive error handling
- ✅ Documented all field names and function parameters

**Known Limitations:**
- Tasks table has no fields configured (returns empty results)
- Body Metrics table has no fields configured
- Weekly Reviews table has no fields configured

---

## Developer Notes

### Architecture

The MCP server uses:
- **Airtable API:** Official Node.js SDK
- **MCP SDK:** Model Context Protocol for Claude integration
- **TypeScript:** Type-safe implementation

### Key Implementation Details

1. **Date Filtering:** Most tables filter by date directly, but Training Plans/Sessions filter via linked Day records
2. **Linked Records:** Use `SEARCH()` and `ARRAYJOIN()` for filtering linked record arrays
3. **Error Handling:** Each data fetch is wrapped in try-catch with error fields in response
4. **Sorting:** Results are sorted by date/time for chronological presentation

### Extending the Server

To add new functions:

1. Define the tool in the `tools` array
2. Add the case handler in the switch statement
3. Use helper functions for common operations
4. Follow the pattern of existing functions
5. Add comprehensive error handling
6. Document the new function in this file

---

*For more details, see:*
- `AIRTABLE_SCHEMA.md` - Complete table schemas
- `AIRTABLE_FIELD_MAPPING.md` - Quick field name reference
- `test_mcp_functions.md` - Test suite and examples
