# Airtable Schema Documentation

**Generated:** 2026-01-21T22:17:14.150Z

**Base ID:** appKYFUTDs7tDg4Wr

---

## Day

**Status:** ✅ Active (5 sample records inspected)

### Fields

| Field Name | Type | Notes |
|------------|------|-------|
| `Calendar Events` | null/undefined | |
| `Day` | string (date format) | |
| `Training Plans` | null/undefined | |
| `Week_id` | string | |
| `Weekday` | string | |
| `week` | array (1 items) - likely linked records | |

### Sample Data

```json
{
  "Day": "2026-12-12",
  "week": [
    "recuGml73VUe3pvw4"
  ],
  "Week_id": "50-26",
  "Weekday": "Saturday"
}
```

## Week

**Status:** ✅ Active (5 sample records inspected)

### Fields

| Field Name | Type | Notes |
|------------|------|-------|
| `Calendar Events (from Days)` | array (3 items) - likely linked records | |
| `Days` | array (7 items) - likely linked records | |
| `End Date` | string (date format) | |
| `Name` | string | |
| `Range` | string | |
| `Start Date` | string (date format) | |
| `Training Phase` | string | |
| `Training Plans (from Days)` | array (7 items) - likely linked records | |
| `Weekly Goals` | string | |

### Sample Data

```json
{
  "Name": "23-26",
  "Days": [
    "rec2eGFhmp2ynd0gL",
    "recQyeHIWjn7CIblp",
    "recsMlKCAPlUTDrix",
    "rechJ9KtYoZTrdQj7",
    "recyr2CiQWGwGNCIy",
    "recaPtHlxXpW8Fp7E",
    "recXyJeETqtYOvTP5"
  ],
  "Start Date": "2026-05-31",
  "End Date": "2026-06-06",
  "Range": "5/31/26 - 6/6/26",
  "Calendar Events (from Days)": [
    "reccA4ItWedFZ51pM",
    "rec0y2pbr42X9vPJq",
    "recMlxXqbCeqaWKio"
  ],
  "Training Phase": "Taper",
  "Weekly Goals": "Reduce volume while maintaining intensity. Prioritize rest and mental preparation for race day.",
  "Training Plans (from Days)": [
    "recwQmIWsA3QaMs8E",
    "recZOj5wAiJLmrLK6",
    "recxFaHbaV1mLqIF4",
    "recROFprMsNlh2izP",
    "recxxrEoHlaKR9OWB",
    "recnHhaGk6oq39GGs",
    "recMzzd6yvOuxbTdT"
  ]
}
```

## Calendar Events

**Status:** ✅ Active (5 sample records inspected)

### Fields

| Field Name | Type | Notes |
|------------|------|-------|
| `All Day` | boolean | |
| `Attendees` | null/undefined | |
| `Calendar` | string | |
| `Date` | string (date format) | |
| `Day` | array (1 items) - likely linked records | |
| `Description` | null/undefined | |
| `Duration (min)` | number | |
| `End Time` | string (date format) | |
| `Event ID` | string | |
| `Last Synced` | string (date format) | |
| `Location` | null/undefined | |
| `Name` | string | |
| `Recurring` | boolean | |
| `Start Time` | string (date format) | |
| `Status` | string | |
| `Title` | string | |

### Sample Data

```json
{
  "Name": "On Campus",
  "Event ID": "2lu2ttptt31sdhkgdr7cvhmevl_20260424",
  "Title": "On Campus",
  "Date": "2026-04-24",
  "Start Time": "2026-04-24T06:00:00.000Z",
  "End Time": "2026-04-25T05:59:00.000Z",
  "Duration (min)": 1439,
  "Calendar": "Personal",
  "Status": "Confirmed",
  "Last Synced": "2026-01-17T21:34:52.200Z",
  "Day": [
    "recHJH6fKclPbWVJi"
  ],
  "All Day": true,
  "Recurring": true
}
```

## Tasks

**Status:** ✅ Active (3 sample records inspected)

### Fields

| Field Name | Type | Notes |
|------------|------|-------|

### Sample Data

```json
{}
```

## Projects

**Status:** ✅ Active (2 sample records inspected)

### Fields

| Field Name | Type | Notes |
|------------|------|-------|
| `Classes` | array (1 items) - likely linked records | |
| `Due Date` | array (1 items) - likely linked records | |
| `Name` | string | |
| `Status` | string | |

### Sample Data

```json
{
  "Name": "Assignment 0",
  "Classes": [
    "recQML3XgnudAP1aw"
  ],
  "Due Date": [
    "recpNEUl3Qa5Tqz7n"
  ],
  "Status": "Done"
}
```

## Classes

**Status:** ✅ Active (5 sample records inspected)

### Fields

| Field Name | Type | Notes |
|------------|------|-------|
| `Class` | string | |
| `Class Type` | null/undefined | |
| `Credits` | null/undefined | |
| `Description` | string | |
| `Domain` | null/undefined | |
| `Grade` | null/undefined | |
| `Prerequisites` | null/undefined | |
| `Semester` | null/undefined | |

