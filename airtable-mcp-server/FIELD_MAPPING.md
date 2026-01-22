# Airtable MCP Server - Field Mapping Documentation

**Generated:** January 21, 2026
**Base:** Personal Planning System

## Overview

This document provides a comprehensive mapping of all field names used in the Airtable Personal Planning System. Use this as a reference when writing queries or updating the MCP server code.

## Table Schemas

### Calendar Events Table

| Field Name | Type | Purpose | Example |
|-----------|------|---------|---------|
| Name | Text | Event name/title | "M508 (Mathematics of Machine Learning)" |
| Event ID | Text | Unique calendar event identifier | "1vpd2ijhq5k7dop9qp7mq6gp7d_20260121T150000Z" |
| Title | Text | Event title | "M508 (Mathematics of Machine Learning)" |
| Date | Date | Event date (YYYY-MM-DD) | "2026-01-21" |
| Start Time | DateTime | Event start time (ISO 8601) | "2026-01-21T15:00:00.000Z" |
| End Time | DateTime | Event end time (ISO 8601) | "2026-01-21T15:50:00.000Z" |
| Duration (min) | Number | Event duration in minutes | 50 |
| Calendar | Select | Calendar source | "Personal", "School and Research" |
| Location | Text | Event location | "Wilson 1144" |
| Description | Long Text | Event description/notes | Full event description |
| Attendees | Text | List of attendees | "marykate@threadedmfg.com" |
| Status | Select | Event status | "Confirmed" |
| Last Synced | DateTime | Last synchronization time | "2026-01-17T21:35:50.170Z" |
| Day | Link to Day | Link to Day record | ["recxaAYA3eObeo1TC"] |
| All Day | Checkbox | All-day event flag | true/false |
| Recurring | Checkbox | Recurring event flag | true/false |

**Key Insights:**
- Calendar events are linked to Day records via the "Day" field
- Date field stores YYYY-MM-DD format dates
- Start Time and End Time use ISO 8601 datetime format
- All Day and Recurring are boolean checkboxes

### Tasks Table

| Field Name | Type | Purpose | Example |
|-----------|------|---------|---------|
| Name | Text | Task name/title | "Finish base structure" |
| Category | Select | Task category | "Personal Project" |

**Key Insights:**
- Tasks table has minimal fields currently
- No "due date" field exists (mentioned in error reports)
- No "status" field exists (mentioned in error reports)
- May need to add these fields to the Airtable base for full functionality

**Note:** The original requirements document mentioned errors about "due date" and "status" fields, but these fields don't currently exist in the Tasks table. The MCP server functions should not attempt to filter by these fields.

### Training Sessions Table

| Field Name | Type | Purpose | Example |
|-----------|------|---------|---------|
| Name | Text | Activity name | "Gallatin County Running" |
| Day | Link to Day | Link to Day record(s) | ["recqgBoB0buoSjhOu"] |
| Activity ID | Text | Garmin activity ID | "21581066749" |
| Start Time | DateTime | Activity start time (ISO 8601) | "2026-01-17T15:30:45.000Z" |
| Activity Type | Select | Type of activity | "Running", "Cycling", "Hiking" |
| Training Effect | Number | Overall training effect | 4.099999904632568 |
| Source | Select | Data source | "Garmin" |
| Garmin URL | URL | Link to Garmin Connect | "https://connect.garmin.com/modern/activity/21581066749" |
| Aerobic Training Effect | Number | Aerobic training effect | 4.099999904632568 |
| Anaerobic Training Effect | Number | Anaerobic training effect | 1.2000000476837158 |
| Activity Training Load | Number | Training load metric | 171.0349578857422 |
| Avg Grade Adjusted Speed (mph) | Number | Average grade-adjusted speed | 6.23 |
| Avg Moving Speed (mph) | Number | Average moving speed | 6.23 |
| Body Battery Change | Number | Change in body battery | -8 |
| Moving Duration (min) | Number | Moving time in minutes | 40.5 |

**Key Insights:**
- Training sessions are linked to Day records
- Most sessions have Garmin as the source
- Some fields may be null for certain activity types (e.g., cycling may not have Anaerobic Training Effect)

### Training Plans Table

| Field Name | Type | Purpose | Example |
|-----------|------|---------|---------|
| Name | Text | Plan name | (Similar structure to Training Sessions) |
| Day | Link to Day | Link to Day record(s) | Array of day record IDs |
| Activity ID | Text | Unique activity identifier | - |
| Start Time | DateTime | Planned start time | - |
| Activity Type | Select | Type of activity | - |
| ... | ... | (Similar fields to Training Sessions) | - |

