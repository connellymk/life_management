#!/usr/bin/env python3
"""
Meal Plan Data Gatherer
Fetches next week's calendar events and planned workouts from Notion
so Claude can generate a training-aware meal plan.

Usage:
    python orchestrators/meal_plan.py
    python orchestrators/meal_plan.py --week-offset 1    # Two weeks out
    python orchestrators/meal_plan.py --start-date 2026-02-09
"""

import sys
import json
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import Config
from core.utils import setup_logging

logger = setup_logging("meal_plan")

NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _make_request(method: str, endpoint: str, data=None) -> dict:
    """Make a Notion API request."""
    import requests

    url = f"{NOTION_API_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {Config.NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }
    response = requests.request(method=method, url=url, headers=headers, json=data)
    if not response.ok:
        logger.error(f"Notion API error: {response.status_code} - {response.text}")
        response.raise_for_status()
    return response.json()


def get_week_dates(start_date: datetime = None, week_offset: int = 0) -> tuple[datetime, datetime]:
    """
    Calculate the start (Monday) and end (Sunday) of the target week.

    Args:
        start_date: Explicit start date (overrides week_offset)
        week_offset: 0 = next week, 1 = two weeks out, etc.

    Returns:
        (monday, sunday) as datetime objects
    """
    today = datetime.now().date()

    if start_date:
        # Use the Monday of the week containing start_date
        monday = start_date - timedelta(days=start_date.weekday())
    else:
        # Next Monday from today + offset
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7  # If today is Monday, go to next Monday
        monday = today + timedelta(days=days_until_monday + (7 * week_offset))

    sunday = monday + timedelta(days=6)
    return monday, sunday


def fetch_calendar_events(monday, sunday) -> list[dict]:
    """
    Fetch calendar events for the target week from Notion.

    Returns list of simplified event dicts with title, start, end, location, source.
    """
    db_id = Config.NOTION_CALENDAR_DB_ID
    if not db_id:
        logger.warning("NOTION_CALENDAR_DB_ID not set, skipping calendar events")
        return []

    start_str = monday.isoformat()
    end_str = (sunday + timedelta(days=1)).isoformat()  # Inclusive of Sunday

    query = {
        "filter": {
            "and": [
                {
                    "property": "Start Time",
                    "date": {"on_or_after": start_str},
                },
                {
                    "property": "Start Time",
                    "date": {"before": end_str},
                },
                {
                    "property": "Sync Status",
                    "select": {"does_not_equal": "Cancelled"},
                },
            ]
        },
        "sorts": [{"property": "Start Time", "direction": "ascending"}],
        "page_size": 100,
    }

    try:
        response = _make_request("POST", f"/databases/{db_id}/query", query)
        results = response.get("results", [])
    except Exception as e:
        logger.error(f"Failed to fetch calendar events: {e}")
        return []

    events = []
    for page in results:
        props = page.get("properties", {})

        title_prop = props.get("Title", {}).get("title", [])
        title = title_prop[0]["plain_text"] if title_prop else "(No title)"

        start_prop = props.get("Start Time", {}).get("date", {})
        start = start_prop.get("start", "") if start_prop else ""

        end_prop = props.get("End Time", {}).get("date", {})
        end = end_prop.get("start", "") if end_prop else ""

        source_prop = props.get("Source", {}).get("select", {})
        source = source_prop.get("name", "") if source_prop else ""

        location_prop = props.get("Location", {}).get("rich_text", [])
        location = location_prop[0]["plain_text"] if location_prop else ""

        events.append({
            "title": title,
            "start": start,
            "end": end,
            "source": source,
            "location": location,
        })

    return events


def fetch_planned_workouts(monday, sunday) -> list[dict]:
    """
    Fetch workouts/activities for the target week from Notion.

    Returns list of simplified workout dicts.
    """
    db_id = Config.NOTION_WORKOUTS_DB_ID
    if not db_id:
        logger.warning("NOTION_WORKOUTS_DB_ID not set, skipping workouts")
        return []

    start_str = monday.isoformat()
    end_str = (sunday + timedelta(days=1)).isoformat()

    query = {
        "filter": {
            "and": [
                {
                    "property": "Date",
                    "date": {"on_or_after": start_str},
                },
                {
                    "property": "Date",
                    "date": {"before": end_str},
                },
            ]
        },
        "sorts": [{"property": "Date", "direction": "ascending"}],
        "page_size": 100,
    }

    try:
        response = _make_request("POST", f"/databases/{db_id}/query", query)
        results = response.get("results", [])
    except Exception as e:
        logger.error(f"Failed to fetch workouts: {e}")
        return []

    workouts = []
    for page in results:
        props = page.get("properties", {})

        name_prop = props.get("Name", {}).get("title", [])
        name = name_prop[0]["plain_text"] if name_prop else "Workout"

        date_prop = props.get("Date", {}).get("date", {})
        date = date_prop.get("start", "") if date_prop else ""

        type_prop = props.get("Activity Type", {}).get("select", {})
        activity_type = type_prop.get("name", "") if type_prop else ""

        duration = props.get("Duration", {}).get("number")
        distance = props.get("Distance", {}).get("number")
        calories = props.get("Calories", {}).get("number")

        workouts.append({
            "name": name,
            "date": date,
            "type": activity_type,
            "duration_minutes": duration,
            "distance_miles": distance,
            "calories": calories,
        })

    return workouts