### Sample Data

```json
{
  "Class": "CSCI 540",
  "Description": "Advanced Database Systems"
}
```

## Training Plans

**Status:** ✅ Active (5 sample records inspected)

### Fields

| Field Name | Type | Notes |
|------------|------|-------|
| `Day` | array (1 items) - likely linked records | |
| `Focus Areas` | array (1 items) - first item type: string | |
| `Name` | string | |
| `Planned Distance` | null/undefined | |
| `Planned Duration` | null/undefined | |
| `Planned Elevation Gain` | null/undefined | |
| `Priority` | string | |
| `Status` | string | |
| `Target Pace Effort` | string | |
| `Training Phase` | string | |
| `Workout Description` | string | |
| `Workout Detail` | string | |
| `Workout Type` | string | |
| `week (from Day)` | array (1 items) - likely linked records | |

### Sample Data

```json
{
  "Name": "Week 3 - Monday: Rest",
  "Status": "Planned",
  "Workout Detail": "Rest Day",
  "Training Phase": "Base Building",
  "Priority": "Important",
  "Focus Areas": [
    "Recovery"
  ],
  "Workout Description": "Complete rest day. Focus on sleep, nutrition, and mental recovery. Light walking is okay if needed.",
  "Target Pace Effort": "Complete rest",
  "Day": [
    "rec3EcWn1ZIJJgzXW"
  ],
  "week (from Day)": [
    "rec8mAe0IYEXmhuTW"
  ],
  "Workout Type": "Rest"
}
```

## Training Sessions

**Status:** ✅ Active (5 sample records inspected)

### Fields

| Field Name | Type | Notes |
|------------|------|-------|
| `Activity ID` | string | |
| `Activity Training Load` | number | |
| `Activity Type` | string | |
| `Aerobic Training Effect` | number | |
| `Anaerobic Training Effect` | null/undefined | |
| `Avg Grade Adjusted Speed (mph)` | null/undefined | |
| `Avg Moving Speed (mph)` | number | |
| `Body Battery Change` | number | |
| `Day` | array (1 items) - likely linked records | |
| `Garmin URL` | string | |
| `Moving Duration (min)` | number | |
| `Name` | string | |
| `Source` | string | |
| `Start Time` | string (date format) | |
| `Training Effect` | number | |

### Sample Data

```json
{
  "Name": "Lago Argentino Hiking",
  "Day": [
    "recGt0t8zO4L8abEe"
  ],
  "Activity ID": "21421383544",
  "Start Time": "2026-01-02T11:19:11.000Z",
  "Activity Type": "Hiking",
  "Training Effect": 1.2999999523162842,
  "Source": "Garmin",
  "Garmin URL": "https://connect.garmin.com/modern/activity/21421383544",
  "Aerobic Training Effect": 1.2999999523162842,
  "Activity Training Load": 13.365264892578125,
  "Avg Moving Speed (mph)": 3.02,
  "Body Battery Change": -7,
  "Moving Duration (min)": 83.2
}
```

## Health Metrics

**Status:** ✅ Active (5 sample records inspected)

### Fields

| Field Name | Type | Notes |
|------------|------|-------|
| `Active Calories` | null/undefined | |
| `Body Battery` | null/undefined | |
| `Day` | array (1 items) - likely linked records | |
| `Floors Climbed` | null/undefined | |
| `Intensity Minutes` | null/undefined | |
| `Last Modified` | string (date format) | |
| `Moderate Intensity Minutes` | null/undefined | |
| `Name` | string (date format) | |
| `Resting HR` | null/undefined | |
| `Sleep Duration` | null/undefined | |
| `Sleep Score` | null/undefined | |
| `Steps` | null/undefined | |
| `Stress Level` | null/undefined | |
| `Total Calories` | null/undefined | |
| `Vigorous Intensity Minutes` | null/undefined | |

### Sample Data

```json
{
  "Name": "2026-01-07",
  "Day": [
    "recwY5nKOr882LPj8"
  ],
  "Last Modified": "2026-01-18T14:11:02.000Z"
}
```

## Body Metrics

**Status:** ✅ Active (3 sample records inspected)

### Fields

| Field Name | Type | Notes |
|------------|------|-------|

### Sample Data

```json
{}
```

## Planned Meals

**Status:** ✅ Active (5 sample records inspected)

### Fields

| Field Name | Type | Notes |
|------------|------|-------|
| `Date` | string (date format) | |
| `Day` | array (1 items) - likely linked records | |
| `Meal Type` | string | |
| `Name` | string | |
| `Recipe` | array (1 items) - likely linked records | |
| `Servings` | number | |
| `Status` | string | |

### Sample Data

