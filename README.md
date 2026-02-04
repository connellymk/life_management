# Personal Assistant System

A unified personal productivity system that syncs data from multiple sources (Google Calendar, Garmin Connect) to Notion, enabling AI-powered life management with Claude.

## Overview

This system syncs external data sources to Notion databases:
- **Calendar Events**: Google Calendar → Notion
- **Health & Training**: Garmin Connect → Notion (Activities + Daily Tracking)

### Integrations

1. **Google Calendar** → Notion Calendar Events
   - Multi-calendar support (Personal, School, Work, etc.)
   - Timezone-aware sync (Mountain Time)
   - All-day and timed event handling
   - Duplicate prevention with Event ID tracking
   - **Status**: ✅ Production Ready

2. **Garmin Connect** → Notion
   - **Garmin Activities** → Workouts with performance metrics
   - **Daily Tracking** → Daily health data (steps, sleep, stress, body metrics)
   - Imperial units (miles, lbs, feet)
   - **Status**: ✅ Production Ready

## Architecture

```
personal_assistant/
├── core/                    # Shared utilities
│   ├── config.py           # Unified configuration
│   └── utils.py            # Logging, retry, rate limiting
│
├── integrations/           # External data sources
│   ├── google_calendar/    # Google Calendar API client
│   │   └── sync.py        # Calendar event fetching
│   └── garmin/            # Garmin Connect API client
│       └── sync.py        # Health and activity data fetching
│
├── notion/                # Notion database operations
│   ├── calendar.py        # Calendar Events sync
│   └── health.py          # Garmin Activities + Daily Tracking sync
│
├── orchestrators/         # Main sync scripts
│   ├── sync_calendar.py   # Run calendar sync (Notion)
│   └── sync_health.py     # Run health sync (Notion)
│
├── .env                   # Configuration (credentials, database IDs)
└── README.md             # This file
```

## Notion Databases

### Calendar Events
- Title, Start/End Time, Calendar Source
- All-day and timed events
- Location, Attendees, Status

### Garmin Activities
- Activity Type, Duration, Distance, Pace, Heart Rate
- Elevation, Calories
- Direct links to Garmin Connect

### Daily Tracking
- Steps, Floors Climbed, Calories
- Sleep Duration, Sleep Score
- Resting HR, Stress Level, Body Battery
- Weight, Body Fat %, Muscle Mass

## Running Syncs

### Prerequisites

- Mac/Linux/Windows with Python 3.9+
- Google account with Google Calendar
- Garmin Connect account (for health sync)
- Notion Integration with access to your databases

### First-Time Setup

1. **Create and activate a virtual environment**:
   ```bash
   # Create virtual environment
   python3 -m venv venv

   # Activate virtual environment
   # On Mac/Linux:
   source venv/bin/activate
   # On Windows:
   # venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure credentials** in `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

### On-Demand Sync

#### Calendar Sync (Notion)

```bash
# Run sync
python orchestrators/sync_calendar.py

# Dry run (preview without changes)
python orchestrators/sync_calendar.py --dry-run

# Health check
python orchestrators/sync_calendar.py --health-check

# Sync specific date range
python orchestrators/sync_calendar.py --start-date 2026-01-01 --end-date 2026-12-31
```

#### Health Sync (Notion)

```bash
# Run full sync
python orchestrators/sync_health.py

# Sync activities only
python orchestrators/sync_health.py --workouts-only

# Sync daily metrics only
python orchestrators/sync_health.py --metrics-only

# Sync body metrics only
python orchestrators/sync_health.py --body-only

# Dry run
python orchestrators/sync_health.py --dry-run

# Health check
python orchestrators/sync_health.py --health-check

# Sync specific date range
python orchestrators/sync_health.py --start-date 2026-01-01 --end-date 2026-01-31
```

### Automated Syncing (Optional)

**Mac/Linux (cron)**:
```bash
crontab -e

# Calendar - every 15 minutes
*/15 * * * * cd /path/to/personal_assistant && python orchestrators/sync_calendar.py >> logs/cron_calendar.log 2>&1

# Health - twice daily
0 7,19 * * * cd /path/to/personal_assistant && python orchestrators/sync_health.py >> logs/cron_health.log 2>&1
```

## Security

- All credentials stored in `.env` files (gitignored)
- OAuth tokens cached locally
- No credentials committed to git

## Troubleshooting

**Configuration not valid**:
- Run health check for the relevant sync
- Check `.env` file has all required values

**Notion connection fails**:
- Verify token starts with `ntn_` or `secret_`
- Check integration has access to your databases

**Google Calendar auth fails**:
- Delete `credentials/google_token.json` and re-authenticate
- Check `credentials/google_client_secret.json` exists

**Garmin connection fails**:
- Verify email and password in `.env` are correct
- Check Garmin Connect is accessible in browser

---

**Built with Claude Code**
