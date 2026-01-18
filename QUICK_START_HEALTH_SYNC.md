# Quick Start: Garmin Health Sync to Airtable

## Prerequisites

1. **Garmin Connect Account**
   - Email and password in `.env` file
   ```bash
   GARMIN_EMAIL=your_email@example.com
   GARMIN_PASSWORD=your_password
   ```

2. **Airtable Setup**
   - Personal Access Token in `.env` file
   - Base ID in `.env` file
   - Tables created: Training Sessions, Health Metrics, Body Metrics, Day, Week
   ```bash
   AIRTABLE_ACCESS_TOKEN=pat_...
   AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
   ```

## Quick Test

Run the health check to verify everything is configured:

```bash
python test_health_sync.py
```

You should see:
- ✓ Airtable configuration valid
- ✓ Training Sessions table accessible
- ✓ Health Metrics table accessible
- ✓ Body Metrics table accessible
- ✓ Garmin credentials configured

## First Sync

Sync all your Garmin data to Airtable (last 90 days):

```bash
python orchestrators/sync_health.py
```

This will:
1. Fetch activities from Garmin Connect (last 90 days)
2. Fetch daily health metrics (last 90 days)
3. Fetch body composition measurements (last 30 days)
4. Sync everything to Airtable with Day/Week links

Expected time: ~5-10 minutes for initial sync

## What Gets Synced

### Training Sessions
- Activity name, type, date/time
- Duration, distance, elevation gain
- Heart rate (average, max)
- Pace, speed, calories
- Links to Day table (for daily rollups)
- Links to Week table (for weekly mileage)
- Direct link to Garmin Connect

### Health Metrics (Daily)
- Sleep duration, score, stages (deep, REM, light)
- Steps, floors climbed
- Calories (active, total)
- Heart rate (resting, HRV)
- Stress level, body battery
- Intensity minutes
- Links to Day table

### Body Metrics
- Weight, BMI
- Body fat %, muscle mass
- Bone mass, body water %
- Links to Day table (for weight trends)

## Daily Usage

### Manual Sync

Run anytime to sync latest data:

```bash
python orchestrators/sync_health.py
```

### Preview Before Syncing

See what would be synced without making changes:

```bash
python orchestrators/sync_health.py --dry-run
```

### Sync Specific Data

Only sync workouts:
```bash
python orchestrators/sync_health.py --workouts-only
```

Only sync health metrics:
```bash
python orchestrators/sync_health.py --metrics-only
```

Only sync body composition:
```bash
python orchestrators/sync_health.py --body-only
```

### With SQL Archival

Keep unlimited history in local SQL database:

```bash
python orchestrators/sync_health.py --archive-to-sql
```

This syncs to both Airtable (visual dashboard) and SQL (historical analytics).

## Automated Syncing

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task: "Garmin Health Sync"
3. Trigger: Daily at 7:00 AM
4. Action: Start a program
   - Program: `python`
   - Arguments: `C:\Users\Administrator\Desktop\personal_assistant\orchestrators\sync_health.py`
   - Start in: `C:\Users\Administrator\Desktop\personal_assistant`

### Linux/Mac Cron

Add to crontab (`crontab -e`):

```cron
# Sync health data twice daily (7 AM and 7 PM)
0 7,19 * * * cd /path/to/personal_assistant && python orchestrators/sync_health.py
```

## View Your Data in Airtable

After syncing, open your Airtable base and check:

1. **Training Sessions** table
   - See all your workouts
   - Group by Activity Type or Week
   - View on calendar

2. **Health Metrics** table
   - Daily health data
   - Filter to last 7 or 30 days
   - Create charts for trends

3. **Body Metrics** table
   - Weight and composition measurements
   - Create weight trend chart

4. **Day** table
   - See all activities/metrics for any day
   - Automatic rollups from linked records

5. **Week** table
   - Weekly training summary
   - Total mileage, workout count
   - Average health metrics

## Create Useful Views

### Training Calendar
1. Open Training Sessions table
2. Add Calendar view
3. Configure by "Start Time" field

### This Week's Workouts
1. Add Grid view
2. Filter: Start Time is within "this week"
3. Sort by Start Time descending

### Weekly Mileage
1. Open Week table
2. Add Rollup field: SUM(Training Sessions → Distance)
3. Sort by Week descending

### Sleep Trends
1. Open Health Metrics table
2. Add Chart view
3. X-axis: Date, Y-axis: Sleep Duration

### Weight Trend
1. Open Body Metrics table
2. Add Chart view
3. X-axis: Date, Y-axis: Weight

## Troubleshooting

### "No activities found"
- Check date range (default: last 90 days)
- Verify you have activities in Garmin Connect
- Try authenticating manually (delete `credentials/garmin_tokens`)

### "Table not found"
- Verify table names in `.env` match Airtable
- Check Base ID is correct
- Ensure Day and Week tables exist

### "Authentication failed"
- Check Garmin email/password in `.env`
- Delete cached tokens: `rm credentials/garmin_tokens`
- Re-run sync

### Slow sync
- First sync is slow (fetches 90 days)
- Subsequent syncs are fast (only new data)
- Consider reducing `SYNC_LOOKBACK_DAYS` in `.env`

## Configuration

All settings in `.env` file:

```bash
# Garmin
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_password

# Airtable
AIRTABLE_ACCESS_TOKEN=pat_...
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX

# Table Names (update if different in your base)
AIRTABLE_DAY=Day
AIRTABLE_WEEK=Week
AIRTABLE_TRAINING_SESSIONS=Training Sessions
AIRTABLE_HEALTH_METRICS=Health Metrics
AIRTABLE_BODY_METRICS=Body Metrics

# Sync Settings
SYNC_LOOKBACK_DAYS=90        # How far back to sync
UNIT_SYSTEM=imperial         # imperial or metric

# Optional: SQL archival
DATA_DB_PATH=data.db
```

## Next Steps

1. ✓ Run initial sync
2. Create views in Airtable
3. Set up automated daily sync
4. Link Training Plans to actual sessions
5. Create Weekly Review automation
6. Build custom interfaces

## Support

- Health check: `python test_health_sync.py`
- View logs: `logs/sync.log`
- Full documentation: See `GARMIN_AIRTABLE_MIGRATION.md`

---

**Built with Claude Code**
