# Personal Assistant Refactor Plan

## Status: In Progress

I've started the refactor to create a unified structure for all future integrations. Here's what's been completed and what remains.

## ✅ Completed

1. **Created new directory structure:**
   ```
   personal_assistant/
   ├── core/                    # Shared utilities
   ├── integrations/            # Data source integrations
   │   ├── google_calendar/
   │   └── garmin/
   ├── orchestrators/           # Sync scripts
   ├── scripts/                 # Utility scripts
   └── notion/                  # Notion database schemas
   ```

2. **Created shared core/state_manager.py** - Unified state management for all integrations

3. **Created consolidated requirements.txt** - All dependencies in one file

## 🔄 Remaining Work

### Step 1: Create Core Utilities (30 min)

**File: `core/utils.py`**
- Merge utils from both modules
- Shared logging setup
- Retry decorators
- Rate limiting
- Unit conversions (imperial/metric)

**File: `core/config.py`**
- Base configuration class
- Load from single `.env` file
- Validation methods

### Step 2: Migrate Google Calendar Integration (20 min)

**Move and adapt:**
- `calendar-sync/src/google_sync.py` → `integrations/google_calendar/sync.py`
- `calendar-sync/src/notion_sync.py` → `notion/calendar.py`
- Update imports to use `core.` and `integrations.`

**File: `integrations/google_calendar/config.py`**
```python
from core.config import BaseConfig

class GoogleCalendarConfig(BaseConfig):
    GOOGLE_CALENDAR_IDS = os.getenv("GOOGLE_CALENDAR_IDS", "primary")
    GOOGLE_CALENDAR_NAMES = os.getenv("GOOGLE_CALENDAR_NAMES", "Personal")
    # ... other Google-specific settings
```

### Step 3: Migrate Garmin Integration (20 min)

**Move and adapt:**
- `health-training/src/garmin_sync.py` → `integrations/garmin/sync.py`
- `health-training/src/notion_sync.py` → `notion/health.py`
- Update imports

**File: `integrations/garmin/config.py`**
```python
from core.config import BaseConfig

class GarminConfig(BaseConfig):
    GARMIN_EMAIL = os.getenv("GARMIN_EMAIL")
    GARMIN_PASSWORD = os.getenv("GARMIN_PASSWORD")
    UNIT_SYSTEM = os.getenv("UNIT_SYSTEM", "imperial")
    # ... other Garmin-specific settings
```

### Step 4: Create Unified Orchestrators (30 min)

**File: `orchestrators/sync_calendar.py`**
```python
#!/usr/bin/env python3
"""
Calendar sync orchestrator
Syncs Google Calendar (and future: Microsoft Calendar) to Notion
"""

from core.state_manager import StateManager
from integrations.google_calendar.sync import GoogleCalendarSync
from notion.calendar import CalendarNotionClient

def main():
    state = StateManager()
    google = GoogleCalendarSync()
    notion = CalendarNotionClient(state)

    # Sync logic here
    ...
```

**File: `orchestrators/sync_health.py`**
```python
#!/usr/bin/env python3
"""
Health sync orchestrator
Syncs Garmin (and future: Apple Health, Strava) to Notion
"""

from core.state_manager import StateManager
from integrations.garmin.sync import GarminSync
from notion.health import HealthNotionClient

def main():
    state = StateManager()
    garmin = GarminSync()
    notion = HealthNotionClient(state)

    # Sync logic here
    ...
```

**File: `orchestrators/sync_all.py`** (NEW - syncs everything)
```python
#!/usr/bin/env python3
"""
Master sync orchestrator
Runs all syncs in parallel or sequentially
"""

import asyncio
from orchestrators import sync_calendar, sync_health

async def main():
    # Run syncs in parallel
    await asyncio.gather(
        sync_calendar.sync(),
        sync_health.sync()
    )
```

### Step 5: Create Single .env File (10 min)

