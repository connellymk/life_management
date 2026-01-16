# Personal Assistant System

A unified personal productivity system that syncs data from multiple sources (Google Calendar, Garmin Connect) into Notion, enabling AI-powered life management with Claude.

## Overview

This system uses a modular architecture to integrate multiple data sources into Notion for comprehensive life management.

### Integrations

1. **Google Calendar** → Notion Calendar Events
   - Multi-calendar support
   - Incremental sync with state management
   - Selective updates (preserves manual edits)
   - Duplicate prevention
   - **Status**: ✅ Production Ready

2. **Garmin Connect** → Notion Health Databases
   - Workouts/activities tracking (90 days history)
   - Daily health metrics (steps, sleep, heart rate, stress, body battery)
   - Sleep scores and intensity minutes
   - Body composition (weight, BMI, body fat)
   - Imperial units (miles, lbs, feet)
   - **Status**: ✅ Production Ready

## Quick Links

- [Health Database Setup](HEALTH_DATABASE_SETUP.md) - Create Notion databases for Garmin sync

## Architecture

```
personal_assistant/
├── core/                    # Shared utilities
│   ├── config.py           # Unified configuration
│   ├── state_manager.py    # SQLite state tracking
│   └── utils.py            # Logging, retry, rate limiting
│
├── integrations/           # External data sources
│   ├── google_calendar/    # Google Calendar API client
│   └── garmin/            # Garmin Connect API client
│
├── notion/                # Notion database operations
│   ├── calendar.py        # Calendar Events database
│   └── health.py          # Workouts, Daily Metrics, Body Metrics
│
├── orchestrators/         # Main sync scripts
│   ├── sync_calendar.py   # Run calendar sync
│   └── sync_health.py     # Run health sync
│
├── .env                   # Configuration (credentials, database IDs)
├── state.db              # SQLite state database
└── README.md             # This file
```

## Notion Database Structure

### Calendar Sync Databases

1. **Calendar Events** - Synced from Google Calendar
   - Title, Start Time, End Time
   - Source (Personal, School, Work)
   - Location, Attendees
   - URL (link to Google Calendar)
   - Sync Status, Last Synced

2. **Tasks** - Manual task management
   - Name, Due Date, Status
   - Classes (relation to Classes database)

3. **Classes** - Course tracking
   - Class name, Semester, Instructor
   - Grade, Credits
   - Task List (relation to Tasks)

### Health Training Databases

1. **Workouts** - Activities from Garmin
   - Title, Date, Activity Type
   - Duration, Distance, Elevation
   - Heart Rate, Calories, Pace
   - Link to Garmin Connect

2. **Daily Metrics** - Daily health summaries
   - Date, Steps, Sleep Hours
   - Resting HR, Stress Level
   - Active Calories

3. **Body Metrics** - Body composition
   - Date, Weight, BMI
   - Body Fat %, Muscle Mass
   - Bone Mass, Body Water %

## Integration

### Unified Dashboard

Create one Notion page with linked views of all databases:
- Calendar Events (upcoming meetings/events)
- Tasks (assignments and todos)
- Workouts (recent training)
- Daily Metrics (health trends)

Share this single page with Claude for comprehensive life management.

### Claude Use Cases

**Scheduling**:
```
Look at my calendar and tasks. I need to:
- Find 3 hours this week for my CSCI assignment
- Schedule 4 workouts (prefer mornings)
- Block time for office hours

What's the best schedule?
```

**Training Analysis**:
```
Check my workouts and sleep data. Am I training consistently?
Should I take a recovery day based on my recent stress levels?
```

**Time Management**:
```
Analyze my week: meetings, tasks, workouts. Am I overcommitted?
Where can I find time for a 2-hour deep work session?
```

**Performance Tracking**:
```
Compare my running pace over the last month. Am I improving?
Is there any correlation with my sleep or training frequency?
```

## Running Syncs

### Prerequisites

- Windows/Mac with Python 3.9+
- Google account with Google Calendar
- Garmin Connect account (for health sync)
- Notion account with integration set up

### On-Demand Sync

Navigate to the project directory:

```bash
cd personal_assistant
```

#### Calendar Sync

**Run sync**:
```bash
python orchestrators/sync_calendar.py
```

**Dry run** (preview without making changes):
```bash
python orchestrators/sync_calendar.py --dry-run
```

**Health check** (verify configuration):
```bash
python orchestrators/sync_calendar.py --health-check
```

#### Health Sync

First, create the required Notion databases by following [HEALTH_DATABASE_SETUP.md](HEALTH_DATABASE_SETUP.md).

**Run sync**:
```bash
python orchestrators/sync_health.py
```

