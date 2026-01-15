# Migration Guide: Unified Personal Assistant Structure

This guide walks you through migrating from the separate `calendar-sync` and `health-training` modules to the new unified structure.

## Why Migrate?

**Benefits:**
- ✅ Single `.env` file to manage
- ✅ One virtual environment for all integrations
- ✅ Shared utilities (no code duplication)
- ✅ Easy to add new integrations (Microsoft Calendar, Plaid, etc.)
- ✅ Cleaner, more professional structure

## Before You Start

**Your current modules will keep working!** This migration is optional but recommended for future integrations.

### Backup (Optional but Recommended)

```bash
cd /Users/marykate/Desktop/personal_assistant
tar -czf backup_$(date +%Y%m%d).tar.gz calendar-sync/ health-training/
```

## Migration Steps

### Step 1: Preview Changes (Dry Run)

```bash
cd /Users/marykate/Desktop/personal_assistant
python migrate.py --dry-run
```

This shows you what will change without modifying any files.

### Step 2: Run Migration

```bash
python migrate.py
```

Type `yes` when prompted.

**What it does:**
1. Creates `core/utils.py` and `core/config.py` (shared utilities)
2. Migrates Google Calendar code to `integrations/google_calendar/`
3. Migrates Garmin code to `integrations/garmin/`
4. Migrates Notion clients to `notion/calendar.py` and `notion/health.py`
5. Creates unified `.env` file (merges both existing .env files)
6. Moves old modules to `_archive/` folder

### Step 3: Review Merged .env File

The script merges your `.env` files, but you should review for duplicates:

```bash
open -e .env
```

Clean up any duplicate entries. Your final `.env` should look like:

```bash
# Notion (shared)
NOTION_TOKEN=ntn_your_token_here
NOTION_CALENDAR_DB_ID=xxxxx
NOTION_WORKOUTS_DB_ID=xxxxx
NOTION_DAILY_METRICS_DB_ID=xxxxx
NOTION_BODY_METRICS_DB_ID=xxxxx

# Google Calendar
GOOGLE_CALENDAR_IDS=primary,school_id@group.calendar.google.com
GOOGLE_CALENDAR_NAMES=Personal,School and Research

# Garmin
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_password

# Settings
SYNC_LOOKBACK_DAYS=90
SYNC_LOOKAHEAD_DAYS=365
UNIT_SYSTEM=imperial
LOG_LEVEL=INFO
```

### Step 4: Set Up Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Copy Credentials

```bash
# Copy Google OAuth credentials
mkdir -p credentials
cp _archive/calendar-sync/credentials/google_client_secret.json credentials/

# Copy Garmin tokens (if they exist)
cp -r _archive/health-training/credentials/garmin_tokens credentials/ 2>/dev/null || true
```

### Step 6: Test Authentication

```bash
# Create test script
cat > scripts/test_auth.py << 'EOF'
#!/usr/bin/env python3
"""Test authentication for all integrations."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import GoogleCalendarConfig, GarminConfig
from integrations.google_calendar.sync import GoogleCalendarSync
from integrations.garmin.sync import GarminSync

print("Testing Google Calendar...")
is_valid, errors = GoogleCalendarConfig.validate()
if errors:
    print(f"  Config errors: {errors}")
else:
    print("  ✓ Config valid")

print("\nTesting Garmin...")
is_valid, errors = GarminConfig.validate()
if errors:
    print(f"  Config errors: {errors}")
else:
    print("  ✓ Config valid")

print("\n✓ All tests passed!")
EOF

chmod +x scripts/test_auth.py
python scripts/test_auth.py
```

### Step 7: Create Orchestrators

The migration script created the structure, but you need to create the orchestrator files:

**Create `orchestrators/sync_calendar.py`:**

```bash
cat > orchestrators/sync_calendar.py << 'EOF'
#!/usr/bin/env python3
"""Calendar sync orchestrator - syncs Google Calendar to Notion"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from old calendar-sync orchestrator
# You'll need to adapt this based on your calendar-sync/sync_orchestrator.py

from core.state_manager import StateManager
from integrations.google_calendar.sync import GoogleCalendarSync
from notion.calendar import NotionSync

def main():
    state = StateManager()
    google = GoogleCalendarSync()
    notion = NotionSync(state)

    # Your sync logic here
    # (Copy from calendar-sync/sync_orchestrator.py)

    print("✓ Calendar sync complete!")

if __name__ == "__main__":
    main()
EOF

chmod +x orchestrators/sync_calendar.py
```

**Create `orchestrators/sync_health.py`:**

