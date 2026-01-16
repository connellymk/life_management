# Health Database Setup Guide

This guide walks you through creating the three required Notion databases for syncing Garmin health and training data.

## Overview

You need to create three databases in Notion:

1. **Workouts** - For activities/exercises from Garmin
2. **Daily Metrics** - For daily health summaries (steps, heart rate, stress, etc.)
3. **Body Metrics** - For body composition measurements (weight, body fat %, etc.)

## Step 1: Create Workouts Database

1. In Notion, create a new page called "Workouts" (or any name you prefer)
2. Create a database (inline or full-page)
3. Add the following properties:

| Property Name | Type | Description |
|--------------|------|-------------|
| Name | Title | Workout name (auto-generated) |
| Date | Date | When the workout occurred |
| Activity Type | Select | Type of activity (Run, Bike, Swim, etc.) |
| Duration | Number | Duration in minutes |
| Distance | Number | Distance (in miles for imperial) |
| Calories | Number | Calories burned |
| Avg Heart Rate | Number | Average heart rate (bpm) |
| Max Heart Rate | Number | Maximum heart rate (bpm) |
| Elevation Gain | Number | Elevation gained (in feet for imperial) |
| Avg Pace | Text | Average pace (min/mile for imperial) |
| Avg Speed | Number | Average speed (mph for imperial) |
| Garmin URL | URL | Link to Garmin Connect activity |
| External ID | Text | Garmin activity ID (for deduplication) |
| Synced At | Date | Last sync timestamp |

4. Copy the database ID from the URL:
   - Open the database as a full page
   - The URL will look like: `https://www.notion.so/YOUR_WORKSPACE/1234567890abcdef1234567890abcdef?v=...`
   - Copy the 32-character ID (the part after the last `/` and before the `?`)

## Step 2: Create Daily Metrics Database

1. Create a new page called "Daily Metrics"
2. Create a database with these properties:

| Property Name | Type | Description |
|--------------|------|-------------|
| Name | Title | Date (auto-generated) |
| Date | Date | The day for these metrics |
| Steps | Number | Total steps |
| Distance | Number | Total distance (miles) |
| Calories Active | Number | Active calories burned |
| Calories Total | Number | Total calories burned |
| Floors Climbed | Number | Floors climbed |
| Avg Heart Rate | Number | Average resting heart rate (bpm) |
| Min Heart Rate | Number | Minimum heart rate (bpm) |
| Max Heart Rate | Number | Maximum heart rate (bpm) |
| Stress Avg | Number | Average stress level (0-100) |
| Body Battery Max | Number | Max body battery (0-100) |
| Sleep Duration | Number | Sleep duration (hours) |
| Sleep Score | Number | Sleep quality score (0-100) |
| Moderate Intensity Minutes | Number | Moderate exercise minutes |
| Vigorous Intensity Minutes | Number | Vigorous exercise minutes |
| VO2 Max | Number | VO2 max estimate (optional - not currently synced) |
| External ID | Text | Unique ID for the day (for deduplication) |
| Synced At | Date | Last sync timestamp |

3. Copy the database ID (same process as Step 1)

## Step 3: Create Body Metrics Database

1. Create a new page called "Body Metrics"
2. Create a database with these properties:

| Property Name | Type | Description |
|--------------|------|-------------|
| Name | Title | Date (auto-generated) |
| Date | Date | When the measurement was taken |
| Weight | Number | Body weight (lbs for imperial) |
| BMI | Number | Body Mass Index |
| Body Fat % | Number | Body fat percentage |
| Muscle Mass | Number | Muscle mass (lbs) |
| Bone Mass | Number | Bone mass (lbs) |
| Body Water % | Number | Body water percentage |
| External ID | Text | Unique ID for measurement (for deduplication) |
| Synced At | Date | Last sync timestamp |

3. Copy the database ID

## Step 4: Update .env File

Add the three database IDs to your `.env` file:

```bash
# Replace these placeholders with your actual 32-character database IDs
NOTION_WORKOUTS_DB_ID=your_workouts_database_id_here
NOTION_DAILY_METRICS_DB_ID=your_daily_metrics_database_id_here
NOTION_BODY_METRICS_DB_ID=your_body_metrics_database_id_here
```

Example:
```bash
NOTION_WORKOUTS_DB_ID=1234567890abcdef1234567890abcdef
NOTION_DAILY_METRICS_DB_ID=abcdef1234567890abcdef1234567890
NOTION_BODY_METRICS_DB_ID=567890abcdef1234567890abcdef1234
```

## Step 5: Share Databases with Integration

1. For each database, click the "..." menu in the top right
2. Click "Add connections"
3. Select your Notion integration (the one with the token in your .env)
4. Grant access

## Step 6: Test the Setup

Run the health sync health check:

```bash
cd personal_assistant
python orchestrators/sync_health.py --health-check
```

Expected output:
```
✓ Configuration valid
✓ Garmin connection successful
✓ Workouts database accessible
✓ Daily Metrics database accessible
✓ Body Metrics database accessible
✓ All systems operational
```

## Step 7: Run Initial Sync

Try a dry run first to see what will be synced:

```bash
python orchestrators/sync_health.py --dry-run
```

If that looks good, run the actual sync:

```bash
python orchestrators/sync_health.py
```

This will sync:
- Activities from the last 90 days
- Daily metrics from the last 90 days
- Body composition measurements from the last 30 days

**First sync takes about 5-6 minutes.** Subsequent syncs are much faster (10-15 seconds) as they only fetch new data.

## Optional: Customize Database Views

You can create custom views in each database:

### Workouts Database Views
- **Calendar View** - See workouts by date
- **Gallery View** - View by activity type
- **Timeline View** - Track training progression

### Daily Metrics Database Views
- **Calendar View** - Daily metrics calendar
- **Chart View** - Trend graphs for steps, sleep, stress
- **Table View** - Detailed daily breakdown

### Body Metrics Database Views
- **Chart View** - Weight and body composition trends
- **Table View** - Detailed measurements

## Troubleshooting

### "Database not found" error
- Verify the database ID is exactly 32 characters
- Make sure the database is shared with your integration
- Check that the database ID has no spaces or extra characters

### "Permission denied" error
- The integration needs to be connected to each database
- Go to each database → "..." → "Add connections" → Select your integration

### "Invalid property" error
- Make sure all required properties exist in the database
- Property names must match exactly (case-sensitive)
- Check that property types are correct (Number, Date, Select, etc.)

### No data syncing
- Verify your Garmin credentials in .env are correct
- Check that you have activities in Garmin Connect
- Make sure the date range covers your activities

## What's Next

After setup is complete:

1. **Update cron jobs** to run health sync twice daily:
   ```bash
   0 7,19 * * * cd /Users/marykate/Desktop/personal_assistant && venv/bin/python orchestrators/sync_health.py >> logs/cron_health.log 2>&1
   ```

2. **Create a Notion dashboard** combining Calendar Events, Tasks, Workouts, and Daily Metrics

3. **Explore the data** - You now have a comprehensive view of your schedule, training, and health!
