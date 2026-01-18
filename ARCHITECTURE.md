# Personal Assistant System Architecture

## Overview

The Personal Assistant System is a unified productivity platform that syncs data from multiple sources into a hybrid storage architecture combining **Airtable** (visual dashboard with relational features) and **SQL** (unlimited historical data).

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                  DATA SOURCES                        │
├──────────────┬──────────────┬───────────────────────┤
│ Google       │ Garmin       │ Plaid Banking         │
│ Calendar     │ Connect      │                       │
└──────┬───────┴──────┬───────┴──────┬────────────────┘
       │              │              │
       ▼              ▼              ▼
┌─────────────────────────────────────────────────────┐
│              SYNC ORCHESTRATORS                      │
├──────────────┬──────────────┬───────────────────────┤
│ sync_        │ sync_        │ sync_                 │
│ calendar.py  │ health.py    │ financial.py          │
└──────┬───────┴──────┬───────┴──────┬────────────────┘
       │              │              │
       ▼              ▼              ▼
┌─────────────────────────────────────────────────────┐
│         STORAGE LAYER (HYBRID)                      │
├────────────────────────┬────────────────────────────┤
│    AIRTABLE            │    SQL (data.db)           │
│  ┌──────────────────┐  │  ┌──────────────────────┐ │
│  │ Day/Week Tables  │  │  │ Transactions         │ │
│  │ (Dimensions)     │  │  │ (Unlimited History)  │ │
│  ├──────────────────┤  │  ├──────────────────────┤ │
│  │ Calendar Events  │  │  │ Accounts             │ │
│  ├──────────────────┤  │  ├──────────────────────┤ │
│  │ Training         │  │  │ Balances             │ │
│  │ Sessions         │  │  │ (Daily Snapshots)    │ │
│  ├──────────────────┤  │  ├──────────────────────┤ │
│  │ Training Plans   │  │  │ Investments          │ │
│  ├──────────────────┤  │  └──────────────────────┘ │
│  │ Health Metrics   │  │                            │
│  ├──────────────────┤  │  Optional Archival:        │
│  │ Body Metrics     │  │  ┌──────────────────────┐ │
│  ├──────────────────┤  │  │ Historical Health    │ │
│  │ Tasks, Projects  │  │  │ Data (>90 days)      │ │
│  │ Classes          │  │  └──────────────────────┘ │
│  ├──────────────────┤  │                            │
│  │ Weekly Reviews   │  │                            │
│  └──────────────────┘  │                            │
└────────────────────────┴────────────────────────────┘
```

## Storage Strategy

### Airtable: Visual Dashboard + Relational Database

**Purpose**: Recent data (last 90 days) with powerful visual interfaces and rollups

**Core Dimension Tables**:
- **Day Table**: Central date dimension (ISO format: 2026-01-17)
  - Links all daily data for powerful aggregations
  - Automatic connections to Week, Month, Quarter, Year
- **Week Table**: Weekly planning dimension (format: "3-26")
  - Weekly rollups and summaries
  - Training plan overview field

**Data Tables** (18 total):
1. **Calendar Events** - Google Calendar sync with Day links
2. **Training Sessions** - Actual workouts from Garmin
3. **Training Plans** - Planned workouts (compare to actuals)
4. **Health Metrics** - Daily health data (sleep, HRV, steps, stress)
5. **Body Metrics** - Weight and body composition
6. **Tasks** - Task management with due dates
7. **Projects** - Project tracking with task rollups
8. **Classes** - Course tracking
9. **Meal Plans** - Weekly meal planning
10. **Planned Meals** - Individual meal assignments
11. **Recipes** - Recipe library
12. **Grocery Items** - Shopping lists
13. **Accounts** (Optional) - Financial account summary
14. **Transactions** (Optional) - Recent transactions
15. **Finance Summary** (Optional) - Monthly rollups
16. **Weekly Reviews** - Weekly reflection with auto-rollups
17. **Sync Logs** - Integration health monitoring

**Why Airtable?**
- True relational database (foreign keys, rollups, lookups)
- Rich formula language and built-in automations
- Multiple view types (Kanban, Calendar, Gallery, Timeline, Gantt)
- Custom interfaces without coding
- Real-time collaboration
- Native mobile apps
- 100k records per base (sufficient for 90-day rolling window)

### SQL Database: Long-term Analytics

**Purpose**: Unlimited historical data and complex analytics

**Financial Data** (Required):
- `accounts` - Bank accounts, credit cards, investments
- `transactions` - All transactions (unlimited history)
- `balances` - Daily balance snapshots
- `investments` - Investment holdings snapshots
- `bills` - Recurring payments

**Health Data** (Optional Archival):
- `daily_metrics` - Historical health data (>90 days old)
- `body_metrics` - Historical body composition
- `training_sessions` - Historical workouts

**Why SQL?**
- Unlimited history (10+ years ≈ 20 MB)
- 30-500x faster complex queries
- No API rate limits
- Advanced analytics (JOINs, GROUP BY, window functions)
- Privacy: Financial data stays local
- Complex correlations and trend analysis

## Data Flow

### Google Calendar → Airtable

```
Google Calendar API
      ↓
