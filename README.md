# Calendar Sync Integration System

A Python-based system to consolidate calendar events and tasks from multiple sources (Google Calendar, Microsoft Calendar, Strava, GitHub) into Notion, creating a single source of truth for personal productivity and time management.

## Overview

This system syncs your calendar events and tasks into Notion, allowing you to:
- **View all events in one place** - Personal, work, and school calendars unified
- **Use Claude.ai as your assistant** - With everything in Notion, Claude can help you plan and manage your time
- **Automated syncing** - Set it and forget it - events sync automatically
- **Training integration** - Track workouts alongside your calendar (coming soon)
- **Smart scheduling** - Let AI help you optimize your time

## Current Status

**✓ Phase 1 Complete - MVP:**
- ✅ Google Calendar → Notion sync
- ✅ OAuth authentication
- ✅ Duplicate prevention
- ✅ Automated scheduling ready
- ✅ Dry-run testing mode

**🚧 Coming Soon:**
- 📊 State management with SQLite (Phase 2)
- 🔄 Incremental syncing (Phase 2)
- 📅 Microsoft Calendar sync (Phase 2)
- 🏃 Strava/training sync (Phase 2)
- 📈 Dashboard and analytics (Phase 3)

## Quick Start

### Prerequisites

- Mac with Python 3.9 or higher
- Google account with calendar events
- Notion account

### Installation

1. **Clone or download this repository**
   ```bash
   cd /Users/marykate/Desktop/calendar-sync
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up credentials**

   Follow the detailed instructions in [SETUP_GUIDES.md](SETUP_GUIDES.md):
   - Set up Google Calendar API credentials
   - Create Notion integration and databases
   - Configure `.env` file

5. **Test authentication**
   ```bash
   python scripts/test_auth.py
   ```

6. **Run your first sync!**
   ```bash
   # Dry run first (see what would be synced)
   python sync_orchestrator.py --dry-run

   # Actual sync
   python sync_orchestrator.py
   ```

## Usage

### Basic Commands

```bash
# Full sync (all calendars)
python sync_orchestrator.py

# Dry run (see what would be synced without making changes)
python sync_orchestrator.py --dry-run

# Health check (verify all connections are working)
python sync_orchestrator.py --health-check

# Sync only calendars (skip training, etc.)
python sync_orchestrator.py --calendars-only
```

### Automated Syncing

To run syncs automatically every 15 minutes:

**Option 1: Using cron (recommended for Mac)**

1. Open crontab:
   ```bash
   crontab -e
   ```

2. Add this line (replace paths with your actual paths):
   ```cron
   */15 * * * * cd /Users/marykate/Desktop/calendar-sync && /Users/marykate/Desktop/calendar-sync/venv/bin/python sync_orchestrator.py >> logs/cron.log 2>&1
   ```

3. Save and exit

**Option 2: Using Python schedule (runs continuously)**

Create a file `run_scheduled.py`:

```python
import schedule
import time
import subprocess

def run_sync():
    subprocess.run(["python", "sync_orchestrator.py"])

schedule.every(15).minutes.do(run_sync)

print("Scheduler started. Running sync every 15 minutes...")
while True:
    schedule.run_pending()
    time.sleep(60)
```

Then run it:
```bash
python run_scheduled.py
```

## Project Structure

```
calendar-sync/
├── src/                      # Source code
│   ├── config.py            # Configuration management
│   ├── utils.py             # Utility functions (logging, retry, etc.)
│   ├── google_sync.py       # Google Calendar integration
│   ├── notion_sync.py       # Notion API wrapper
│   ├── microsoft_sync.py    # (Future) Microsoft Calendar integration
│   └── training_sync.py     # (Future) Strava/training integration
│
├── scripts/                  # Utility scripts
│   └── test_auth.py         # Test authentication
│
├── credentials/              # OAuth credentials (gitignored)
│   └── google_client_secret.json
│
├── logs/                     # Log files (gitignored)
│   └── sync.log
│
├── tests/                    # Unit tests (future)
│
├── .env                      # Configuration (gitignored)
├── .env.example              # Configuration template
├── requirements.txt          # Python dependencies
├── sync_orchestrator.py      # Main sync script
├── README.md                 # This file
├── SETUP_GUIDES.md          # Detailed setup instructions
└── TECHNICAL_PLAN.md        # Architecture and implementation plan
```

## Configuration

All configuration is in `.env` file:

```bash
# Google Calendar
GOOGLE_CALENDAR_IDS=primary
GOOGLE_CALENDAR_NAMES=Personal

