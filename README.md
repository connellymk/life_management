# Personal Assistant System

A unified personal productivity system that syncs data from multiple sources (Google Calendar, Garmin Connect, Plaid Banking) using a hybrid storage architecture (Airtable + SQL), enabling AI-powered life management with Claude.

## Overview

This system uses a **hybrid storage architecture** combining Airtable and SQL databases:
- **Airtable**: Visual dashboards with relational database features (calendar events, workouts, tasks, training plans)
- **SQL**: Unlimited historical data for long-term analytics (optional archival of data older than 90 days)

This gives you the best of both worlds: powerful visual interfaces with rollups and relationships, plus unlimited storage for historical analysis.

### Integrations

1. **Google Calendar** → Airtable Calendar Events
   - Multi-calendar support
   - Timezone-aware sync (Mountain Time for Bozeman, MT)
   - All-day and timed event handling
   - Duplicate prevention with Event ID tracking
   - Links to Day table for rollups and aggregations
   - **Status**: ✅ Production Ready

2. **Garmin Connect** → Airtable (with SQL archival option)
   - **Training Sessions** → Airtable (workouts with performance metrics)
   - **Training Plans** → Airtable (planned workouts, compare to actuals)
   - **Health Metrics** → Airtable (daily health data: sleep, HR, stress, steps)
   - **Body Metrics** → Airtable (weight, body composition)
   - Links to Day and Week tables for weekly rollups
   - Imperial units (miles, lbs, feet)
   - **Status**: ⚙️ In Development

3. **Plaid Banking** → SQL Database
   - Bank accounts, credit cards, investments (encrypted tokens)
   - Transactions (unlimited history)
   - Daily balance snapshots (net worth tracking)
   - Investment holdings and performance
   - **Security**: Encrypted tokens, masked account numbers, local storage only
   - **Status**: ✅ Production Ready (SQL only, Airtable summary view optional)

## Quick Links

- [Airtable Structure Plan](airtable_structure_plan.md) - Complete Airtable base structure and schema
- [Airtable Setup Guide](AIRTABLE_SETUP.md) - Personal Access Token setup and authentication
- [Airtable Setup Complete](AIRTABLE_SETUP_COMPLETE.md) - Current setup status and next steps
- [Financial Security Plan](FINANCIAL_SECURITY_PLAN.md) - Security architecture for financial data

## Architecture

```
personal_assistant/
├── core/                    # Shared utilities
│   ├── config.py           # Unified configuration
│   ├── database.py         # SQLite database management
│   ├── secure_storage.py   # Encrypted token storage
│   ├── state_manager.py    # SQLite state tracking
│   └── utils.py            # Logging, retry, rate limiting
│
├── integrations/           # External data sources
│   ├── google_calendar/    # Google Calendar API client
│   │   └── sync.py        # Calendar event fetching
│   ├── garmin/            # Garmin Connect API client
│   │   └── sync.py        # Health and activity data fetching
│   └── plaid/             # Plaid banking API client
│       └── sync.py        # Financial data fetching
│
├── storage/               # SQL storage modules
│   ├── financial.py       # Financial data CRUD operations
│   ├── health.py          # Health data CRUD operations
│   └── queries.py         # Pre-built analytics queries
│
├── airtable/              # Airtable database operations
│   ├── base_client.py     # Airtable API client
│   ├── date_utils.py      # Date/time conversion utilities
│   ├── calendar.py        # Calendar Events sync
│   └── health.py          # Training Sessions, Health Metrics, Body Metrics sync
│
├── orchestrators/         # Main sync scripts
│   ├── sync_calendar.py   # Run calendar sync (Airtable)
│   ├── sync_health.py     # Run health sync (Airtable)
│   ├── sync_financial.py  # Run financial sync (SQL only)
│   └── setup_plaid.py     # Link bank accounts
│
├── scripts/               # Utility scripts
│   └── init_database.py   # Initialize SQL database
│
├── .env                   # Configuration (credentials, base/table names)
├── state.db              # SQLite state database
├── data.db               # SQLite data database (financial + optional health archival)
└── README.md             # This file
```

