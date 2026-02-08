# CLAUDE.md

## Project Overview

**Notion Life Sync** — A Python personal assistant that syncs data from Google Calendar, Garmin Connect, and Kroger into a unified Notion workspace. All data flows into interconnected Notion databases with a central Daily Tracking dimension table.

## Architecture

```
integrations/       → Read-only API clients (Google Calendar, Garmin, Kroger)
notion/             → Notion database writers (calendar.py, health.py)
orchestrators/      → CLI entry points (sync_calendar.py, sync_health.py, grocery_cart.py, meal_plan.py)
core/               → Shared infra: config, state management (SQLite), utilities
tests/              → Pytest suite with full mocking (no credentials needed)
credentials/        → OAuth tokens & API keys (gitignored)
grocery_lists/      → Weekly shopping list text files
```

## Claude Skills

### `/meal-plan` — Weekly Meal Plan Generator
Located at `.claude/skills/meal-plan/SKILL.md`. Generates a training-aware, AIP-compliant weekly meal plan by:
1. Running `orchestrators/meal_plan.py` to fetch next week's calendar events, workouts, and health metrics from Notion
2. Analyzing training load per day (heavy/moderate/light/rest)
3. Generating a 7-day meal plan with pre/post-workout nutrition
4. Writing a grocery list to `grocery_lists/` in the Kroger cart format
5. Publishing the meal plan as a Notion page

Usage: `/meal-plan` (next week), `/meal-plan 1` (two weeks out), `/meal-plan 2026-03-01` (specific week)

## Tech Stack

- **Language:** Python 3.10+
- **APIs:** Google Calendar (OAuth 2.0), Garmin Connect (garth), Kroger v1 (OAuth + PKCE), Notion API
- **Key libraries:** notion-client, garth, google-auth, requests, tenacity, python-dotenv
- **State:** SQLite (`state.db`) for sync tracking, deduplication, and event mapping
- **Testing:** pytest with pre-mocked third-party packages in conftest.py

## Common Commands

```bash
# Activate venv
source venv/bin/activate

# Run tests
pytest tests/ -v

# Calendar sync
python orchestrators/sync_calendar.py
python orchestrators/sync_calendar.py --dry-run
python orchestrators/sync_calendar.py --health-check

# Health/Garmin sync
python orchestrators/sync_health.py
python orchestrators/sync_health.py --workouts-only
python orchestrators/sync_health.py --metrics-only

# Grocery (Kroger)
python orchestrators/grocery_cart.py --find-store <ZIP>
python orchestrators/grocery_cart.py --auth
python orchestrators/grocery_cart.py --file grocery_lists/week7_feb9-15.txt
python orchestrators/grocery_cart.py --items "avocados" "milk"

# Meal plan data gathering (used by /meal-plan skill)
python orchestrators/meal_plan.py                          # Next week
python orchestrators/meal_plan.py --week-offset 1          # Two weeks out
python orchestrators/meal_plan.py --start-date 2026-02-16  # Specific week
```

## Configuration

All configuration lives in `.env` (see `.env.example` for template). Key variables:
- `NOTION_TOKEN`, `NOTION_CALENDAR_DB_ID`, `NOTION_WORKOUTS_DB_ID`, `NOTION_DAILY_TRACKING_DB_ID`
- `GOOGLE_CALENDAR_IDS`, `GOOGLE_CALENDAR_NAMES`
- `GARMIN_EMAIL`, `GARMIN_PASSWORD`
- `KROGER_CLIENT_ID`, `KROGER_CLIENT_SECRET`, `KROGER_LOCATION_ID`
- `SYNC_LOOKBACK_DAYS=90`, `SYNC_LOOKAHEAD_DAYS=365`, `UNIT_SYSTEM=imperial`

## Code Conventions

- Config classes in `core/config.py` each have a `.validate()` method returning `(bool, List[str])`
- External IDs are generated via `core/utils.generate_external_id()` for deduplication
- All API calls use `@retry_with_backoff()` decorator and `RateLimiter` from `core/utils.py`
- State tracking (sync timestamps, event→Notion page mappings) goes through `core/state_manager.py`
- Orchestrators use argparse with `--dry-run` and `--health-check` flags as standard
- Timezone is hardcoded to Mountain Time (America/Denver)
- Unit conversion helpers live in `core/utils.py` (imperial is default)

## Testing Notes

- Tests fully mock all third-party packages — no API credentials or network access needed
- `conftest.py` pre-mocks modules (google, garth, notion_client, etc.) before any imports
- Fixtures: `mock_garmin`, `sample_activities`, `sample_daily_metrics`
- No Kroger tests yet (integration is in active development)

## Current State

- Kroger integration is in active development (uncommitted changes in `integrations/kroger/client.py` and `orchestrators/grocery_cart.py`)
- Calendar and health syncs are stable and production-ready
- Cron scheduling is documented in README for automated syncs
