# Training Plan Migration Instructions for Claude Code

## Overview
Migrate the Beaverhead 100K training plan from Notion to Airtable, creating the necessary table structures and importing all data.

---

## Environment Configuration

### Airtable
- **Base ID**: `appKYFUTDs7tDg4Wr`
- **Planned Training Activities Table ID**: `tblxSnGD6CS9ea0cM`
- **Weekly Planning Table ID**: `tbl2B7ecl7heYiKha`

### Notion
- **Training Plan Database ID**: `9a3c2dd1b2354f2a8e8f330d7fda16c3`
- **Training Plan Page URL**: `https://www.notion.so/Beaverhead-100K-Training-Plan-2eb90d86c150804aa50feffed78e45f4`

---

## Task 1: Create Airtable Table Schema

### Table 1: Planned Training Activities (tblxSnGD6CS9ea0cM)

Create the following fields using the Airtable API:

| Field Name | Type | Options | Description |
|------------|------|---------|-------------|
| Name | singleLineText | (primary field) | Workout name |
| Date | date | dateFormat: "iso" | Scheduled workout date |
| Week Number | number | precision: 0 | Training week (1-25) |
| Day of Week | singleSelect | choices: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday | Day of the week |
| Status | singleSelect | choices: Planned, Completed, Skipped, Modified, Missed | Workout completion status |
| Workout Type | singleSelect | choices: Long Run, Easy Run, Tempo Run, Hill Workout, Intervals, Recovery Run, Strength Training, Cross Training, Rest Day | Type of workout |
| Training Phase | singleSelect | choices: Base Building, Build 1, Build 2, Peak, Taper | Training phase |
| Priority | singleSelect | choices: Key Workout, Important, Standard, Optional | Workout priority level |
| Focus Areas | multipleSelects | choices: Endurance, Speed, Hills, Recovery, Nutrition Practice, Gear Testing, Mental Training | Training focus areas |
| Workout Description | multilineText | | Detailed workout instructions |
| Planned Distance | number | precision: 2 | Planned distance in miles |
| Planned Duration | number | precision: 0 | Planned duration in minutes |
| Planned Elevation Gain | number | precision: 0 | Planned elevation gain in feet |
| Target Pace Effort | singleLineText | | Target pace or effort zone |
| Workout Notes | multilineText | | Post-workout reflections and notes |
| Weekly Mileage Target | number | precision: 1 | Total mileage target for the week |
| Weekly Elevation Target | number | precision: 0 | Total elevation target for the week |

### Table 2: Weekly Planning (tbl2B7ecl7heYiKha)

Create the following fields using the Airtable API:

| Field Name | Type | Options | Description |
|------------|------|---------|-------------|
| Week Number | number | precision: 0 (primary field) | Training week (1-25) |
| Week Starting | date | dateFormat: "iso" | Monday of the week |
| Week Ending | date | dateFormat: "iso" | Sunday of the week |
| Training Phase | singleSelect | choices: Base Building, Build 1, Build 2, Peak, Taper | Training phase for this week |
| Weekly Goals | multilineText | | Goals and objectives for the week |
| Mileage Target | number | precision: 1 | Target miles for the week |
| Elevation Target | number | precision: 0 | Target elevation gain for the week |
| Key Workouts | multilineText | | Description of key workouts this week |
| Weekly Reflection | multilineText | | Post-week reflections |
| Challenges | multilineText | | Difficulties encountered this week |
| Wins | multilineText | | Accomplishments this week |
| Energy Level | rating | max: 5 | Overall energy level (1-5) |
| Recovery Quality | rating | max: 5 | How well recovered (1-5) |
| Overall Rating | rating | max: 5 | Overall week satisfaction (1-5) |
| Adjustments Made | multilineText | | Any changes made to the plan |
| Next Week Focus | multilineText | | Looking ahead to next week |
| Notes | multilineText | | General notes |

---

## Task 2: Export Data from Notion

### Source Database
Query all pages from Notion database `9a3c2dd1b2354f2a8e8f330d7fda16c3`

### Field Mapping from Notion to Airtable

