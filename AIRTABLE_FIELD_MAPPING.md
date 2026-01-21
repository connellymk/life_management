# Field Name Reference for MCP Server

## Quick Reference

Use these exact field names in filterByFormula and sort operations:

### Day

```typescript
// Field names:
"Calendar Events" // null/undefined
"Day" // string (date format)
"Training Plans" // null/undefined
"Week_id" // string
"Weekday" // string
"week" // array (1 items) - likely linked records
```

### Week

```typescript
// Field names:
"Calendar Events (from Days)" // array (3 items) - likely linked records
"Days" // array (7 items) - likely linked records
"End Date" // string (date format)
"Name" // string
"Range" // string
"Start Date" // string (date format)
"Training Phase" // string
"Training Plans (from Days)" // array (7 items) - likely linked records
"Weekly Goals" // string
```

### Calendar Events

```typescript
// Field names:
"All Day" // boolean
"Attendees" // null/undefined
"Calendar" // string
"Date" // string (date format)
"Day" // array (1 items) - likely linked records
"Description" // null/undefined
"Duration (min)" // number
"End Time" // string (date format)
"Event ID" // string
"Last Synced" // string (date format)
"Location" // null/undefined
"Name" // string
"Recurring" // boolean
"Start Time" // string (date format)
"Status" // string
"Title" // string
```

### Tasks

```typescript
// Field names:
```

### Projects

```typescript
// Field names:
"Classes" // array (1 items) - likely linked records
"Due Date" // array (1 items) - likely linked records
"Name" // string
"Status" // string
```

### Classes

```typescript
// Field names:
"Class" // string
"Class Type" // null/undefined
"Credits" // null/undefined
"Description" // string
"Domain" // null/undefined
"Grade" // null/undefined
"Prerequisites" // null/undefined
"Semester" // null/undefined
```

### Training Plans

```typescript
// Field names:
"Day" // array (1 items) - likely linked records
"Focus Areas" // array (1 items) - first item type: string
"Name" // string
"Planned Distance" // null/undefined
"Planned Duration" // null/undefined
"Planned Elevation Gain" // null/undefined
"Priority" // string
"Status" // string
"Target Pace Effort" // string
"Training Phase" // string
"Workout Description" // string
"Workout Detail" // string
"Workout Type" // string
"week (from Day)" // array (1 items) - likely linked records
```

### Training Sessions

```typescript
// Field names:
"Activity ID" // string
"Activity Training Load" // number
"Activity Type" // string
"Aerobic Training Effect" // number
"Anaerobic Training Effect" // null/undefined
"Avg Grade Adjusted Speed (mph)" // null/undefined
"Avg Moving Speed (mph)" // number
"Body Battery Change" // number
"Day" // array (1 items) - likely linked records
"Garmin URL" // string
"Moving Duration (min)" // number
"Name" // string
"Source" // string
"Start Time" // string (date format)
"Training Effect" // number
```

### Health Metrics

```typescript
// Field names:
"Active Calories" // null/undefined
"Body Battery" // null/undefined
"Day" // array (1 items) - likely linked records
"Floors Climbed" // null/undefined
"Intensity Minutes" // null/undefined
"Last Modified" // string (date format)
"Moderate Intensity Minutes" // null/undefined
"Name" // string (date format)
"Resting HR" // null/undefined
"Sleep Duration" // null/undefined
"Sleep Score" // null/undefined
"Steps" // null/undefined
"Stress Level" // null/undefined
"Total Calories" // null/undefined
"Vigorous Intensity Minutes" // null/undefined
```

### Body Metrics

```typescript
// Field names:
```

### Planned Meals

```typescript
// Field names:
"Date" // string (date format)
"Day" // array (1 items) - likely linked records
"Meal Type" // string
"Name" // string
"Recipe" // array (1 items) - likely linked records
"Servings" // number
"Status" // string
```

### Meal Plans

```typescript
// Field names:
"End Date" // string (date format)
"Name" // string
"Notes" // string
"Start Date" // string (date format)
"Status" // string
```

### Recipes

```typescript
// Field names:
"Calories" // number
"Carbs" // number
"Category" // string
"Cook Time" // number
"Fat" // number
"Grocery Items" // array (8 items) - likely linked records
"Ingredients" // string
"Instructions" // string
"Name" // string
"Planned Meals" // array (2 items) - likely linked records
"Prep Time" // number
"Protein" // number
"Servings" // number
"Tags" // array (4 items) - first item type: string
"Total Time" // number
```

### Grocery Items

```typescript
// Field names:
"Category" // string
"Name" // string
"Notes" // string
"Quantity" // string
"Recipe" // array (1 items) - likely linked records
"Unit" // string
```

### Weekly Reviews

```typescript
// Field names:
```