# Notion
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_CALENDAR_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Sync Settings
SYNC_LOOKBACK_DAYS=7
SYNC_LOOKAHEAD_DAYS=90
SYNC_INTERVAL_MINUTES=15

# Logging
LOG_LEVEL=INFO
LOG_PATH=logs/sync.log
```

See `.env.example` for all available options.

## Notion Database Schema

Your Notion "Calendar Events" database should have these properties:

| Property Name | Type | Notes |
|--------------|------|-------|
| Title | Title | Event name |
| Start Time | Date | Include time, can have end date |
| End Time | Date | Include time (optional, can use range in Start Time) |
| Source | Select | Options: Personal Google, Work Google, etc. |
| Location | Text | Event location |
| Description | Text | Event description |
| External ID | Text | For duplicate prevention |
| Attendees | Multi-select | Event attendees |
| Last Synced | Date | Last sync timestamp |
| URL | URL | Link to original event |
| Sync Status | Select | Options: Active, Cancelled, Updated |

## Using with Claude.ai

Once your events are in Notion, you can use Claude.ai as your personal assistant:

1. **Share your Notion database** with Claude by providing the database link

2. **Ask Claude to help you:**
   - "What's my schedule this week?"
   - "When's my next free 2-hour block?"
   - "Help me plan my research time around my classes"
   - "Review my training schedule for the week"
   - "What conflicts do I have next week?"

3. **Let Claude assist with planning:**
   - Block time for focused work
   - Schedule tasks around your existing commitments
   - Balance school, work, and training

## Troubleshooting

### "401 Unauthorized" from Google
- Your OAuth token may have expired
- Delete `credentials/google_token.json` and re-authenticate
- Run `python scripts/test_auth.py`

### "Object not found" from Notion
- Make sure you shared the database with your integration
- Verify the database ID in `.env` is correct
- Check that the integration has the right permissions

### Events not appearing
- Check the date range settings (`SYNC_LOOKBACK_DAYS`, `SYNC_LOOKAHEAD_DAYS`)
- Verify events exist in that range in your Google Calendar
- Check logs at `logs/sync.log` for errors

### Duplicate events
- The system uses External ID to prevent duplicates
- If you see duplicates, check that the External ID property exists in your database
- You can manually delete duplicates and re-run the sync

For more troubleshooting help, see [SETUP_GUIDES.md](SETUP_GUIDES.md#troubleshooting).

## Development

### Running Tests

```bash
# Test authentication
python scripts/test_auth.py

# Test individual modules
python src/config.py          # Test configuration
python src/utils.py           # Test utilities
python src/google_sync.py     # Test Google Calendar
python src/notion_sync.py     # Test Notion
```

### Viewing Logs

```bash
# View recent logs
tail -f logs/sync.log

# View all logs
less logs/sync.log

# Search logs
grep "ERROR" logs/sync.log
```

### Code Style

This project uses:
- Black for formatting
- Flake8 for linting
- Type hints for clarity

```bash
# Format code
black src/ scripts/ *.py

# Lint code
flake8 src/ scripts/ *.py
```

## Roadmap

### Phase 1: MVP ✅ (Current)
- Google Calendar sync
- Basic Notion integration
- OAuth authentication
- Duplicate prevention

### Phase 2: Enhancement 🚧 (In Progress)
- SQLite state management
- Incremental syncing
- Microsoft Calendar integration
- Strava/training sync
- Performance optimization

### Phase 3: Advanced Features 📅 (Planned)
- Dashboard and statistics
- Conflict detection
- Smart scheduling suggestions
- Mobile notifications
- GitHub integration

## Security Notes

- **Never commit `.env` file** - Contains secrets
- **Never commit credential files** - OAuth tokens are sensitive
- **Use read-only scopes** where possible
- **Regularly rotate tokens** if compromised
- **Keep dependencies updated** for security patches

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check [SETUP_GUIDES.md](SETUP_GUIDES.md) for setup help
2. Check [TECHNICAL_PLAN.md](TECHNICAL_PLAN.md) for architecture details
3. Review logs at `logs/sync.log`
4. Open an issue in the repository

## Acknowledgments

Built with:
- [Google Calendar API](https://developers.google.com/calendar)
- [Notion API](https://developers.notion.com/)
- [notion-client](https://github.com/ramnes/notion-sdk-py)

---

**Status**: MVP Complete - Ready for daily use!

**Last Updated**: January 14, 2026