**Key Insights:**
- Training Plans use the same field structure as Training Sessions
- The "Date" field mentioned in error reports does NOT exist
- Plans are linked to Days via the "Day" field
- Filter using Day record IDs, not dates

**Note:** The error "Unknown field name: 'Date'" indicates the code was trying to use a Date field that doesn't exist. Training Plans should be queried using the Day link field.

### Planned Meals Table

| Field Name | Type | Purpose | Example |
|-----------|------|---------|---------|
| Name | Text | Meal name | "Chia Pudding with Berries" |
| Date | Date | Meal date (YYYY-MM-DD) | "2026-01-24" |
| Day | Link to Day | Link to Day record | ["recILIxQtCmlSkQoP"] |
| Meal Type | Select | Type of meal | "Breakfast", "Lunch", "Dinner", "Snack" |
| Recipe | Link to Recipe | Link to recipe record(s) | ["recNg8jKvfurb9dee"] |
| Servings | Number | Number of servings | 1, 1.5, 2 |
| Status | Select | Meal status | "Planned", "Prepared" |
| Notes | Long Text | Additional notes | "Lighter breakfast before long run" |

**Key Insights:**
- Meals have both Date (YYYY-MM-DD) and Day (link) fields
- Can be queried by date directly
- Recipes are linked separately
- Servings can be fractional (0.75, 1.5)

### Recipes Table

| Field Name | Type | Purpose | Example |
|-----------|------|---------|---------|
| Name | Text | Recipe name | "Chia Pudding with Berries" |
| (Additional fields not shown in sample data) | - | - | - |

**Key Insights:**
- Recipes are searched by Name field
- Use FIND(LOWER()) for case-insensitive search

### Health Metrics Table

| Field Name | Type | Purpose | Example |
|-----------|------|---------|---------|
| Name | Date | Date of metrics (YYYY-MM-DD) | "2026-01-21" |
| (Additional fields for sleep, steps, etc.) | Various | Health data | - |

**Key Insights:**
- The "Name" field stores the date (YYYY-MM-DD format)
- Filter using `{Name} = 'YYYY-MM-DD'` or date ranges
- No health metrics found in test date range

### Day Table

| Field Name | Type | Purpose | Example |
|-----------|------|---------|---------|
| Day | Date | Date (YYYY-MM-DD) | "2026-01-21" |
| Weekday | Text | Day of week | "Tuesday" |
| (Links to other records) | Various | Rollup fields | - |

**Key Insights:**
- Central table that links all date-based records
- Used for querying Training Plans and Sessions
- Day record IDs must be retrieved before querying linked tables

### Classes Table

| Field Name | Type | Purpose | Example |
|-----------|------|---------|---------|
| Class | Text | Class code | "M 508" |
| Description | Text | Class name | "Mathematics of Machine Learning" |
| Semester | Text | Semester code | "S26" (Spring 2026) |
| Prerequisites | Link to Classes | Prerequisite classes | Array of class record IDs |
| From field: Prerequisites | Link to Classes | Reverse prerequisite links | Array of class record IDs |
| Grade | Text | Grade received | "A", "B+", "P" |
| Credits | Number | Credit hours | 3 |
| Class Type | Multiple Select | Type categories | ["Core"], ["Elective"], ["Prereq"] |
| Domain | Select | Academic domain | "CSCI", "STAT", "Math", "ECIV" |
| Projects | Link to Projects | Related projects | Array of project record IDs |

**Key Insights:**
- Classes have bidirectional prerequisite relationships
- Multiple class types can be assigned
- Some classes are ongoing/future (no grade yet)

### Projects Table

**Note:** Unable to retrieve project data (403 NOT_AUTHORIZED error). The API key may not have permission to access this table, or the table may have restricted permissions.

## Common Query Patterns

### Querying by Date

**Calendar Events:**
```typescript
filterByFormula: `{Date} = '2026-01-21'`
filterByFormula: `AND({Date} >= '2026-01-20', {Date} <= '2026-01-27')`
```

**Planned Meals:**
```typescript
filterByFormula: `{Date} = '2026-01-21'`
filterByFormula: `AND({Date} >= '2026-01-20', {Date} <= '2026-01-27')`
```

**Health Metrics:**
```typescript
filterByFormula: `{Name} = '2026-01-21'`  // Note: Name field stores the date
filterByFormula: `AND({Name} >= '2026-01-20', {Name} <= '2026-01-27')`
```