```json
{
  "Name": "Baked Salmon with Vegetables",
  "Date": "2026-01-20",
  "Day": [
    "recOOfsp17DWSRgcJ"
  ],
  "Meal Type": "Dinner",
  "Recipe": [
    "recxgnfwRexjBBvhH"
  ],
  "Servings": 1,
  "Status": "Planned"
}
```

## Meal Plans

**Status:** ✅ Active (1 sample records inspected)

### Fields

| Field Name | Type | Notes |
|------------|------|-------|
| `End Date` | string (date format) | |
| `Name` | string | |
| `Notes` | string | |
| `Start Date` | string (date format) | |
| `Status` | string | |

### Sample Data

```json
{
  "Name": "Week 1 - Base Building Start",
  "Start Date": "2026-01-19",
  "End Date": "2026-01-26",
  "Status": "Planning",
  "Notes": "Meal Prep Notes:\nFirst week! Plan 2-3 hours Sunday for prep. Make chia pudding Saturday night. Focus on getting comfortable with the routine.\n\nKey Training Days:\nWednesday: Easy Hills (6 mi, 600 ft) | Saturday: Long Run (8 mi, 1,000 ft)"
}
```

## Recipes

**Status:** ✅ Active (5 sample records inspected)

### Fields

| Field Name | Type | Notes |
|------------|------|-------|
| `Calories` | number | |
| `Carbs` | number | |
| `Category` | string | |
| `Cook Time` | number | |
| `Fat` | number | |
| `Grocery Items` | array (8 items) - likely linked records | |
| `Ingredients` | string | |
| `Instructions` | string | |
| `Name` | string | |
| `Planned Meals` | array (2 items) - likely linked records | |
| `Prep Time` | number | |
| `Protein` | number | |
| `Servings` | number | |
| `Tags` | array (4 items) - first item type: string | |
| `Total Time` | number | |

### Sample Data

```json
{
  "Name": "Hard Boiled Eggs with Everything Seasoning",
  "Category": "Snack",
  "Prep Time": 5,
  "Cook Time": 15,
  "Total Time": 20,
  "Servings": 6,
  "Ingredients": "Ingredients\n• 12 eggs\n• Water for boiling\nEverything Seasoning Mix:\n• 2 tbsp sesame seeds\n• 1 tbsp poppy seeds\n• 1 tbsp dried minced garlic\n• 1 tbsp dried minced onion\n• 2 tsp flaky sea salt\n##",
  "Instructions": "Instructions\nPlace eggs in a large pot and cover with cold water by 1 inch.\nBring to a rolling boil over high heat.\nOnce boiling, remove from heat, cover, and let sit for 10-12 minutes.\nTransfer eggs to an ice bath for 5 minutes.\nPeel eggs (they should peel easily after ice bath).\nMix together everything seasoning ingredients in a small jar.\nStore peeled eggs in container in fridge.\nWhen ready to eat, sprinkle with everything seasoning.\n## Meal Prep Notes\nBoil all 12 eggs on Sunday. Store peeled in airtight container for up to 7 days. Bring 2 eggs as a snack with a small container of seasoning mix.\n## Nutrition Benefits\nPerfect high-protein snack. Two eggs provide 12g protein and healthy fats. Great post-workout recovery snack.\n## Serving Ideas\n• With apple slices\n• With veggie sticks\n• Sliced over salad\n• Alone as quick protein boost",
  "Tags": [
    "Gluten-Free",
    "Dairy-Free",
    "High-Protein",
    "Meal Prep"
  ],
  "Calories": 140,
  "Protein": 12,
  "Carbs": 2,
  "Fat": 10,
  "Planned Meals": [
    "recIr2B4FzRBG0J6S",
    "recuXlM7ipEzqsRnX"
  ],
  "Grocery Items": [
    "recxeYj04MKMY7mXy",
    "recUmW5i79Ib5Pimf",
    "recPiyMrrQMJrEPQF",
    "recWHqoM1a42W0Vzq",
    "recUwQBxCDnOABb9W",
    "recyqqM0g1Fx15PpJ",
    "recoUjS2uvpMKS0Pa",
    "recRg8oHOMm5iDfTS"
  ]
}
```

## Grocery Items

**Status:** ✅ Active (5 sample records inspected)

### Fields

| Field Name | Type | Notes |
|------------|------|-------|
| `Category` | string | |
| `Name` | string | |
| `Notes` | string | |
| `Quantity` | string | |
| `Recipe` | array (1 items) - likely linked records | |
| `Unit` | string | |

### Sample Data

```json
{
  "Name": "fresh ginger",
  "Category": "Other",
  "Quantity": "2",
  "Unit": "tbsp",
  "Recipe": [
    "rechs16XsLnp2A2m8"
  ],
  "Notes": "From recipe: Ground Beef & Vegetable Stir-Fry"
}
```

## Weekly Reviews

**Status:** ✅ Active (3 sample records inspected)

### Fields

| Field Name | Type | Notes |
|------------|------|-------|

### Sample Data

```json
{}
```

