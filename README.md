# Notion Life Sync

A Python system that syncs **Google Calendar** and **Garmin Connect** data into Notion, creating a unified personal dashboard for calendar events, workouts, and daily health tracking.

## What It Does

```
Google Calendar  ──>  Notion Calendar Events
Garmin Connect   ──>  Notion Garmin Activities
                 ──>  Notion Daily Tracking
```

- **Calendar sync** pulls events from one or more Google Calendars into a Notion database, with support for incremental sync, recurring events, multi-day events, and timezone handling (Mountain Time).
- **Health sync** pulls workouts, daily metrics (steps, sleep, stress, body battery), and body composition data from Garmin Connect into Notion databases.
- All Notion records are linked through a **Daily Tracking** dimension table, so calendar events and workouts relate back to the same day.

## Features

- **Incremental sync** via Google Calendar sync tokens — only fetches changes since last run
- **Duplicate prevention** using external ID tracking and event mapping
- **Dry-run mode** to preview changes without writing to Notion
- **Health checks** to verify credentials and API access before syncing
- **Date range filtering** to sync specific windows of time
- **Rate limiting and retry logic** with exponential backoff for API resilience
- **Rotating log files** for debugging production issues

## Project Structure

```
├── core/                        # Shared infrastructure
│   ├── config.py                # Configuration from .env
│   ├── utils.py                 # Logging, retry, rate limiting, unit converters
│   └── state_manager.py         # SQLite sync state and event mapping
│
├── integrations/                # API clients (read-only)
│   ├── google_calendar/sync.py  # Google Calendar OAuth + event fetching
│   └── garmin/sync.py           # Garmin Connect auth + data fetching
│
├── notion/                      # Notion database writers
│   ├── calendar.py              # Calendar Events database operations
│   └── health.py                # Activities + Daily Tracking operations
│
├── orchestrators/               # CLI entry points
│   ├── sync_calendar.py         # Google Calendar → Notion
│   └── sync_health.py           # Garmin → Notion
│
└── tests/                       # Test suite (57 tests)
    ├── conftest.py              # Shared fixtures and third-party mocks
    ├── test_sync_calendar.py    # Calendar orchestrator tests
    └── test_sync_health.py      # Health orchestrator tests
```

## Setup

### Prerequisites

- Python 3.10+
- A [Notion integration](https://www.notion.so/my-integrations) with access to your target databases
- A [Google Cloud project](https://console.cloud.google.com/) with the Calendar API enabled and OAuth credentials
- A [Garmin Connect](https://connect.garmin.com/) account (for health sync)

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/notion-life-sync.git
cd notion-life-sync

python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

| Variable | Required For | Description |
|---|---|---|
| `NOTION_TOKEN` | All syncs | Notion integration token (`ntn_` or `secret_`) |
| `NOTION_CALENDAR_DB_ID` | Calendar | Notion database ID for calendar events |
| `NOTION_WORKOUTS_DB_ID` | Health | Notion database ID for Garmin activities |
| `NOTION_DAILY_TRACKING_DB_ID` | Health | Notion database ID for daily health metrics |
| `GOOGLE_CALENDAR_IDS` | Calendar | Comma-separated Google Calendar IDs |
| `GOOGLE_CALENDAR_NAMES` | Calendar | Comma-separated display names (must match IDs) |
| `GARMIN_EMAIL` | Health | Garmin Connect email |
| `GARMIN_PASSWORD` | Health | Garmin Connect password |

See `.env.example` for the full list of optional settings (sync window, logging, units).

### Google Calendar Credentials

1. Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the **Google Calendar API**
3. Create **OAuth 2.0 Client ID** credentials (Desktop application type)
4. Download the JSON file and save it to `credentials/google_client_secret.json`
5. On first run, a browser window opens to authorize read-only calendar access

## Usage

### Calendar Sync

```bash
python orchestrators/sync_calendar.py                # sync all calendars
python orchestrators/sync_calendar.py --dry-run       # preview without writing
python orchestrators/sync_calendar.py --health-check  # verify config and API access
python orchestrators/sync_calendar.py --start-date 2025-01-01 --end-date 2025-12-31
```

### Health Sync

```bash
python orchestrators/sync_health.py                  # full sync (workouts + metrics + body)
python orchestrators/sync_health.py --workouts-only   # activities only
python orchestrators/sync_health.py --metrics-only    # daily metrics only
python orchestrators/sync_health.py --body-only       # body composition only
python orchestrators/sync_health.py --dry-run
python orchestrators/sync_health.py --health-check
python orchestrators/sync_health.py --start-date 2025-01-01 --end-date 2025-01-31
```

### Automated Sync (cron)

```bash
crontab -e

# Calendar — every 15 minutes
*/15 * * * * cd /path/to/notion-life-sync && venv/bin/python orchestrators/sync_calendar.py >> logs/cron.log 2>&1

# Health — twice daily
0 7,19 * * * cd /path/to/notion-life-sync && venv/bin/python orchestrators/sync_health.py >> logs/cron.log 2>&1
```

## Notion Database Schemas

You'll need to create these databases in Notion and share them with your integration.

### Calendar Events

| Property | Type | Description |
|---|---|---|
| Title | Title | Event name |
| Start Time | Date | Event start (timezone-aware) |
| End Time | Date | Event end |
| Calendar | Select | Source calendar name |
| Location | Text | Event location |
| Attendees | Text | Comma-separated attendee list |
| Status | Select | Confirmed, Tentative, or Cancelled |
| Recurring | Checkbox | Whether the event is recurring |
| Event ID | Text | Google Calendar event ID (used for sync) |
| Day | Relation | Link to Daily Tracking |

### Garmin Activities

| Property | Type | Description |
|---|---|---|
| Title | Title | Activity name |
| Activity Type | Select | Running, Cycling, Swimming, etc. |
| Start Time | Date | Activity start time |
| Duration | Number | Duration in seconds |
| Distance | Number | Distance in miles |
| Avg Pace | Text | Average pace (min/mile) |
| Avg HR | Number | Average heart rate (bpm) |
| Calories | Number | Calories burned |
| Elevation | Number | Elevation gain in feet |
| Day | Relation | Link to Daily Tracking |

### Daily Tracking

| Property | Type | Description |
|---|---|---|
| Day | Title | Date (`YYYY-MM-DD`) |
| Steps | Number | Daily step count |
| Sleep Hours | Number | Hours of sleep |
| Resting HR | Number | Resting heart rate |
| Stress Level | Number | Average stress score |
| Body Battery | Number | Garmin body battery level |
| Weight | Number | Weight in lbs |
| Body Fat % | Number | Body fat percentage |

## Testing

```bash
source venv/bin/activate
pytest tests/ -v
```

Tests mock all external APIs, so they run without credentials or network access.

## Troubleshooting

| Problem | Solution |
|---|---|
| Config validation fails | Run `--health-check` to see which values are missing |
| Notion connection fails | Verify your token starts with `ntn_` or `secret_` and the integration has been shared with your databases |
| Google Calendar auth fails | Delete `credentials/google_token.json` and re-authenticate on next run |
| Garmin connection fails | Check email and password in `.env`; verify Garmin Connect works in a browser |
| Duplicate events appearing | Run a full sync (without `--start-date`) to reconcile state |

## Security

- All credentials are stored in `.env` (gitignored) and never committed
- Google OAuth tokens are cached locally in `credentials/` (gitignored)
- Garmin session tokens are cached by the `garth` library in your home directory
- The sync state database (`state.db`) stores only IDs and timestamps, no sensitive data

## License

[MIT](LICENSE)