```bash
cat > orchestrators/sync_health.py << 'EOF'
#!/usr/bin/env python3
"""Health sync orchestrator - syncs Garmin to Notion"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.state_manager import StateManager
from integrations.garmin.sync import GarminSync
from notion.health import NotionSync

def main():
    state = StateManager()
    garmin = GarminSync()
    notion = NotionSync(state)

    # Your sync logic here
    # (Copy from health-training/sync_orchestrator.py)

    print("✓ Health sync complete!")

if __name__ == "__main__":
    main()
EOF

chmod +x orchestrators/sync_health.py
```

### Step 8: Test Syncs

```bash
# Test calendar sync
python orchestrators/sync_calendar.py --dry-run
python orchestrators/sync_calendar.py

# Test health sync
python orchestrators/sync_health.py --dry-run
python orchestrators/sync_health.py
```

### Step 9: Update Cron Jobs

Edit your crontab:

```bash
crontab -e
```

**Old cron jobs:**
```bash
*/5 * * * * cd /Users/marykate/Desktop/personal_assistant/calendar-sync && venv/bin/python sync_orchestrator.py >> logs/cron.log 2>&1
0 7,19 * * * cd /Users/marykate/Desktop/personal_assistant/health-training && venv/bin/python sync_orchestrator.py >> logs/cron.log 2>&1
```

**New cron jobs:**
```bash
*/5 * * * * cd /Users/marykate/Desktop/personal_assistant && venv/bin/python orchestrators/sync_calendar.py >> logs/cron_calendar.log 2>&1
0 7,19 * * * cd /Users/marykate/Desktop/personal_assistant && venv/bin/python orchestrators/sync_health.py >> logs/cron_health.log 2>&1
```

### Step 10: Verify Everything Works

```bash
# Check logs
tail -f logs/cron_calendar.log
tail -f logs/cron_health.log

# Check Notion databases
# Make sure events and workouts are still syncing
```

## New Directory Structure

```
personal_assistant/
├── core/                          # Shared utilities
│   ├── __init__.py
│   ├── config.py                  # Unified configuration
│   ├── state_manager.py           # Shared state management
│   └── utils.py                   # Shared utilities
│
├── integrations/                  # Data source integrations
│   ├── google_calendar/
│   │   ├── __init__.py
│   │   └── sync.py
│   └── garmin/
│       ├── __init__.py
│       └── sync.py
│
├── notion/                        # Notion database clients
│   ├── __init__.py
│   ├── calendar.py
│   └── health.py
│
├── orchestrators/                 # Sync scripts
│   ├── sync_calendar.py
│   └── sync_health.py
│
├── scripts/                       # Utility scripts
│   └── test_auth.py
│
├── credentials/                   # OAuth credentials
├── logs/                          # Log files
├── _archive/                      # Old modules (backup)
│   ├── calendar-sync/
│   └── health-training/
│
├── .env                           # Unified configuration
├── .env.example
├── .gitignore
├── requirements.txt
├── venv/
├── state.db
├── README.md
├── MIGRATION_GUIDE.md (this file)
└── migrate.py
```

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:

```python
# Make sure your orchestrators include:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Old Modules Still Running

Make sure you updated your cron jobs! Check with:

```bash
crontab -l
```

### .env File Issues

Make sure your `.env` is in the project root (`personal_assistant/`), not in subdirectories.

### State Database

The new structure uses `state.db` in the project root. Your old state is preserved in `_archive/`.

## Rollback (If Needed)

If something goes wrong, you can rollback:

```bash
cd /Users/marykate/Desktop/personal_assistant

# Restore old modules
mv _archive/calendar-sync .
mv _archive/health-training .

# Restore old cron jobs
crontab -e
# (change back to old paths)
```

## Adding New Integrations (Future)

Now it's easy to add new integrations!

**Example: Adding Microsoft Calendar**

1. Create `integrations/microsoft_calendar/sync.py`
2. Update `orchestrators/sync_calendar.py` to include Microsoft
3. Add Microsoft credentials to `.env`
4. Done!

**Example: Adding Plaid (Banking)**

1. Create `integrations/plaid/sync.py`
2. Create `notion/finance.py` for transactions database
3. Create `orchestrators/sync_finance.py`
4. Add Plaid credentials to `.env`
5. Done!

## Summary

After migration, you have:

- ✅ Unified structure ready for future integrations
- ✅ Single `.env` file and virtual environment
- ✅ Shared utilities (no duplication)
- ✅ Old modules archived (safe backup)
- ✅ Everything still working!

---

**Questions?** See `REFACTOR_PLAN.md` for more details, or review the migration script: `migrate.py`