| Notion Property | Notion Type | Airtable Field | Notes |
|-----------------|-------------|----------------|-------|
| Name | title | Name | |
| Date | date | Date | Extract start date only |
| Week Number | number | Week Number | |
| Day of Week | select | Day of Week | |
| Status | select | Status | Default to "Planned" if empty |
| Workout Type | select | Workout Type | |
| Training Phase | select | Training Phase | |
| Priority | select | Priority | |
| Focus Areas | multi_select | Focus Areas | Array of values |
| Workout Description | rich_text | Workout Description | Concatenate all text blocks |
| Planned Distance | number | Planned Distance | |
| Planned Duration | number | Planned Duration | |
| Planned Elevation Gain | number | Planned Elevation Gain | |
| Target Pace Effort | rich_text | Target Pace Effort | Concatenate all text blocks |
| Workout Notes | rich_text | Workout Notes | Concatenate all text blocks |
| Weekly Mileage Target | number | Weekly Mileage Target | |
| Weekly Elevation Target | number | Weekly Elevation Target | |

### Expected Record Count
Approximately **175 training activities** (25 weeks × 7 days, minus rest days)

---

## Task 3: Create Weekly Planning Records

Generate **25 weekly planning records** with the following logic:

### Week Calculation
- **Start Date**: January 20, 2026 (Monday)
- **Weeks**: 1 through 25
- **End Date**: July 12, 2026 (Race day is Saturday of week 25)

### Training Phase by Week
- **Weeks 1-8**: Base Building
- **Weeks 9-14**: Build 1
- **Weeks 15-20**: Build 2
- **Weeks 21-22**: Peak
- **Weeks 23-25**: Taper

### Weekly Goals by Phase
- **Base Building**: "Build aerobic base with easy miles and cross-training. Focus on consistency and volume."
- **Build 1**: "Increase volume with hill repeats and back-to-back long runs. Focus on sustained efforts."
- **Build 2**: "Peak mileage weeks with long runs featuring significant elevation. Tempo and hill work."
- **Peak**: "Race simulation and confidence building. Practice race-day gear and nutrition strategy."
- **Taper**: "Reduce volume while maintaining intensity. Prioritize rest and mental preparation for race day."

### Weekly Targets
Calculate from the planned activities for each week:
- **Mileage Target**: Sum of all `Weekly Mileage Target` values for activities in that week (or calculate from planned activities)
- **Elevation Target**: Sum of all `Weekly Elevation Target` values for activities in that week

### Key Workouts
For each week, extract the names of activities where `Priority = "Key Workout"` and format as a bulleted list.

---

## Task 4: Migration Execution Order

1. **Create fields** in both Airtable tables using the schema definitions above
2. **Export all activities** from Notion Training Plan database
3. **Transform data** according to the field mapping
4. **Import activities** to Airtable Planned Training Activities table (use batch operations for efficiency)
5. **Create weekly planning records** (25 records) in Airtable Weekly Planning table
6. **Verify migration**:
   - Count records in each table
   - Check sample records for data integrity
   - Verify all select field values are valid
7. **Save backup** of exported Notion data to JSON file

---

## Data Validation Requirements

### Required Fields (must have values)
- Name
- Date
- Week Number
- Workout Type
- Training Phase

### Optional Fields (can be null/empty)
- Day of Week
- Priority
- Focus Areas
- Workout Description
- All "Planned" metrics (Distance, Duration, Elevation)
- Target Pace Effort
- Workout Notes
- Weekly targets

### Select Field Validation
Ensure all select/multi-select values match the exact choices defined in the table schema. If a Notion value doesn't match, either:
- Map it to the closest valid option
- Skip the field (leave null)
- Log a warning

---

## Success Criteria

- ✅ All fields created in both Airtable tables
- ✅ ~175 training activities imported successfully
- ✅ 25 weekly planning records created
- ✅ All dates properly formatted (YYYY-MM-DD)
- ✅ No data loss from Notion export
- ✅ Backup JSON file created
- ✅ Verification report shows correct counts

---

## Notes for Implementation

- Use Airtable's batch create operations (max 10 records per batch) for efficiency
- Handle API rate limits appropriately
- For rich text fields in Notion, concatenate all text blocks into plain text
- Week numbers should be integers from 1 to 25
- Dates should be ISO format strings (YYYY-MM-DD)
- Save intermediate results (Notion export) before starting Airtable import
- Log all operations for debugging

---

## Error Handling

If any step fails:
1. Log the error with context
2. Save current progress
3. Report which step failed and how many records were processed
4. Create backup of any data in memory before exiting

---

## Post-Migration Tasks (Manual)

After successful migration, the user will need to:
1. Create linked record fields to connect tables:
   - Planned Activities → Weekly Planning (by Week Number)
   - Planned Activities → Completed Sessions (existing table)
   - Planned Activities → Calendar Events (existing table)
2. Set up rollup fields for calculations
3. Create views (Calendar, By Week, By Phase, etc.)
4. Configure automations if desired