**Dry run** (preview without making changes):
```bash
python orchestrators/sync_health.py --dry-run
```

**Health check** (verify configuration):
```bash
python orchestrators/sync_health.py --health-check
```

### Automated Syncing (Optional)

**Windows (Task Scheduler)**:
- Calendar Sync: Every 5 minutes
- Health Sync: Twice daily (7 AM, 7 PM)

**Mac/Linux (cron)**:
```bash
# Calendar - every 5 minutes
*/5 * * * * cd /path/to/personal_assistant && python orchestrators/sync_calendar.py >> logs/cron_calendar.log 2>&1

# Health - twice daily
0 7,19 * * * cd /path/to/personal_assistant && python orchestrators/sync_health.py >> logs/cron_health.log 2>&1
```

## Features

### Calendar Sync
- ✅ Multi-calendar support (Personal, School, Work, etc.)
- ✅ Incremental sync (10x faster after first sync)
- ✅ Selective updates (preserves manual edits in Notion)
- ✅ Duplicate prevention with state management
- ✅ All-day event handling
- ✅ Attendee tracking
- ✅ OAuth 2.0 authentication with token caching

### Health Sync
- ✅ Workout tracking (runs, rides, swims, strength, etc.) - 90 days
- ✅ Daily health metrics (steps, sleep, heart rate, stress, body battery) - 90 days
- ✅ Sleep scores and intensity minutes
- ✅ Body composition tracking (weight, BMI, body fat %, muscle mass)
- ✅ Imperial units (miles, lbs, feet)
- ✅ Duplicate prevention with state management
- ✅ Direct links to Garmin Connect activities
- ✅ Activity type mapping (Run, Ride, Swim, Walk, Strength)
- ✅ Average speed calculations

## Performance

**Calendar Sync**:
- First sync: ~5-6 minutes (362 events with duplicate checking)
- Subsequent syncs: ~3-5 seconds (incremental with sync tokens)
- Recommended: Every 5 minutes (automated) or on-demand

**Health Sync**:
- First sync: ~5-6 minutes (90 days of data - 42 workouts + 91 daily metrics)
- Subsequent syncs: ~10-15 seconds (only new data)
- Recommended: Twice daily or on-demand

## Security

- All credentials stored in `.env` files (gitignored)
- OAuth tokens cached locally
- No credentials committed to git
- Session tokens auto-refresh

## Future Enhancements

Potential additions:
- Microsoft Calendar integration (MSU student/employee calendars)
- Strava integration (alternative to Garmin)
- GitHub issues as tasks
- Email integration (Gmail)
- Bidirectional sync (edit in Notion → update source)
- Analytics dashboard
- Conflict detection
- Weather data for workouts

## Troubleshooting

### Configuration Issues

**"Configuration not valid" error**:
- Run health check: `python orchestrators/sync_calendar.py --health-check`
- Check `.env` file has all required values
- Verify database IDs are exactly 32 characters

**Notion connection fails**:
- Verify token starts with `secret_` or `ntn_`
- Check databases are shared with your Notion integration
- Test connection with health check command

**Google Calendar auth fails**:
- Delete `credentials/google_token.json` and re-authenticate
- Check `credentials/google_client_secret.json` exists
- Verify OAuth consent screen is configured

**Garmin connection fails**:
- Verify email and password in `.env` are correct
- Check Garmin Connect is accessible in browser
- Try running health check to see detailed error

### Duplicate Events

If you see duplicate events in Notion:
1. Clear all events from the Notion database
2. Reset the state database:
   ```bash
   python fix_calendar_sync.py
   ```
3. Run the sync again to create fresh data

The sync tracks events using External IDs and a state database to prevent duplicates.

### General Issues

**Module won't run**:
- Check Python version: `python --version` (should be 3.9+)
- Verify dependencies installed: `pip list | grep notion`
- Install requirements if needed: `pip install -r requirements.txt`

**Logs not showing**:
- Check `logs/` directory exists
- Verify LOG_PATH in `.env` is correct
- View logs: `tail -f logs/sync.log`

## Project Status

- ✅ **Calendar Sync**: Production ready (362 events synced)
- ✅ **Health Sync**: Production ready (42 workouts + 91 days of metrics synced)
- ✅ **Unified architecture**: Complete
- ⏳ **Future integrations**: Planned (see Future Enhancements)

## Current Data

- **Calendar Events**: 362 events (2 calendars, Oct 2025 - Jan 2027)
- **Workouts**: 42 activities (90 days history)
- **Daily Metrics**: 91 days of health data
- **Body Metrics**: 0 measurements (no data available from Garmin)

---

**Built with Claude Code**

Each module is independently functional and can be used standalone or together for comprehensive life management with AI assistance.
