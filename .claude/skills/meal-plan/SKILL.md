---
name: meal-plan
description: Generate a weekly meal plan for the family based on upcoming training schedule, calendar events, and health metrics. Creates an AIP-compliant meal plan, writes it to a Notion page, and generates a grocery list file for the Kroger cart.
allowed-tools: Bash(python3 *), Bash(python *), Read, Glob, Grep, mcp__4585d70e-a543-4af1-9c0c-226e5d94fbe6__notion-create-pages, mcp__4585d70e-a543-4af1-9c0c-226e5d94fbe6__notion-search, mcp__4585d70e-a543-4af1-9c0c-226e5d94fbe6__notion-fetch
argument-hint: "[week-offset or YYYY-MM-DD]"
---

# Weekly Meal Plan Generator

Create a training-aware, AIP-compliant weekly meal plan for the family. This skill pulls schedule and workout data from Notion, generates a complete 7-day meal plan, publishes it to Notion, and writes a grocery list file ready for the Kroger cart orchestrator.

## Step 1: Gather Context

Run the meal plan data gatherer to pull next week's schedule. If $ARGUMENTS is provided, pass it through: use `--start-date` if it looks like a date (YYYY-MM-DD), otherwise use `--week-offset`.

```
python3 orchestrators/meal_plan.py [--start-date DATE | --week-offset N]
```

Parse the JSON output. This gives you:
- **week.start / week.end / week.label**: The target Mon–Sun date range
- **calendar_events**: All calendar events for the week (title, start, end, source, location)
- **planned_workouts**: Scheduled workouts (name, date, type, duration, distance, calories)
- **recent_health_metrics**: Past 7 days of daily tracking (steps, calories, sleep, stress, weight)
- **summary**: Aggregated stats (training minutes, workout types, avg calories, avg sleep)

## Step 2: Analyze the Training Week

From the gathered data, build a day-by-day picture:

For each day (Monday–Sunday):
1. **Training load**: What workout is planned? Type (Run/Bike/Swim/Strength/Walk), duration, distance, estimated calorie burn.
2. **Schedule density**: How many calendar events? Are there time-constrained meals (early morning workouts, lunch meetings, evening commitments)?
3. **Recovery needs**: Is this a rest day following a hard training day? Are there back-to-back training days?

Classify each day as one of:
- **Heavy training day** (>60 min intense workout or >90 min any workout): Higher calorie, extra carbs and protein
- **Moderate training day** (30–60 min workout): Standard active-day nutrition
- **Light/rest day** (no workout or <30 min easy): Lighter meals, focus on recovery nutrients
- **Race/event day**: Pre-event fueling, easy-to-digest meals

## Step 3: Generate the Meal Plan

Create a 7-day meal plan following these guidelines:

### AIP (Autoimmune Protocol) Compliance
All meals MUST be AIP-compliant. This means:
- **YES**: Meat, fish, vegetables, fruit, healthy fats (avocado oil, olive oil, coconut oil), sweet potatoes, plantains, bone broth, coconut products, herbs, collagen
- **NO**: Grains, dairy, eggs, nuts, seeds (except coconut and occasional chia noted in prior lists), nightshades (tomatoes, peppers, eggplant, white potatoes), legumes, refined sugars, alcohol, coffee, seed-based spices (cumin, coriander, paprika, mustard, nutmeg)
- **Allowed spices**: Salt, garlic, ginger, turmeric, cinnamon, herbs (basil, oregano, thyme, rosemary, sage, mint, parsley, cilantro)

### Meal Structure Per Day
- **Breakfast**: Quick on busy/early workout days, heartier on rest days
- **Lunch**: Prep-friendly (batch cookable), portable if schedule is packed
- **Dinner**: Family meal — feeds the whole family
- **Snacks** (1–2 per day): Pre/post workout fuel on training days, optional on rest days

### Training-Aware Nutrition
- **Pre-workout** (training days): Easily digestible carbs + small protein — e.g., banana with collagen, sweet potato bites
- **Post-workout** (training days): Protein + carbs for recovery — e.g., chicken with sweet potato, smoothie with collagen and berries
- **Heavy training days**: Add an extra starchy carb serving (sweet potato, plantain) and increase protein portions
- **Rest days**: Emphasize anti-inflammatory foods (turmeric, ginger, leafy greens, berries, bone broth)

### Practical Constraints
- **Batch cooking**: Identify 2–3 proteins and 2–3 carb bases that repeat across the week to simplify prep
- **Leftovers**: Dinner leftovers become next-day lunches where possible
- **Time-aware**: Quick breakfasts on early-morning workout days, meal-prep lunches on busy calendar days
- **Family-friendly**: Dinners should work for the whole family, not just the athlete

### Meal Plan Format

For each day, produce:

```
### [Day], [Date]
**Training**: [workout summary or "Rest day"]
**Schedule**: [notable calendar events affecting meals]

**Breakfast**: [meal] — [brief description]
**Snack**: [if applicable — pre-workout fuel, etc.]
**Lunch**: [meal] — [brief description]
**Snack**: [if applicable — post-workout recovery, etc.]
**Dinner**: [meal — family dinner] — [brief description]
```

## Step 4: Generate Grocery List

After creating the meal plan, compile a consolidated grocery list:

1. Review all ingredients across every meal for the week
2. Consolidate duplicates and estimate quantities
3. Group by category matching the existing format (see `grocery_lists/` for examples)

Write the grocery list to: `grocery_lists/week{N}_{mon_date}-{sun_date}.txt`

Use the same format as existing grocery lists:
```
# Week N Grocery List — Mon Date–Sun Date, Year
# AIP Meal Plan
# Usage: python orchestrators/grocery_cart.py --file grocery_lists/weekN_monDD-sunDD.txt

# === PROTEINS ===
2x ground turkey 1 lb
...

# === PRODUCE ===
7x sweet potatoes large
...

# === PANTRY ===
coconut milk full fat canned
...

# === SPICES (check pantry first) ===
ground turmeric
...
```

Determine the week number from the date (ISO week number).

## Step 5: Publish to Notion

Search Notion for an existing "Meal Plans" page or database to place the meal plan under. If none is found, create a standalone page.

Create a Notion page with:
- **Title**: `Meal Plan — {week.label}`
- **Content**: The full meal plan in markdown, with each day as a section, plus a "Grocery List" section at the bottom summarizing what to buy

Before creating the page, show the user the complete meal plan and ask for confirmation.

## Step 6: Summary

After publishing, print a summary:
- Week covered
- Number of training days vs rest days
- Grocery list file path (remind the user they can run `python orchestrators/grocery_cart.py --file <path>` to add items to their Kroger cart)
- Link to the Notion page