## Storage Strategy

### Airtable Base (Visual Dashboard + Relational Database)

**Core Dimension Tables:**
1. **Day** - Central date dimension (ISO format: 2026-01-17)
   - Links all daily data for powerful rollups
   - Connects to Week, Month, Quarter, Year tables

2. **Week** - Weekly planning dimension (format: "3-26")
   - Weekly training plan overview
   - Rollups for weekly summaries

**Calendar & Tasks:**
3. **Calendar Events** - Synced from Google Calendar
   - Title, Start/End Time, Calendar Source (Personal, School, Work)
   - All-day and timed events
   - Links to Day table for daily rollups
   - Location, Attendees, Status

4. **Tasks** - Manual task management
   - Name, Due Date, Status, Priority
   - Links to Projects, Classes

5. **Projects** - Project tracking with task rollups

6. **Classes** - Course tracking with related tasks

**Health & Training:**
7. **Training Sessions** - Actual workouts from Garmin
   - Activity Type, Duration, Distance, Pace, Heart Rate
   - Links to Day and Week for rollups
   - Elevation, Calories, Training Effect

8. **Training Plans** - Planned workouts
   - Compare planned vs actual
   - Link to completed Training Session
   - Weekly mileage targets

9. **Health Metrics** - Daily health data
   - Sleep (duration, score, stages)
   - Activity (steps, floors, calories)
   - Recovery (HRV, stress, body battery)

10. **Body Metrics** - Body composition
    - Weight, body fat %, muscle mass, BMI

**Meal Planning:**
11. **Meal Plans** - Weekly meal plans
12. **Planned Meals** - Individual meals (links recipes to days)
13. **Recipes** - Recipe library
14. **Grocery Items** - Shopping lists

**Financial (Summary View - Optional):**
15. **Accounts** - Account summary (last 90 days)
16. **Transactions** - Recent transactions (last 90 days)
17. **Finance Summary** - Monthly rollups

**Weekly Reviews:**
18. **Weekly Reviews** - Weekly reflection with automatic rollups
19. **Sync Logs** - Integration health monitoring

**Why Airtable?**
- True relational database (foreign keys, rollups, lookups)
- Rich formula language and automations
- Multiple view types (Kanban, Calendar, Gallery, Timeline)
- Better collaboration and real-time updates
- Custom interfaces without code
- 100k records per base (plenty for 90-day rolling window)

### SQL Database (Long-term Analytics - Optional)

**Financial Data (data.db) - Required:**
- `accounts` - Bank accounts, credit cards, investments
- `transactions` - All transactions (unlimited history)
- `balances` - Daily balance snapshots (net worth tracking)
- `investments` - Investment holdings snapshots

**Health Data (data.db) - Optional Archival:**
- `daily_metrics` - Historical health data (>90 days)
- `body_metrics` - Historical body composition (>90 days)
- `training_sessions` - Historical workouts (>90 days)

**Why Keep SQL for Financial?**
- Unlimited transaction history (10+ years)
- 30-500x faster queries for complex analytics
- Privacy: Financial data stays local
- No cloud storage or API limits

## Integration

### Unified Dashboard

**Airtable Interfaces:**
Create custom Airtable interfaces with:
- **Daily Dashboard**: Calendar events, tasks for today, recent workouts, health metrics
- **Weekly Planning**: Upcoming week overview with training plan, meal plan, key tasks
- **Training Dashboard**: Workout log with planned vs actual comparison, weekly mileage rollups
- **Health Dashboard**: Sleep trends, activity charts, recovery metrics
- **Financial Dashboard** (optional): Recent transactions, spending by category, account balances