### Querying Training Plans/Sessions by Date Range

Training Plans and Sessions are linked to Day records, so you must:

1. First, get Day record IDs for the date range:
```typescript
const dayRecords = await base('Day')
  .select({
    filterByFormula: `AND({Day} >= '2026-01-20', {Day} <= '2026-01-27')`,
  })
  .all();
const dayRecordIds = dayRecords.map(r => r.id);
```

2. Then query using those IDs:
```typescript
const dayIdFilter = dayRecordIds.map(id => `SEARCH('${id}', ARRAYJOIN({Day}))`).join(', ');
const plans = await base('Training Plans')
  .select({
    filterByFormula: `OR(${dayIdFilter})`,
  })
  .all();
```

## Field Type Reference

| Type | Description | Example |
|------|-------------|---------|
| Text | Short text field | "Task name" |
| Long Text | Multi-line text | "Detailed description..." |
| Number | Numeric value | 42, 3.14 |
| Date | Date without time (YYYY-MM-DD) | "2026-01-21" |
| DateTime | Date with time (ISO 8601) | "2026-01-21T15:00:00.000Z" |
| Select | Single-select dropdown | "In Progress" |
| Multiple Select | Multi-select dropdown | ["Core", "Elective"] |
| Checkbox | Boolean true/false | true |
| URL | Web link | "https://example.com" |
| Link to Record | Reference to another table | ["rec1234567890"] |

## Known Issues and Solutions

### Issue 1: Tasks Table Missing Fields

**Error:** `Unknown field names: due date, status`

**Cause:** The Tasks table doesn't have "due date" or "status" fields.

**Solution:**
- Remove any filtering by these fields in the code
- OR add these fields to the Airtable base if needed

### Issue 2: Training Plans Date Field

**Error:** `Unknown field name: "Date"`

**Cause:** Training Plans table uses "Day" (link) field, not "Date" field.

**Solution:**
- Always query Training Plans using Day record IDs
- Never try to filter by a "Date" field directly

### Issue 3: Health Metrics Date Field

**Quirk:** Health Metrics uses "Name" field to store the date.

**Solution:**
- Filter using `{Name} = 'YYYY-MM-DD'` instead of `{Date}`

## Best Practices

1. **Always verify field names** before writing queries
2. **Use Day record IDs** for Training Plans/Sessions queries
3. **Handle optional fields** - many fields can be null/empty
4. **Use proper date formats** - YYYY-MM-DD for dates, ISO 8601 for datetimes
5. **Check permissions** before accessing tables (e.g., Projects table)
6. **Use ARRAYJOIN and SEARCH** for link field queries
7. **Sort results** by date/time for chronological order

## API Usage Examples

### Get Today's Schedule
```typescript
const today = '2026-01-21';

// Calendar events
const events = await base('Calendar Events')
  .select({
    filterByFormula: `{Date} = '${today}'`,
    sort: [{ field: 'Start Time', direction: 'asc' }],
  })
  .all();

// Meals
const meals = await base('Planned Meals')
  .select({
    filterByFormula: `{Date} = '${today}'`,
  })
  .all();

// Health metrics
const health = await base('Health Metrics')
  .select({
    filterByFormula: `{Name} = '${today}'`,
    maxRecords: 1,
  })
  .all();
```

### Get Week's Training
```typescript
const startDate = '2026-01-20';
const endDate = '2026-01-27';

// Get Day record IDs
const dayRecords = await base('Day')
  .select({
    filterByFormula: `AND({Day} >= '${startDate}', {Day} <= '${endDate}')`,
  })
  .all();

const dayRecordIds = dayRecords.map(r => r.id);

if (dayRecordIds.length > 0) {
  const dayIdFilter = dayRecordIds
    .map(id => `SEARCH('${id}', ARRAYJOIN({Day}))`)
    .join(', ');

  const sessions = await base('Training Sessions')
    .select({
      filterByFormula: `OR(${dayIdFilter})`,
    })
    .all();
}
```

## Conclusion

The MCP server implementation is mostly correct and already includes the `get_complete_schedule` function. The main issues are:

1. **Tasks table** lacks "due date" and "status" fields (they need to be added to Airtable or code updated to not use them)
2. **Training Plans** should be queried using Day links, not a Date field
3. **Health Metrics** uses "Name" field for dates (already correctly implemented)

All other field names are correctly used in the current implementation.