integrations/google_calendar/sync.py
      ↓
airtable/calendar.py
      ↓
Airtable Calendar Events table
      ↓
Links to Day table by ISO date
```

**Features**:
- Multi-calendar support (Personal, School and Research, Work)
- Timezone-aware (Mountain Time with UTC storage)
- All-day and timed event handling
- Duplicate prevention via Event ID
- Incremental sync with state management

**Status**: ✅ Production Ready

### Garmin Connect → Airtable

```
Garmin Connect API
      ↓
integrations/garmin/sync.py
      ↓
airtable/health.py
      ↓
┌─────────────┬──────────────┬─────────────┐
Training      Health         Body
Sessions      Metrics        Metrics
      ↓             ↓              ↓
Links to     Links to Day    Links to Day
Day & Week   (1 per day)
```

**Features**:
- Training Sessions: Activities with performance metrics
- Health Metrics: Daily summaries (sleep, HRV, steps, stress, body battery)
- Body Metrics: Weight and composition from smart scale
- Links to Day/Week tables for rollups
- Imperial units (miles, lbs, feet)

**Status**: ⚙️ In Development

### Plaid Banking → SQL

```
Plaid API
      ↓
integrations/plaid/sync.py
      ↓
storage/financial.py
      ↓
SQL database (data.db)
```

**Features**:
- Unlimited transaction history
- Daily balance snapshots for net worth tracking
- Investment holdings and performance
- Encrypted access tokens
- Masked account numbers (last 4 digits only)

**Status**: ✅ Production Ready

## Integration Architecture

### Module Structure

```
personal_assistant/
├── core/
│   ├── config.py          # Unified configuration
│   ├── database.py        # SQLite management
│   ├── secure_storage.py  # Encrypted token storage
│   ├── state_manager.py   # Sync state tracking
│   └── utils.py           # Logging, retry, rate limiting
│
├── integrations/
│   ├── google_calendar/
│   │   └── sync.py        # Fetch calendar events
│   ├── garmin/
│   │   └── sync.py        # Fetch activities and health data
│   └── plaid/
│       └── sync.py        # Fetch financial data
│
├── airtable/
│   ├── base_client.py     # Airtable API client
│   ├── date_utils.py      # Date/time utilities
│   ├── calendar.py        # Calendar Events sync
│   └── health.py          # Health data sync
│
├── storage/
│   ├── financial.py       # Financial CRUD operations
│   ├── health.py          # Health CRUD operations (SQL)
│   └── queries.py         # Pre-built analytics queries
│
└── orchestrators/
    ├── sync_calendar.py   # Calendar sync orchestrator
    ├── sync_health.py     # Health sync orchestrator
    ├── sync_financial.py  # Financial sync orchestrator
    └── setup_plaid.py     # Link bank accounts
```

### Configuration

**.env File**:
```bash
# Airtable
AIRTABLE_ACCESS_TOKEN=pat_...
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
AIRTABLE_DAY=Day
AIRTABLE_WEEK=Week
AIRTABLE_CALENDAR_EVENTS=Calendar Events
AIRTABLE_TRAINING_SESSIONS=Training Sessions
AIRTABLE_HEALTH_METRICS=Health Metrics
AIRTABLE_BODY_METRICS=Body Metrics
AIRTABLE_TRAINING_PLANS=Training Plans

# Google Calendar
GOOGLE_CLIENT_SECRET_FILE=credentials/google_client_secret.json
GOOGLE_TOKEN_FILE=credentials/google_token.json