**Claude Integration:**
Claude can interact with your data through:
- **Airtable API**: Query recent data (last 90 days) for visual insights and planning
- **SQL Database**: Query unlimited financial history for deep analytics
- **Combined Insights**: Pull from both systems for comprehensive life management

Share your Airtable base with Claude for powerful AI-assisted planning and analysis.

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

**Financial Analysis** (SQL queries):
```
Analyze my spending by category over the last 6 months. What are my trends?
Show me my net worth trend over the last year.
Find all transactions over $100 in the last 30 days.
Compare this month's spending to last month.
```

**Health Analytics** (SQL queries):
```
Show me my weekly activity summary for the last 4 weeks.
Is there a correlation between my sleep and next-day activity?
What are my stress patterns by day of week?
How has my resting heart rate trended over 90 days?
```

**Combined Insights**:
```
Check my calendar and workouts from Notion. Review my health metrics from SQL.
Am I training consistently? Should I take a recovery day based on stress levels?
```

## Running Syncs

### Prerequisites

- Windows/Mac with Python 3.9+
- Google account with Google Calendar
- Garmin Connect account (for health sync)
- Plaid account (for financial sync - free sandbox available)
- Airtable account with Personal Access Token

### First-Time Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize SQL database**:
   ```bash
   python scripts/init_database.py
   ```
   This creates `data.db` with all required tables for financial and health data.

3. **Set up Airtable base**:
   - Create an Airtable Personal Access Token at https://airtable.com/create/tokens
   - Follow [AIRTABLE_SETUP.md](AIRTABLE_SETUP.md) for authentication setup
   - See [airtable_structure_plan.md](airtable_structure_plan.md) for complete table schema
   - Tables can be created manually or via API (see AIRTABLE_SETUP_COMPLETE.md for current status)

4. **Configure credentials** in `.env` file:
   ```bash
   AIRTABLE_ACCESS_TOKEN=pat_your_token_here
   AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
   # ... other credentials
   ```

### On-Demand Sync

Navigate to the project directory:

```bash
cd personal_assistant
```

#### Calendar Sync (Airtable)

First, ensure Airtable Calendar Events table is set up with Day table links.

**Run sync** (sync all calendars to Airtable):
```bash
python orchestrators/sync_calendar.py
```

**Dry run** (preview events without creating/updating in Airtable):
```bash
python orchestrators/sync_calendar.py --dry-run
```

**Health check** (verify Airtable configuration):
```bash
python orchestrators/sync_calendar.py --health-check
```

**Sync specific date range**:
```bash
python orchestrators/sync_calendar.py --start-date 2026-01-01 --end-date 2026-12-31
```

**Full refresh** (force re-sync all events, ignoring state):
```bash
python orchestrators/sync_calendar.py --force-refresh
```

#### Health Sync (Airtable)

First, ensure Airtable tables are set up (Training Sessions, Health Metrics, Body Metrics).

**Run sync** (activities and metrics to Airtable):
```bash
python orchestrators/sync_health.py
```

**Sync activities only**:
```bash
python orchestrators/sync_health.py --workouts-only
```

**Sync metrics only**:
```bash
python orchestrators/sync_health.py --metrics-only
```

**Dry run** (preview without making changes):
```bash
python orchestrators/sync_health.py --dry-run
```

**Health check** (verify Airtable configuration):
```bash
python orchestrators/sync_health.py --health-check
```

**Note**: Health sync to Airtable is currently in development. SQL database sync for health metrics is available as a fallback.

#### Financial Sync (SQL Only)

Financial data syncs directly to SQL database (no Notion setup required).

**Setup (link bank accounts)**:
```bash
python orchestrators/setup_plaid.py
```

**Run sync** (to SQL database):
```bash
python orchestrators/sync_financial.py
```

**Dry run** (preview without making changes):
```bash
python orchestrators/sync_financial.py --dry-run
```

**Health check** (verify SQL database):
```bash
python orchestrators/sync_financial.py --health-check
```