**File: `.env`**
```bash
# ==================== Notion ====================
NOTION_TOKEN=ntn_your_token_here

# Calendar Events Database
NOTION_CALENDAR_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Health Databases
NOTION_WORKOUTS_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DAILY_METRICS_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_BODY_METRICS_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ==================== Google Calendar ====================
GOOGLE_CALENDAR_IDS=primary,school_id@group.calendar.google.com
GOOGLE_CALENDAR_NAMES=Personal,School and Research

SYNC_LOOKBACK_DAYS=90
SYNC_LOOKAHEAD_DAYS=365

# ==================== Garmin ====================
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_password

# ==================== Settings ====================
UNIT_SYSTEM=imperial
LOG_LEVEL=INFO
```

### Step 6: Update Documentation (20 min)

**Create: `MIGRATION_GUIDE.md`**
- How to migrate from old structure
- What changed
- How to run new orchestrators

**Update: `README.md`**
- New structure
- New commands (`python orchestrators/sync_calendar.py`)
- How to add future integrations

### Step 7: Create Virtual Environment (5 min)

```bash
cd /Users/marykate/Desktop/personal_assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 8: Test Everything (15 min)

1. Copy `.env` from calendar-sync and merge with health-training
2. Test auth: `python scripts/test_auth.py`
3. Test calendar sync: `python orchestrators/sync_calendar.py --dry-run`
4. Test health sync: `python orchestrators/sync_health.py --dry-run`
5. Run actual syncs

### Step 9: Update Cron Jobs (5 min)

**Old cron:**
```bash
*/5 * * * * cd .../calendar-sync && venv/bin/python sync_orchestrator.py
0 7,19 * * * cd .../health-training && venv/bin/python sync_orchestrator.py
```

**New cron:**
```bash
*/5 * * * * cd /Users/marykate/Desktop/personal_assistant && venv/bin/python orchestrators/sync_calendar.py >> logs/cron_calendar.log 2>&1
0 7,19 * * * cd /Users/marykate/Desktop/personal_assistant && venv/bin/python orchestrators/sync_health.py >> logs/cron_health.log 2>&1
```

### Step 10: Archive Old Modules (2 min)

```bash
cd /Users/marykate/Desktop/personal_assistant
mkdir _archive
mv calendar-sync _archive/
mv health-training _archive/
```

## Benefits of New Structure

### For You Now
- ✅ Single `.env` file to manage
- ✅ One virtual environment
- ✅ Shared utilities (no duplication)
- ✅ Clearer organization

### For Future Integrations

**Adding Microsoft Calendar:**
```
1. Create integrations/microsoft_calendar/sync.py
2. Add config to integrations/microsoft_calendar/config.py
3. Update orchestrators/sync_calendar.py to include Microsoft
4. Done!
```

**Adding Plaid (Banking):**
```
1. Create integrations/plaid/sync.py
2. Create notion/finance.py for transaction database
3. Create orchestrators/sync_finance.py
4. Add PLAID_CLIENT_ID to .env
5. Done!
```

## Estimated Total Time

- **Initial refactor**: 2-2.5 hours
- **Testing**: 30 minutes
- **Total**: ~3 hours

## Decision Point

**Do you want to:**

**A) I'll finish the refactor now** (will take the full session)
- I'll create all the files
- Migrate all the code
- Test everything
- Update docs

**B) I'll create a migration script for you** (15 minutes)
- Script that moves files automatically
- You run it when ready
- Less hand-holding, but faster

**C) Pause and revisit later**
- Current modules still work
- Refactor when you're ready to add integration #3
- Keep REFACTOR_PLAN.md for reference

## My Recommendation

Given we're at 110K tokens used, I recommend **Option B**: I'll create an automated migration script that you can run when you're ready. This way:

1. Your current setup keeps working
2. You have clear documentation of what changes
3. You can run the migration script when convenient
4. The script handles all file moves and updates

What do you think?
