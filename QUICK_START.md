# Quick Start Guide

## First-Time Setup (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Airtable
1. Create Personal Access Token at https://airtable.com/create/tokens
2. Copy your Base ID from Airtable URL (starts with `app`)
3. Add to `.env` file:
   ```bash
   AIRTABLE_ACCESS_TOKEN=pat_your_token_here
   AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
   ```

### 3. Set Up Google Calendar
1. Get OAuth credentials from Google Cloud Console
2. Save as `credentials/google_client_secret.json`
3. Add calendar IDs to `.env`:
   ```bash
   GOOGLE_CALENDAR_IDS=primary,your.email@gmail.com
   GOOGLE_CALENDAR_NAMES=Personal,School and Research
   ```

### 4. Test Connection
```bash
python test_airtable.py
```

## Common Commands

### Calendar Sync (Google Calendar → Airtable)

**Full sync** (recommended first run):
```bash
python orchestrators/sync_calendar.py
```

**Dry run** (see what would sync without making changes):
```bash
python orchestrators/sync_calendar.py --dry-run
```

**Health check** (verify configuration):
```bash
python orchestrators/sync_calendar.py --health-check
```

**Sync specific date range**:
```bash
python orchestrators/sync_calendar.py --start-date 2026-01-01 --end-date 2026-12-31
```

**Force refresh** (ignore sync state, re-sync everything):
```bash
python orchestrators/sync_calendar.py --force-refresh
```

### Health Sync (Garmin → Airtable)

**Note**: Health sync to Airtable is in development. Commands listed for when migration is complete.

```bash
# Full sync (workouts + metrics)
python orchestrators/sync_health.py

# Workouts only
python orchestrators/sync_health.py --workouts-only

# Metrics only (sleep, steps, HR, etc.)
python orchestrators/sync_health.py --metrics-only

# Dry run
python orchestrators/sync_health.py --dry-run

# Health check
python orchestrators/sync_health.py --health-check
```

### Financial Sync (Plaid → SQL)

**First-time setup** (link bank accounts):
```bash
python orchestrators/setup_plaid.py
```

**Sync all financial data**:
```bash
python orchestrators/sync_financial.py
```

**Sync specific data**:
```bash
python orchestrators/sync_financial.py --accounts-only
python orchestrators/sync_financial.py --transactions-only
python orchestrators/sync_financial.py --balances-only
```

## Troubleshooting

### Calendar Sync Issues

**"No credentials found"**:
```bash
# Delete cached token and re-authenticate
rm credentials/google_token.json
python orchestrators/sync_calendar.py
```

**"Airtable connection failed"**:
```bash
# Test Airtable connection
python test_airtable.py

# Verify token and base ID in .env
cat .env | grep AIRTABLE
```

**"No Day record found for date"**:
- Your Day table might not have records for all dates
- Day records should be pre-populated with dates you want to track
- Calendar sync will warn but continue if Day link is missing

### Check Sync Logs

```bash
# View recent sync activity
tail -50 logs/sync.log

# Follow logs in real-time
tail -f logs/sync.log

# Search for errors
grep ERROR logs/sync.log
```

### Reset State Database

If syncs are duplicating or acting strange:

```bash
# Backup current state
cp state.db state.db.backup

# Clear sync state (will re-sync everything)
python -c "from core.state_manager import StateManager; s = StateManager(); s.clear_all_state()"
```

## What Gets Synced

### Calendar Events → Airtable
- ✅ Event title, start/end times
- ✅ All-day vs timed events
- ✅ Location, description, attendees
- ✅ Calendar source (Personal, School, Work)
- ✅ Links to Day table (for rollups)
- ✅ Timezone-aware (Mountain Time)

### Garmin Health → Airtable (In Development)
- ⚙️ Training Sessions (workouts with metrics)
- ⚙️ Health Metrics (sleep, steps, HR, stress)
- ⚙️ Body Metrics (weight, body composition)
- ⚙️ Links to Day/Week tables

### Plaid Banking → SQL
- ✅ Accounts (checking, savings, credit cards, investments)
- ✅ Transactions (unlimited history)
- ✅ Daily balance snapshots
- ✅ Investment holdings

## Performance Expectations

**Calendar Sync**:
- First sync: ~3-5 minutes (350+ events)
- Incremental: ~5-10 seconds
- Recommended: Every 5-15 minutes (automated)

**Health Sync**:
- First sync: ~5-10 minutes
- Incremental: ~10-20 seconds
- Recommended: Twice daily (7 AM, 7 PM)

**Financial Sync**:
- First sync: ~5-10 seconds
- Incremental: ~2-5 seconds
- Recommended: Daily (7 AM)

## Next Steps

1. **Run your first sync**:
   ```bash
   python orchestrators/sync_calendar.py
   ```

2. **Check Airtable** - Verify events appear in Calendar Events table

3. **Set up automation** - Add to cron or Task Scheduler for automatic syncs

4. **Explore Airtable**:
   - Create Calendar view grouped by Day
   - Add rollups to Week table for weekly summaries
   - Build custom interfaces for daily/weekly planning

5. **Read full docs**:
   - [README.md](README.md) - Complete documentation
   - [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
   - [MIGRATION_NOTES.md](MIGRATION_NOTES.md) - Current migration status

---

**Built with Claude Code**

For issues or questions, see the Troubleshooting section in README.md