**Sync specific data only**:
```bash
python orchestrators/sync_financial.py --accounts-only
python orchestrators/sync_financial.py --transactions-only
python orchestrators/sync_financial.py --balances-only
python orchestrators/sync_financial.py --investments-only
```

### Automated Syncing (Optional)

Set up automated syncs to keep your Airtable and SQL databases up to date.

**Windows (Task Scheduler)**:
1. Open Task Scheduler
2. Create tasks with these schedules:
   - **Calendar Sync**: Every 5-15 minutes
     - Action: `python C:\path\to\personal_assistant\orchestrators\sync_calendar.py`
   - **Health Sync**: Twice daily (7 AM, 7 PM)
     - Action: `python C:\path\to\personal_assistant\orchestrators\sync_health.py`
   - **Financial Sync**: Daily (7 AM)
     - Action: `python C:\path\to\personal_assistant\orchestrators\sync_financial.py`

**Mac/Linux (cron)**:
```bash
# Edit crontab
crontab -e

# Add these lines:

# Calendar - every 5 minutes (Airtable)
*/5 * * * * cd /path/to/personal_assistant && python orchestrators/sync_calendar.py >> logs/cron_calendar.log 2>&1

# Health - twice daily
0 7,19 * * * cd /path/to/personal_assistant && python orchestrators/sync_health.py >> logs/cron_health.log 2>&1

# Financial - daily at 7 AM
0 7 * * * cd /path/to/personal_assistant && python orchestrators/sync_financial.py >> logs/cron_financial.log 2>&1
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

### Financial Sync
- ⚙️ Bank account and credit card tracking
- ⚙️ Transaction sync (30 days rolling, with categories)
- ⚙️ Daily balance snapshots (net worth tracking)
- ⚙️ Investment holdings and performance
- ⚙️ Bill tracking (recurring payments)
- 🔐 Encrypted access token storage (Fernet encryption)
- 🔐 Masked account numbers (last 4 digits only)
- 🔐 Secure logging (sensitive data redacted)
- 🔐 HTTPS-only API communication
- ⚠️ Sandbox testing available (free Plaid account)

## Performance

**Calendar Sync** (Airtable):
- First sync: ~3-5 minutes (350+ events with Day table linking)
- Subsequent syncs: ~5-10 seconds (incremental with Event ID tracking)
- Timezone handling: Mountain Time (America/Denver) with UTC storage
- Recommended: Every 5-15 minutes (automated) or on-demand

**Health Sync** (Airtable):
- First sync: ~5-10 minutes (activities + metrics with Day/Week linking)
- Subsequent syncs: ~10-20 seconds (new activities and daily metrics)
- Data retention: Last 90 days in Airtable (optional archival to SQL)
- Recommended: Twice daily (7 AM, 7 PM) or on-demand
- Status: ⚙️ In development

**Financial Sync** (SQL):
- First sync: ~5-10 seconds (accounts + unlimited transactions)
- Subsequent syncs: ~2-5 seconds (only new transactions)
- Query performance: 30-500x faster than API-based systems
- Recommended: Daily (7 AM automated) or on-demand

**Airtable Benefits:**
- Rich relational queries with rollups and lookups (instant)
- Multiple view types without custom code
- Real-time collaboration and updates
- Native mobile apps for on-the-go access
- 5 requests/second rate limit (rarely hit with smart caching)

## Security

**General Security**:
- All credentials stored in `.env` files (gitignored)
- OAuth tokens cached locally
- No credentials committed to git
- Session tokens auto-refresh

**Financial Security** (see [FINANCIAL_SECURITY_PLAN.md](FINANCIAL_SECURITY_PLAN.md)):
- All financial data stored locally in SQL database (never in cloud/Notion)
- Plaid access tokens encrypted with Fernet (AES-128)
- Encryption keys stored with restrictive permissions (600)
- Full account numbers NEVER stored - only last 4 digits
- Sensitive data redacted from logs
- Database files protected with owner-only permissions
- HTTPS enforced for all API calls
- SQL injection prevention via parameterized queries

## Future Enhancements

Potential additions:
- **Phase 4 (Optional)**: Notion summaries for financial data
  - Recent transactions (last 30 days) synced to Notion for quick viewing
  - Monthly spending summaries
  - Net worth snapshots
  - Best of both worlds: SQL for history/analysis + Notion for dashboards
- Microsoft Calendar integration (MSU student/employee calendars)
- Strava integration (alternative to Garmin)
- GitHub issues as tasks
- Email integration (Gmail)
- Bidirectional sync (edit in Notion → update source)
- Interactive analytics dashboard
- Weather data for workouts

## Troubleshooting

### Configuration Issues

**"Configuration not valid" error**:
- Run health check: `python orchestrators/sync_calendar.py --health-check`
- Check `.env` file has all required values
- Verify database IDs are exactly 32 characters

**Airtable connection fails**:
- Verify token starts with `pat_` (Personal Access Token)
- Check token has required scopes: `data.records:read`, `data.records:write`, `schema.bases:read`
- Ensure token has access to your specific base
- Verify Base ID starts with `app` and is 17 characters
- Test connection: `python test_airtable.py`

**Google Calendar auth fails**:
- Delete `credentials/google_token.json` and re-authenticate
- Check `credentials/google_client_secret.json` exists
- Verify OAuth consent screen is configured

**Garmin connection fails**:
- Verify email and password in `.env` are correct
- Check Garmin Connect is accessible in browser
- Try running health check to see detailed error

**Plaid connection fails**:
- Check `PLAID_CLIENT_ID` and `PLAID_SECRET` in `.env`
- Verify environment is set correctly (sandbox/production)
- Run health check: `python orchestrators/sync_financial.py --health-check`
- Check Plaid Dashboard for API status

**No bank accounts linked**:
- Run setup script: `python orchestrators/setup_plaid.py`
- Complete Plaid Link flow in browser
- Verify items appear in Plaid Dashboard

**Financial sync errors**:
- Check SQL database is initialized: `python scripts/init_database.py`
- Verify schema: `python orchestrators/sync_financial.py --health-check`
- Run with `--dry-run` to preview what would sync

**Database not initialized**:
```bash
python scripts/init_database.py
```

**Check data counts**:
```bash
python -c "from core.database import Database; db = Database(); print(db.get_table_counts())"
```

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

- ✅ **Airtable Base Setup**: Complete (Day/Week dimensions + 5 core tables with fields)
- ✅ **Calendar Sync**: Production ready (Google Calendar → Airtable with Day linking)
- ⚙️ **Health Sync**: In development (Garmin → Airtable Training Sessions, Health Metrics, Body Metrics)
- ✅ **Financial Sync**: Production ready (Plaid → SQL database with unlimited history)
- ✅ **Hybrid Architecture**: Complete (SQL + Airtable)
- ⏳ **Future integrations**: Planned (see Future Enhancements)

## Current Data

**Airtable (Visual Dashboard):**
- Base ID: appKYFUTDs7tDg4Wr
- Day Table: ISO format dates with Week/Month/Quarter/Year relationships
- Week Table: Format "W-YY" for weekly planning
- Calendar Events: ✅ Synced (timezone-aware, links to Day table)
- Training Sessions: Table ready, sync in development
- Health Metrics: Table ready, sync in development
- Body Metrics: Table ready, sync in development
- Training Plans, Tasks, Projects, Classes: Tables created, awaiting field setup

**SQL Database (Long-term Analytics):**
- Financial Data: Ready for sync (accounts, transactions, balances, investments)
- Health Data (Optional Archival): Tables available for data older than 90 days

---

**Built with Claude Code**

Each module is independently functional and can be used standalone or together for comprehensive life management with AI assistance.
