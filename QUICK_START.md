# Quick Start Guide

Get your calendar sync up and running in under 30 minutes!

## Step 1: Install Dependencies (5 minutes)

```bash
# Navigate to project
cd /Users/marykate/Desktop/calendar-sync

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

You should see `(venv)` in your terminal prompt.

## Step 2: Get Google Calendar Credentials (10 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project: "Calendar Sync"
3. Enable "Google Calendar API"
4. Create OAuth consent screen (External type)
   - Add your email as test user
5. Create credentials:
   - Type: OAuth client ID
   - Application type: Desktop app
6. Download the JSON file
7. Save it as `credentials/google_client_secret.json`

📖 **Detailed instructions**: See SETUP_GUIDES.md → "Google Calendar API Setup"

## Step 3: Set Up Notion (10 minutes)

### Create Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "+ New integration"
3. Name: "Calendar Sync"
4. Select your workspace
5. Click "Submit"
6. Copy the token (starts with `secret_`)

### Create Database

1. In Notion, create a new page
2. Add a database (type `/database` → "Database - Full page")
3. Name it: "Calendar Events"
4. Add these properties:

   ```
   Title (Title) - rename from "Name"
   Start Time (Date) - include time
   End Time (Date) - include time
   Source (Select) - add option "Personal Google"
   Location (Text)
   Description (Text)
   External ID (Text)
   Attendees (Multi-select)
   Last Synced (Date) - include time
   URL (URL)
   Sync Status (Select) - add options "Active", "Cancelled", "Updated"
   ```

5. Share database with integration:
   - Click "..." → "Connections"
   - Select "Calendar Sync"

6. Get database ID:
   - Click "..." → "Copy link"
   - Extract the 32-character ID from URL
   - Example: `https://notion.so/workspace/Calendar-Events-a1b2c3d4e5f67890a1b2c3d4e5f67890?v=...`
   - ID is: `a1b2c3d4e5f67890a1b2c3d4e5f67890`

📖 **Detailed instructions**: See SETUP_GUIDES.md → "Notion API Setup"

## Step 4: Configure Environment (2 minutes)

```bash
# Copy example configuration
cp .env.example .env

# Edit .env file
open -e .env
```

Fill in these values:

```bash
# Notion
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_CALENDAR_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Google Calendar (defaults are fine for now)
GOOGLE_CALENDAR_IDS=primary
GOOGLE_CALENDAR_NAMES=Personal
```

Save and close the file.

## Step 5: Test Authentication (2 minutes)

```bash
python scripts/test_auth.py
```

This will:
1. Open a browser for Google OAuth (sign in and grant permissions)
2. Test Notion connection
3. Verify database access

**Expected output:**
```
✓ Configuration is valid
✓ Successfully authenticated with Google Calendar!
✓ Connected to Notion API!
✓ Calendar Events database accessible!
```

## Step 6: Run Your First Sync! (1 minute)

```bash
# Dry run first (see what would be synced)
python sync_orchestrator.py --dry-run
```

You should see a list of events that will be synced.

```bash
# Actual sync
python sync_orchestrator.py
```

**Expected output:**
```
✓ Sync completed successfully!
Calendars synced: 1
Events fetched: 25
Events created: 25
```

## Step 7: Check Notion

Open your "Calendar Events" database in Notion - you should see all your calendar events!

## Step 8: Set Up Automatic Syncing (Optional, 3 minutes)

### Using cron (Mac)

```bash
# Edit crontab
crontab -e

# Add this line (adjust paths if needed):
*/15 * * * * cd /Users/marykate/Desktop/calendar-sync && /Users/marykate/Desktop/calendar-sync/venv/bin/python sync_orchestrator.py >> logs/cron.log 2>&1

# Save and exit
```

This will sync every 15 minutes automatically.

To verify it's working:
```bash
# View cron log
tail -f logs/cron.log
```

## Next Steps

### Add More Calendars

To sync multiple Google calendars:

1. Get calendar IDs from Google Calendar settings
2. Update `.env`:
   ```bash
   GOOGLE_CALENDAR_IDS=primary,work@example.com
   GOOGLE_CALENDAR_NAMES=Personal,Work
   ```
3. Add "Work" as a Source option in your Notion database
4. Run sync again

### Use with Claude.ai

1. Open your Calendar Events database in Notion
2. Click "Share" → Copy link
3. Share the link with Claude.ai
4. Ask Claude to help you plan your week!

Example prompts:
- "What's my schedule this week?"
- "When's my next free 2-hour block?"
- "Help me find time for a 30-minute workout"

## Troubleshooting

### Issue: "google_client_secret.json not found"
**Solution**: Make sure the file is at `credentials/google_client_secret.json`

### Issue: "401 Unauthorized" from Notion
**Solution**: Check that your NOTION_TOKEN is correct and starts with `secret_`

### Issue: "Database not found"
**Solution**:
1. Verify database ID is correct (32 characters)
2. Make sure you shared the database with your integration

### Issue: No events appearing
**Solution**: Check date range in `.env` (SYNC_LOOKBACK_DAYS, SYNC_LOOKAHEAD_DAYS)

### Still having issues?
- Check `logs/sync.log` for detailed errors
- See SETUP_GUIDES.md for comprehensive troubleshooting
- Review your configuration with: `python src/config.py`

## Summary

You now have:
- ✅ Google Calendar syncing to Notion
- ✅ All your events in one place
- ✅ Automatic syncing every 15 minutes (if configured)
- ✅ Ready to use Claude.ai as your assistant

## What's Next?

See README.md for:
- Advanced configuration options
- Adding Microsoft Calendar sync
- Training/Strava integration
- Dashboard and analytics

---

**Need help?** See SETUP_GUIDES.md or check logs at `logs/sync.log`