# Garmin
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_password

# Plaid
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret
PLAID_ENV=sandbox  # or production
```

## Key Features

### Relational Data Model

**Day Table as Central Hub**:
- All date-based data links to Day table
- Automatic rollups and aggregations
- Calendar events, workouts, health metrics all connected
- Easy to query "what happened on this day"

**Week Table for Planning**:
- Training Sessions link to Week for weekly mileage rollups
- Training Plans link to Week for weekly planning
- Weekly Reviews automatically calculate statistics
- Meal Plans organized by week

### Planned vs Actual Tracking

**Training Plans** ←→ **Training Sessions**
- Training Plans: What you intended to do
- Training Sessions: What you actually did
- Link them together via "Actual Activity" field
- Weekly rollups show planned vs actual mileage
- Identify skipped workouts or modifications

### Hybrid Storage Benefits

**Airtable Strengths**:
- Visual dashboards for daily use
- Real-time updates and collaboration
- Mobile access for on-the-go planning
- Powerful rollups and relationships
- No-code custom interfaces

**SQL Strengths**:
- Unlimited financial history (10+ years)
- Ultra-fast complex analytics
- Privacy (data stays local)
- No API limits or costs
- Advanced statistical analysis

## Security & Privacy

### Airtable Security
- Personal Access Tokens (scoped permissions)
- Base-level access control
- HTTPS encryption for all API calls
- Tokens can be revoked instantly
- Expiration dates on tokens

### Financial Data Security
- All financial data in local SQL database
- Plaid tokens encrypted with Fernet (AES-128)
- Full account numbers NEVER stored (only last 4 digits)
- Sensitive data redacted from logs
- Database files with owner-only permissions (600)
- HTTPS-only API communication

### General Security
- All credentials in `.env` files (gitignored)
- OAuth tokens cached locally
- No credentials in version control
- Automatic token refresh
- SQL injection prevention via parameterized queries

## Performance Metrics

### Airtable Operations
- Calendar sync (first): ~3-5 minutes (350+ events)
- Calendar sync (incremental): ~5-10 seconds
- Health sync (first): ~5-10 minutes
- Health sync (incremental): ~10-20 seconds
- Rate limit: 5 requests/second (rarely hit)

### SQL Operations
- Financial sync (first): ~5-10 seconds
- Financial sync (incremental): ~2-5 seconds
- Complex analytics queries: <10ms
- Net worth calculation: <5ms
- Historical trend analysis: <100ms

### Data Retention
- **Airtable**: Last 90 days (rolling window)
- **SQL**: Unlimited (10+ years = ~20 MB)
- **Monthly archival**: Move old Airtable data to SQL

## Future Enhancements

Planned additions:
- Complete Garmin → Airtable sync (currently in development)
- Automated weekly reviews with AI insights
- Meal planning with recipe integration
- Financial dashboard in Airtable (summary view)
- Microsoft Calendar integration
- Strava integration
- GitHub issues as tasks
- Email integration
- Bidirectional sync (edit in Airtable → update source)
- Weather data correlation with workouts
- Advanced analytics dashboards

## Documentation

### Setup Guides
- [README.md](README.md) - Getting started and overview
- [AIRTABLE_SETUP.md](AIRTABLE_SETUP.md) - Personal Access Token setup
- [AIRTABLE_SETUP_COMPLETE.md](AIRTABLE_SETUP_COMPLETE.md) - Current setup status
- [airtable_structure_plan.md](airtable_structure_plan.md) - Complete base schema

### Reference
- [FINANCIAL_SECURITY_PLAN.md](FINANCIAL_SECURITY_PLAN.md) - Security architecture
- [airtable_findings.md](airtable_findings.md) - Implementation findings

### Scripts
- `test_airtable.py` - Test Airtable connection
- `inspect_tables.py` - Inspect table structure
- `scripts/init_database.py` - Initialize SQL database

## Support

For issues:
1. Check configuration with health check commands
2. Verify credentials in `.env` file
3. Test individual components (Airtable connection, API access)
4. Review logs in `logs/` directory
5. Check sync state in `state.db`

---

**Built with Claude Code**

This architecture provides a powerful foundation for AI-assisted life management, combining the visual power of Airtable with the analytical depth of SQL databases.
