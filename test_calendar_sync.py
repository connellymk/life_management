"""
Test Google Calendar sync to Airtable.

This script fetches events from Google Calendar and syncs them to Airtable.
"""

from datetime import datetime, timedelta
from integrations.google_calendar.sync import GoogleCalendarSync
from airtable.calendar import AirtableCalendarSync
from core.config import GoogleCalendarConfig
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    print("=" * 60)
    print("GOOGLE CALENDAR TO AIRTABLE SYNC TEST")
    print("=" * 60)
    print()

    # Initialize Google Calendar
    logger.info("Connecting to Google Calendar...")
    gcal_sync = GoogleCalendarSync()

    if not gcal_sync.authenticate():
        logger.error("Failed to authenticate with Google Calendar")
        logger.info("Please ensure credentials/google_client_secret.json exists")
        return

    logger.info("Connected to Google Calendar")

    # Initialize Airtable
    logger.info("Connecting to Airtable...")
    try:
        airtable_sync = AirtableCalendarSync()
        logger.info("Connected to Airtable")
    except Exception as e:
        logger.error(f"Failed to connect to Airtable: {e}")
        return

    print()

    # Sync all events for 2026
    start_date = datetime(2026, 1, 1)
    end_date = datetime(2026, 12, 31)

    logger.info(f"Fetching events from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print()

    # Get configured calendars
    calendar_ids = GoogleCalendarConfig.GOOGLE_CALENDAR_IDS
    calendar_names = GoogleCalendarConfig.GOOGLE_CALENDAR_NAMES

    total_synced = 0
    total_errors = 0

    for cal_id, cal_name in zip(calendar_ids, calendar_names):
        logger.info(f"Processing calendar: {cal_name}")

        try:
            # Fetch events from Google Calendar
            events = gcal_sync.get_calendar_events(
                calendar_id=cal_id,
                start_date=start_date,
                end_date=end_date
            )

            logger.info(f"  Found {len(events)} events")

            # Sync each event to Airtable
            for event in events:
                try:
                    # Parse event data
                    event_id = event['id']
                    title = event.get('summary', '(No title)')

                    # Parse start/end times
                    start = event['start']
                    end = event['end']

                    # Handle all-day events
                    if 'date' in start:
                        # All-day event - dates are already in local timezone
                        # Parse as naive datetime and localize to Mountain Time
                        import pytz
                        MOUNTAIN_TZ = pytz.timezone('America/Denver')
                        start_time = datetime.fromisoformat(start['date'])
                        end_time = datetime.fromisoformat(end['date'])
                        # Localize to Mountain Time (make timezone-aware)
                        start_time = MOUNTAIN_TZ.localize(start_time)
                        end_time = MOUNTAIN_TZ.localize(end_time)
                        all_day = True
                    else:
                        # Timed event
                        start_time = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                        end_time = datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00'))
                        all_day = False

                    # Build event data for Airtable
                    event_data = {
                        'Event ID': event_id,
                        'Title': title,
                        'Start Time': start_time,
                        'End Time': end_time,
                        'All Day': all_day,
                        'Calendar': cal_name,
                        'Location': event.get('location', ''),
                        'Description': event.get('description', ''),
                        'Attendees': ', '.join([a.get('email', '') for a in event.get('attendees', [])]),
                        'Status': event.get('status', 'confirmed').capitalize(),
                        'Recurring': 'recurringEventId' in event
                    }

                    # Sync to Airtable
                    result = airtable_sync.sync_event(event_data)

                    if start_time.hour == 0 and start_time.minute == 0:
                        logger.info(f"    OK {title} ({start_time.strftime('%Y-%m-%d')})")
                    else:
                        logger.info(f"    OK {title} ({start_time.strftime('%Y-%m-%d %H:%M')})")
                    total_synced += 1

                except Exception as e:
                    logger.error(f"    FAIL Failed to sync '{title}': {e}")
                    total_errors += 1

        except Exception as e:
            logger.error(f"  Failed to fetch events from {cal_name}: {e}")
            total_errors += 1

        print()

    print("=" * 60)
    print("SYNC COMPLETE")
    print("=" * 60)
    print(f"Total synced: {total_synced}")
    print(f"Total errors: {total_errors}")
    print()
    if total_synced > 0:
        print("SUCCESS! Check your Airtable base to see the synced events!")
    print()


if __name__ == "__main__":
    main()
