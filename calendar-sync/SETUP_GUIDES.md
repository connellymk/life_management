# Setup Guides - Calendar Sync Integration

Complete step-by-step instructions for setting up all required API credentials.

---

## Table of Contents

1. [Google Calendar API Setup](#google-calendar-api-setup)
2. [Notion API Setup](#notion-api-setup)
3. [Initial Configuration](#initial-configuration)
4. [Testing Your Setup](#testing-your-setup)
5. [Troubleshooting](#troubleshooting)

---

## Google Calendar API Setup

### Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Click on the project dropdown at the top of the page
4. Click "New Project"
5. Enter project details:
   - **Project Name**: `Calendar Sync` (or any name you prefer)
   - **Location**: Leave as default or select your organization
6. Click "Create"
7. Wait a few seconds for the project to be created

### Step 2: Enable Google Calendar API

1. Make sure your new project is selected (check the project name at the top)
2. In the left sidebar, click "APIs & Services" → "Library"
   - Or search for "API Library" in the top search bar
3. In the API Library, search for "Google Calendar API"
4. Click on "Google Calendar API"
5. Click the blue "Enable" button
6. Wait for the API to be enabled (takes a few seconds)

### Step 3: Create OAuth Consent Screen

1. In the left sidebar, click "APIs & Services" → "OAuth consent screen"
2. Select **"External"** user type (unless you have a Google Workspace)
3. Click "Create"
4. Fill in the required fields:
   - **App name**: `Calendar Sync`
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
5. Leave other fields as default
6. Click "Save and Continue"
7. On the "Scopes" page, click "Add or Remove Scopes"
8. Search for "Google Calendar API"
9. Select these scopes:
   - `.../auth/calendar.readonly` - See all your calendars
   - `.../auth/calendar.events.readonly` - View events on all your calendars
10. Click "Update" then "Save and Continue"
11. On "Test users" page, click "Add Users"
12. Add your Gmail address
13. Click "Add" then "Save and Continue"
14. Review the summary and click "Back to Dashboard"

### Step 4: Create OAuth Credentials

1. In the left sidebar, click "APIs & Services" → "Credentials"
2. Click "+ Create Credentials" at the top
3. Select "OAuth client ID"
4. For Application type, select **"Desktop app"**
5. Name: `Calendar Sync Desktop Client`
6. Click "Create"
7. You'll see a dialog with your Client ID and Client Secret
8. Click "Download JSON"
9. Save the downloaded file

### Step 5: Save the Credentials File

1. Rename the downloaded file to `google_client_secret.json`
2. Move it to your project's `credentials/` directory:
   ```bash
   mv ~/Downloads/client_secret_*.json /Users/marykate/Desktop/calendar-sync/credentials/google_client_secret.json
   ```

### Important Notes:

- **App Verification**: Your app will show a warning when you first authenticate because it's unverified. This is normal for personal projects. Click "Advanced" → "Go to Calendar Sync (unsafe)" to proceed.
- **Token Storage**: After first authentication, a `google_token.json` file will be created automatically. This stores your access and refresh tokens.
- **Scopes**: We're using read-only scopes for security. The sync won't modify your Google Calendar, only read from it.

---

## Notion API Setup

### Step 1: Create a Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "+ New integration"
3. Fill in the integration details:
   - **Name**: `Calendar Sync`
   - **Logo**: (optional) Upload an icon
   - **Associated workspace**: Select your workspace
4. Under "Capabilities", ensure these are selected:
   - ✓ Read content
   - ✓ Insert content
   - ✓ Update content
   - ✗ Read comments (not needed)
   - ✗ Insert comments (not needed)
   - ✗ Read user information without email (not needed)
   - ✗ Read user information with email (not needed)
5. Under "Content Capabilities":
   - ✓ Update content
   - ✗ No user information (select this)
6. Click "Submit"
7. You'll see your "Internal Integration Token"
8. Click "Show" and copy the token (starts with `secret_`)
9. **Save this token securely** - you'll need it for the `.env` file

### Step 2: Create the Calendar Events Database

1. Open Notion and navigate to where you want the database
2. Click "+ New page" or add a new block
3. Type `/database` and select "Database - Full page"
4. Name the database: **"Calendar Events"**
5. Add the following properties (click "+ New property" or the "+" at the right):

   | Property Name | Type | Options/Notes |
   |--------------|------|---------------|
   | **Title** | Title | (Default, rename from "Name") |
   | **Start Time** | Date | Include time: Yes, End date: No |
   | **End Time** | Date | Include time: Yes, End date: No |
   | **Source** | Select | Options: Personal Google, Work Google, MSU Student, MSU Employee |
   | **Location** | Text | Plain text |
   | **Description** | Text | Plain text |
   | **External ID** | Text | Plain text |
   | **Attendees** | Multi-select | Leave empty initially |
   | **Last Synced** | Date | Include time: Yes |
   | **URL** | URL | URL |
   | **Sync Status** | Select | Options: Active, Cancelled, Updated |

6. To add a property:
   - Click the "+" button at the right of the table header
   - Select the property type
   - Name it as shown above
   - For Select/Multi-select properties, add the options listed

### Step 3: Share Database with Integration

1. Open your "Calendar Events" database
2. Click the "..." menu at the top right
3. Scroll down and click "Connections" or "Add connections"
4. Find and select "Calendar Sync" (your integration)
5. Click "Confirm" or "Invite"

### Step 4: Get the Database ID

1. Open your "Calendar Events" database
2. Click "..." → "Copy link"
3. The URL will look like:
   ```
   https://www.notion.so/workspace/Calendar-Events-a1b2c3d4e5f67890a1b2c3d4e5f67890?v=...
   ```
4. Extract the 32-character ID (between the last dash and the "?"):
   ```
   a1b2c3d4e5f67890a1b2c3d4e5f67890
   ```
5. **Save this ID** - you'll need it for the `.env` file

### Optional: Format the Database View

For better organization, you can customize the database view:

1. **Group by**: Source (to see events by calendar)
2. **Filter**: Sync Status = Active (to hide cancelled events)
3. **Sort**: Start Time (ascending)

To save this view:
1. Set up the grouping, filtering, and sorting as above
2. Click the current view name (usually "All")
3. The settings are automatically saved

---

## Initial Configuration

### Step 1: Create Virtual Environment

```bash
cd /Users/marykate/Desktop/calendar-sync

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Your terminal prompt should now show (venv)
```

### Step 2: Install Dependencies

```bash
# Make sure virtual environment is activated (you should see "venv" in your prompt)
pip install --upgrade pip
pip install -r requirements.txt
```

This will install all required packages. It may take a few minutes.

### Step 3: Create .env File

```bash
# Copy the example file
cp .env.example .env

# Open .env in your text editor
# On Mac, you can use:
nano .env
# or
open -e .env
```

Fill in these values:

```bash
# === Google Calendar ===
GOOGLE_CLIENT_SECRET_PATH=credentials/google_client_secret.json
GOOGLE_TOKEN_PATH=credentials/google_token.json
GOOGLE_CALENDAR_IDS=primary
GOOGLE_CALENDAR_NAMES=Personal

# === Notion ===
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Paste your Notion token here
NOTION_CALENDAR_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Paste your database ID here

# === Sync Configuration ===
SYNC_LOOKBACK_DAYS=7
SYNC_LOOKAHEAD_DAYS=90
SYNC_INTERVAL_MINUTES=15

# === Logging ===
LOG_LEVEL=INFO
LOG_PATH=logs/sync.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5
```

Save and close the file.

### Step 4: Verify File Structure

Your project should look like this:

```
calendar-sync/
├── credentials/
│   ├── README.md
│   └── google_client_secret.json  ← You added this
├── logs/
├── scripts/
├── src/
├── tests/
├── .env  ← You created this
├── .env.example
├── .gitignore
├── requirements.txt
├── SETUP_GUIDES.md
└── TECHNICAL_PLAN.md
```

---

## Testing Your Setup

### Step 1: Test Authentication

Once the code is ready, you'll run:

```bash
cd /Users/marykate/Desktop/calendar-sync
source venv/bin/activate
python scripts/test_auth.py
```

This will:
1. Open a browser window for Google OAuth
2. Ask you to sign in and grant permissions
3. Test your Notion connection
4. Verify database access

**Expected Output:**
```
✓ Google Calendar authentication successful
✓ Notion API connection successful
✓ Calendar Events database accessible
✓ All systems ready!
```

### Step 2: Run Initial Sync (Dry Run)

```bash
python sync_orchestrator.py --dry-run
```

This will:
- Fetch events from Google Calendar
- Show what would be synced to Notion
- **NOT** actually create anything in Notion

**Expected Output:**
```
[DRY RUN] Would sync 15 events from Personal Google Calendar
[DRY RUN] Date range: 2026-01-07 to 2026-04-14

Sample events:
1. Team Meeting (2026-01-15 10:00 - 11:00)
2. Dentist Appointment (2026-01-18 14:00 - 15:00)
...
```

### Step 3: Run Actual Sync

If the dry run looks good:

```bash
python sync_orchestrator.py
```

This will actually sync events to Notion!

**Expected Output:**
```
Starting sync...
✓ Synced 15 events from Personal Google Calendar
✓ Created 15 new events in Notion
✓ Sync completed successfully in 8.3 seconds
```

---

## Troubleshooting

### Google Authentication Issues

**Problem**: "Access blocked: This app's request is invalid"

**Solution**:
1. Make sure you created an OAuth consent screen (Step 3 above)
2. Add yourself as a test user
3. The app status should be "Testing"

---

**Problem**: Browser shows "This app isn't verified"

**Solution**:
This is normal for personal projects. Click "Advanced" → "Go to Calendar Sync (unsafe)"

---

**Problem**: "Error: The credentials do not contain the necessary fields"

**Solution**:
1. Make sure you downloaded the OAuth credentials (not API key)
2. The file should start with: `{"installed":{"client_id":...`
3. Make sure the file is at `credentials/google_client_secret.json`

---

### Notion Issues

**Problem**: "401 Unauthorized" when connecting to Notion

**Solution**:
1. Verify your integration token starts with `secret_`
2. Check for spaces or newlines when copying the token
3. Make sure you copied the Internal Integration Token, not the Integration ID

---

**Problem**: "Could not find database"

**Solution**:
1. Verify you shared the database with your integration (Step 3)
2. Check that the database ID is correct (32 characters, no hyphens)
3. Make sure you copied just the ID, not the full URL

---

**Problem**: "Property [Property Name] does not exist"

**Solution**:
1. Make sure all properties were created in the database
2. Property names are case-sensitive
3. Check for typos in property names

---

### Python/Environment Issues

**Problem**: "Module not found" errors

**Solution**:
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

**Problem**: "Permission denied" when running scripts

**Solution**:
```bash
# Make scripts executable
chmod +x scripts/*.py
chmod +x sync_orchestrator.py

# Or run with python explicitly
python scripts/test_auth.py
```

---

### Rate Limiting

**Problem**: "429 Too Many Requests" from Notion

**Solution**:
- Notion API limit: 3 requests per second
- The sync automatically handles this with rate limiting
- If you see this error, reduce `SYNC_INTERVAL_MINUTES` in .env

---

**Problem**: Google API quota exceeded

**Solution**:
- Google Calendar API: 1,000,000 requests/day
- You're unlikely to hit this with normal usage
- Check the [quota page](https://console.cloud.google.com/apis/api/calendar-json.googleapis.com/quotas) in Google Cloud Console

---

## Next Steps

Once setup is complete:

1. ✓ Test authentication with `python scripts/test_auth.py`
2. ✓ Run dry-run sync to verify events are fetched correctly
3. ✓ Run actual sync to populate Notion
4. ✓ Set up automated scheduling (see main README.md)
5. ✓ Configure Notion for Claude.ai access

---

## Getting Help

If you encounter issues not covered here:

1. Check the logs at `logs/sync.log`
2. Run with verbose logging: `LOG_LEVEL=DEBUG python sync_orchestrator.py`
3. Check the main README.md for additional documentation
4. Review the TECHNICAL_PLAN.md for architecture details

---

**End of Setup Guides**
