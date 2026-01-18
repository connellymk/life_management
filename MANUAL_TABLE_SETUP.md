# Manual Airtable Table Setup Guide

Based on the detected table IDs in your base:
- **Day Table ID**: `tblHMwUnVg8bA1xoP`
- **Week Table ID**: `tbl2B7ecl7heYiKha`

## Tables to Create

### 1. Calendar Events

**Table Name**: `Calendar Events`

**Fields**:

| Field Name | Type | Options/Description |
|------------|------|---------------------|
| Event ID | Single line text | Primary field - Unique event ID from calendar provider |
| Title | Single line text | Event title/summary |
| Day | Link to another record | Link to **Day** table (single record) |
| Date | Date | Keep for sorting/filtering |
| Start Time | Date with time | Include time |
| End Time | Date with time | Include time |
| Duration (min) | Number | Integer |
| All Day | Checkbox | Is this an all-day event? |
| Calendar | Single select | Options: Personal, School and Research, Work |
| Location | Single line text | |
| Description | Long text | |
| Attendees | Long text | Comma-separated list |
| Status | Single select | Options: Confirmed, Tentative, Cancelled |
| Recurring | Checkbox | |
| Last Synced | Date with time | |

---

### 2. Training Sessions

**Table Name**: `Training Sessions`

**Fields**:

| Field Name | Type | Options/Description |
|------------|------|---------------------|
| Activity ID | Single line text | Primary field - Unique activity ID |
| Activity Name | Single line text | |
| Day | Link to another record | Link to **Day** table (single record) |
| Week | Link to another record | Link to **Week** table (single record) |
| Date | Date | Keep for sorting |
| Start Time | Date with time | |
| Activity Type | Single select | Running, Cycling, Swimming, Strength, Hiking, Walking, Other |
| Duration (min) | Number | Integer |
| Distance (mi) | Number | 2 decimal places |
| Elevation Gain (ft) | Number | Integer |
| Avg HR | Number | Integer, heart rate in bpm |
| Max HR | Number | Integer |
| Avg Pace (min/mi) | Single line text | Format: MM:SS |
| Calories | Number | Integer |
| Training Effect | Number | 1 decimal place |
| Notes | Long text | |
| Source | Single select | Garmin, Strava, Manual |
| Last Synced | Date with time | |

---

### 3. Health Metrics

**Table Name**: `Health Metrics`

**Fields**:

| Field Name | Type | Options/Description |
|------------|------|---------------------|
| Day | Link to another record | Primary field - Link to **Day** table (single record, one per day) |
| Date | Date | Keep for sorting |
| Resting HR | Number | Integer, resting heart rate in bpm |
| HRV | Number | Integer, heart rate variability |
| Steps | Number | Integer |
| Floors Climbed | Number | Integer |
| Active Calories | Number | Integer |
| Total Calories | Number | Integer |
| Sleep Duration (hr) | Number | 1 decimal place |
| Sleep Score | Number | Integer, 0-100 |
| Deep Sleep (min) | Number | Integer |
| REM Sleep (min) | Number | Integer |
| Light Sleep (min) | Number | Integer |
| Stress Level | Number | Integer, 0-100 |
| Body Battery | Number | Integer, 0-100 |
| VO2 Max | Number | 1 decimal place |
| Hydration (oz) | Number | Integer |
| Last Synced | Date with time | |

---

### 4. Body Metrics

**Table Name**: `Body Metrics`

**Fields**:

| Field Name | Type | Options/Description |
|------------|------|---------------------|
| Measurement ID | Single line text | Primary field - Auto-generated or timestamp |
| Day | Link to another record | Link to **Day** table (single record) |
| Date | Date | Keep for sorting |
| Weight (lbs) | Number | 1 decimal place |
| Body Fat % | Number | 1 decimal place |
| Muscle Mass (lbs) | Number | 1 decimal place |
| BMI | Number | 1 decimal place |
| Bone Mass (lbs) | Number | 1 decimal place |
| Water % | Number | 1 decimal place |
| Source | Single select | Garmin Scale, Manual |
| Notes | Long text | |
| Last Synced | Date with time | |

---

### 5. Training Plans

**Table Name**: `Training Plans`

**Fields**:

| Field Name | Type | Options/Description |
|------------|------|---------------------|
| Plan Name | Single line text | Primary field - Name of training plan |
| Race/Event | Single line text | Target race or event |
| Event Date | Date | |
| Start Week | Link to another record | Link to **Week** table (single record) |
| End Week | Link to another record | Link to **Week** table (single record) |
| Total Weeks | Number | Integer |
| Current Phase | Single select | Base Building, Build, Peak, Taper, Recovery, Completed |
| Weekly Mileage Target | Number | Integer |
| Key Workouts | Long text | Description of weekly workouts |
| Priority | Single select | A Race, B Race, C Race |
| Status | Single select | Active, Planned, Completed, Abandoned |
| Notes | Long text | |

---

## Quick Setup Steps

For each table:

1. Click **"Add or import"** → **"Create empty table"**
2. Name the table
3. For each field:
   - Click the **+** button or header dropdown
   - Select the field type
   - Configure options (decimal places, select options, etc.)
   - For "Link to another record" fields:
     - Select the target table (Day or Week)
     - Choose "Limit to a single record" for one-to-one relationships

4. After creating all tables, update your token permissions:
   - Go to https://airtable.com/account
   - Find your Personal Access Token
   - Add the new tables to the token's access list

## Alternative: Simplified Approach

If manual creation is too time-consuming, you can:

1. **Start with just Calendar Events and Training Sessions** (most important)
2. Create the other tables later as needed
3. Test the sync process with these two tables first

## Verify Setup

After creating the tables, run:
```bash
python inspect_tables.py
```

This will verify the tables exist and show their structure.
