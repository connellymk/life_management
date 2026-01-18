# Migration to Airtable - Status & Notes

## ✅ Completed

### Documentation
- ✅ Updated README.md to reflect Airtable architecture
- ✅ Created ARCHITECTURE.md with comprehensive system overview
- ✅ Removed all Notion-specific documentation files
- ✅ Verified Airtable setup documentation is current

### Code Cleanup
- ✅ Deleted entire `notion/` directory (replaced by `airtable/`)
- ✅ Removed one-off Airtable setup scripts:
  - `create_airtable_tables.py`
  - `get_table_ids.py`
  - `add_table_fields.py`
  - `fix_missing_fields.py`
  - `verify_table_schemas.py`
  - `restructure_training_plans.py`
  - `clear_calendar_events.py`
  - `check_calendar_sync.py`
  - `check_day_records.py`
  - `check_timezone.py`
  - `find_today.py`

### Kept for Troubleshooting
- ✅ `test_airtable.py` - Verify Airtable connection and setup
- ✅ `test_calendar_sync.py` - Test Google Calendar → Airtable sync
- ✅ `inspect_tables.py` - Inspect Day/Week table structure

## ⚙️ Needs Update

### Orchestrators (Still Reference Notion)

**orchestrators/sync_calendar.py**
- ❌ Currently imports: `from notion.calendar import NotionSync`
- ✅ Should import: `from airtable.calendar import AirtableCalendarSync`
- Status: **Needs refactoring**

**orchestrators/sync_health.py**
- ❌ Currently imports: `from notion.health import NotionSync`
- ✅ Should import: `from airtable.health import AirtableTrainingSessionsSync, AirtableHealthMetricsSync, AirtableBodyMetricsSync`
- Status: **Needs refactoring**

**orchestrators/sync_financial.py**
- ✅ Uses SQL only (no changes needed)
- Status: **Up to date**

## 🔄 Migration Tasks

### Priority 1: Update Calendar Orchestrator

**File**: `orchestrators/sync_calendar.py`

**Required Changes**:
1. Replace import:
   ```python
   # OLD
   from notion.calendar import NotionSync

   # NEW
   from airtable.calendar import AirtableCalendarSync
   ```

2. Update function to use Airtable:
   ```python
   # OLD
   notion_sync = NotionSync(state_manager)

   # NEW
   airtable_sync = AirtableCalendarSync()
   ```

3. Update sync logic to use Airtable methods:
   - `create_event()` → Already implemented in `airtable/calendar.py`
   - `update_event()` → Already implemented
   - `sync_event()` → Already implemented (handles create or update)

**Status**: Calendar sync code in `airtable/calendar.py` is complete, just need to wire up orchestrator

### Priority 2: Update Health Orchestrator

**File**: `orchestrators/sync_health.py`

**Required Changes**:
1. Replace import:
   ```python
   # OLD
   from notion.health import NotionSync

   # NEW
   from airtable.health import (
       AirtableTrainingSessionsSync,
       AirtableHealthMetricsSync,
       AirtableBodyMetricsSync
   )
   ```

2. Initialize separate sync classes:
   ```python
   training_sync = AirtableTrainingSessionsSync()
   health_sync = AirtableHealthMetricsSync()
   body_sync = AirtableBodyMetricsSync()
   ```

3. Update sync functions:
   - Workouts → `training_sync.sync_session()`
   - Daily metrics → `health_sync.create_or_update_metrics()`
   - Body metrics → `body_sync.create_measurement()`

**Status**: Health sync code in `airtable/health.py` is complete, just need to wire up orchestrator

### Priority 3: Testing

**Test Each Sync**:
1. Calendar sync: `python orchestrators/sync_calendar.py --dry-run`
2. Health sync: `python orchestrators/sync_health.py --dry-run`
3. Verify data appears correctly in Airtable
4. Check Day/Week table links are working

## 📋 Airtable Implementation Status

### ✅ Complete
- `airtable/base_client.py` - Airtable API client
- `airtable/date_utils.py` - Date/time conversion utilities
- `airtable/calendar.py` - Calendar Events sync (fully implemented)
- `airtable/health.py` - Training Sessions, Health Metrics, Body Metrics sync (fully implemented)

### ✅ Airtable Base Setup
- Day table (ISO format dates)
- Week table (W-YY format)
- Calendar Events table (16 fields)
- Training Sessions table (18 fields)
- Health Metrics table (19 fields)
- Body Metrics table (13 fields)
- Training Plans table (15 fields)

### ⏳ Pending
- Tasks table (fields TBD)
- Projects table (fields TBD)
- Classes table (fields TBD)
- Meal Plans table (fields TBD)
- Planned Meals table (fields TBD)
- Recipes table (fields TBD)
- Grocery Items table (fields TBD)
- Weekly Reviews table (fields TBD)
- Sync Logs table (fields TBD)

## 🔧 Quick Start After Migration

Once orchestrators are updated:

1. **Test Airtable connection**:
   ```bash
   python test_airtable.py
   ```

2. **Sync calendar** (dry run first):
   ```bash
   python orchestrators/sync_calendar.py --dry-run
   python orchestrators/sync_calendar.py
   ```

3. **Sync health data** (dry run first):
   ```bash
   python orchestrators/sync_health.py --dry-run
   python orchestrators/sync_health.py
   ```

4. **Verify in Airtable**:
   - Check Calendar Events table has events with Day links
   - Check Training Sessions table has workouts with Day/Week links
   - Check Health Metrics table has daily data
   - Verify rollups in Week table work correctly

## 📝 Notes

### Date Handling
- **Airtable Day table**: Uses ISO format (2026-01-17) internally, displays as m/d/yy in UI
- **Date conversion**: `date_to_day_id()` generates ISO format for querying
- **Week ID format**: "W-YY" (e.g., "3-26" for week 3 of 2026)
- **Timezone**: Mountain Time (America/Denver) with UTC storage for timestamps

### Performance
- Calendar sync: ~3-5 minutes first sync, ~5-10 seconds incremental
- Health sync: ~5-10 minutes first sync, ~10-20 seconds incremental
- Rate limit: 5 requests/second (rarely hit with current implementation)

### Future Enhancements
- Automated weekly reviews
- Meal planning integration
- Financial summary view in Airtable (optional)
- Training plan vs actual comparison dashboard
- AI-powered insights from rollup data

---

**Last Updated**: January 17, 2026
**Migration Started**: January 16, 2026 (Airtable base setup)
**Documentation Updated**: January 17, 2026