def fetch_recent_health_metrics(days: int = 7) -> list[dict]:
    """
    Fetch recent daily tracking data for context on current fitness state.

    Returns list of daily metric dicts for the past N days.
    """
    db_id = Config.NOTION_DAILY_TRACKING_DB_ID
    if not db_id:
        logger.warning("NOTION_DAILY_TRACKING_DB_ID not set, skipping health metrics")
        return []

    today = datetime.now().date()
    start = (today - timedelta(days=days)).isoformat()

    query = {
        "filter": {
            "property": "Date",
            "date": {"on_or_after": start},
        },
        "sorts": [{"property": "Date", "direction": "ascending"}],
        "page_size": 100,
    }

    try:
        response = _make_request("POST", f"/databases/{db_id}/query", query)
        results = response.get("results", [])
    except Exception as e:
        logger.error(f"Failed to fetch health metrics: {e}")
        return []

    metrics = []
    for page in results:
        props = page.get("properties", {})

        date_prop = props.get("Date", {}).get("date", {})
        date = date_prop.get("start", "") if date_prop else ""

        row = {"date": date}

        number_fields = {
            "Steps": "steps",
            "Active Calories": "active_calories",
            "Total Calories": "total_calories",
            "Sleep Duration (Hrs)": "sleep_hours",
            "Sleep Score": "sleep_score",
            "Stress Level": "stress_level",
            "Body Battery": "body_battery",
            "Weight (lbs)": "weight_lbs",
            "Intensity Minutes": "intensity_minutes",
        }

        for notion_name, key in number_fields.items():
            val = props.get(notion_name, {}).get("number")
            if val is not None:
                row[key] = val

        metrics.append(row)

    return metrics


def gather_meal_plan_context(
    start_date: datetime = None,
    week_offset: int = 0,
) -> dict:
    """
    Gather all data needed for meal plan generation.

    Returns a structured dict with week dates, events, workouts, and health context.
    """
    monday, sunday = get_week_dates(start_date=start_date, week_offset=week_offset)

    logger.info(f"Gathering meal plan data for week of {monday} — {sunday}")

    events = fetch_calendar_events(monday, sunday)
    workouts = fetch_planned_workouts(monday, sunday)
    health = fetch_recent_health_metrics(days=7)

    context = {
        "week": {
            "start": monday.isoformat(),
            "end": sunday.isoformat(),
            "label": f"{monday.strftime('%b %-d')} — {sunday.strftime('%b %-d, %Y')}",
        },
        "calendar_events": events,
        "planned_workouts": workouts,
        "recent_health_metrics": health,
        "summary": {
            "total_events": len(events),
            "total_workouts": len(workouts),
            "workout_types": list(set(w["type"] for w in workouts if w.get("type"))),
            "total_training_minutes": sum(
                w.get("duration_minutes", 0) or 0 for w in workouts
            ),
            "avg_daily_calories": (
                round(
                    sum(m.get("total_calories", 0) or 0 for m in health)
                    / max(len(health), 1)
                )
                if health
                else None
            ),
            "avg_sleep_hours": (
                round(
                    sum(m.get("sleep_hours", 0) or 0 for m in health)
                    / max(len(health), 1),
                    1,
                )
                if health
                else None
            ),
        },
    }

    return context


def main():
    parser = argparse.ArgumentParser(
        description="Gather schedule and training data for meal planning"
    )
    parser.add_argument(
        "--week-offset",
        type=int,
        default=0,
        help="0 = next week (default), 1 = two weeks out, etc.",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Explicit start date (YYYY-MM-DD), uses the week containing this date",
    )

    args = parser.parse_args()

    # Validate config
    is_valid, errors = Config.validate()
    if not is_valid:
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)

    start_date = None
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
        except ValueError:
            logger.error("Invalid date format. Use YYYY-MM-DD.")
            sys.exit(1)

    context = gather_meal_plan_context(
        start_date=start_date,
        week_offset=args.week_offset,
    )

    # Output as JSON for Claude to consume
    print(json.dumps(context, indent=2, default=str))


if __name__ == "__main__":
    main()
