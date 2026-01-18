"""
Airtable Calendar Events sync operations.

This module handles syncing Google Calendar events to Airtable,
linking each event to the appropriate Day table record.
"""

from datetime import datetime
from typing import List, Dict, Optional
import logging
import pytz

from airtable.base_client import AirtableClient
from airtable.date_utils import date_to_day_id, format_airtable_datetime

logger = logging.getLogger(__name__)

# Bozeman, MT timezone
MOUNTAIN_TZ = pytz.timezone('America/Denver')


class AirtableCalendarSync:
    """Sync calendar events to Airtable."""

    def __init__(self, client: AirtableClient = None):
        """
        Initialize calendar sync.

        Args:
            client: AirtableClient instance (creates new if not provided)
        """
        self.client = client or AirtableClient()
        self.table = self.client.get_calendar_events_table()

    def _get_day_record_id(self, date_obj: datetime) -> Optional[str]:
        """
        Get the Day table record ID for a given date by querying the Day field.

        Args:
            date_obj: datetime object

        Returns:
            Record ID from Day table, or None if not found
        """
        # Format date as ISO string for querying (this matches the Day table's Day field format)
        iso_date = date_obj.strftime('%Y-%m-%d')

        # Query Day table for matching date
        # Use DATESTR because Day is a Date field type in Airtable
        day_table = self.client.get_day_table()
        formula = f'DATESTR({{Day}})="{iso_date}"'
        records = day_table.all(formula=formula, max_records=1)

        if records:
            logger.debug(f"Found Day record for {iso_date}: {records[0]['id']}")
            return records[0]['id']

        logger.warning(f"No Day record found for {iso_date} - Day link will be empty")
        return None

    def create_event(self, event_data: Dict) -> Dict:
        """
        Create a calendar event in Airtable.

        Args:
            event_data: Dictionary with event fields matching Airtable schema

        Returns:
            Dict: Created record from Airtable

        Example event_data structure:
        {
            'Event ID': 'google_calendar_event_id',
            'Title': 'Meeting with Team',
            'Start Time': datetime(2026, 1, 17, 14, 0),
            'End Time': datetime(2026, 1, 17, 15, 0),
            'All Day': False,
            'Calendar': 'Work',
            'Location': 'Conference Room A',
            'Description': 'Weekly team sync',
            'Attendees': 'john@example.com, jane@example.com',
            'Status': 'Confirmed',
            'Recurring': False
        }
        """
        # Parse start time
        start_time = event_data.get('Start Time')
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))

        # Handle all-day vs timed events differently
        is_all_day = event_data.get('All Day', False)
        end_time = event_data.get('End Time')

        if is_all_day:
            # All-day events: times are already localized to Mountain Time
            # Google Calendar returns end date as exclusive (day after), so we use start date for both
            # Set to 12:00am - 11:59pm on the SAME day and convert to UTC for Airtable storage
            start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            # Use start_time date for end_time (same day), set to 11:59pm
            end_time = start_time.replace(hour=23, minute=59, second=0, microsecond=0)

            # Convert Mountain Time to UTC for Airtable storage
            import pytz
            utc = pytz.UTC
            start_time_utc = start_time.astimezone(utc)
            end_time_utc = end_time.astimezone(utc)

            # Get Day record ID using the Mountain Time version
            day_record_id = self._get_day_record_id(start_time)

            # Store in Airtable as UTC (naive after removing tzinfo)
            start_time_for_db = start_time_utc.replace(tzinfo=None)
            end_time_for_db = end_time_utc.replace(tzinfo=None)
        else:
            # Timed events: may be in any timezone, convert to UTC for Airtable
            # Parse end time
            if end_time:
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

            # Convert to Mountain Time for Day record lookup
            import pytz
            utc = pytz.UTC
            start_time_mt = start_time.astimezone(MOUNTAIN_TZ) if start_time.tzinfo else MOUNTAIN_TZ.localize(start_time)
            day_record_id = self._get_day_record_id(start_time_mt)

            # Convert to UTC for Airtable storage
            start_time_utc = start_time.astimezone(utc) if start_time.tzinfo else utc.localize(start_time)
            end_time_utc = end_time.astimezone(utc) if (end_time and end_time.tzinfo) else (utc.localize(end_time) if end_time else None)

            # Store in Airtable as UTC (naive)
            start_time_for_db = start_time_utc.replace(tzinfo=None)
            end_time_for_db = end_time_utc.replace(tzinfo=None) if end_time_utc else None

        # Build Airtable record
        record = {
            'Name': event_data.get('Title'),  # Map Title to Name field
            'Event ID': event_data.get('Event ID'),
            'Title': event_data.get('Title'),
            'Start Time': format_airtable_datetime(start_time_for_db),
            'Date': (start_time.replace(tzinfo=None) if is_all_day else start_time_mt).strftime('%Y-%m-%d'),
            'All Day': is_all_day
        }

        # Link to Day table if record found
        if day_record_id:
            record['Day'] = [day_record_id]

        # Add end time and duration
        if end_time_for_db:
            record['End Time'] = format_airtable_datetime(end_time_for_db)
            # Calculate duration in minutes
            duration = (end_time_for_db - start_time_for_db).total_seconds() / 60
            record['Duration (min)'] = int(duration)

        if event_data.get('Calendar'):
            record['Calendar'] = event_data.get('Calendar')

        if event_data.get('Location'):
            record['Location'] = event_data.get('Location')

        if event_data.get('Description'):
            record['Description'] = event_data.get('Description')

        if event_data.get('Attendees'):
            record['Attendees'] = event_data.get('Attendees')

        if event_data.get('Status'):
            record['Status'] = event_data.get('Status')

        if event_data.get('Recurring') is not None:
            record['Recurring'] = event_data.get('Recurring')

        # Add sync timestamp
        record['Last Synced'] = format_airtable_datetime(datetime.now())

        logger.info(f"Creating event '{record['Title']}' for {start_time.strftime('%Y-%m-%d')}")
        created = self.table.create(record)
        return created

    def update_event(self, record_id: str, event_data: Dict) -> Dict:
        """
        Update an existing calendar event in Airtable.

        Args:
            record_id: Airtable record ID
            event_data: Dictionary with fields to update

        Returns:
            Dict: Updated record from Airtable
        """
        updates = {}

        # Handle all-day flag
        is_all_day = event_data.get('All Day', False)
        if 'All Day' in event_data:
            updates['All Day'] = is_all_day

        # Handle start time
        if 'Start Time' in event_data:
            start_time = event_data['Start Time']
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))

            # Convert from UTC to Mountain Time (or localize if naive)
            import pytz
            utc = pytz.UTC
            if is_all_day:
                # All-day: already in Mountain Time, set to 12:00am
                start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
                # Get Day record ID
                day_record_id = self._get_day_record_id(start_time)
                if day_record_id:
                    updates['Day'] = [day_record_id]
                # Convert to UTC for storage
                start_time_utc = start_time.astimezone(utc)
                updates['Start Time'] = format_airtable_datetime(start_time_utc.replace(tzinfo=None))
                updates['Date'] = start_time.strftime('%Y-%m-%d')

                # For all-day events, also set end time to 11:59pm same day
                end_time = start_time.replace(hour=23, minute=59, second=0, microsecond=0)
                end_time_utc = end_time.astimezone(utc)
                updates['End Time'] = format_airtable_datetime(end_time_utc.replace(tzinfo=None))
            else:
                # Timed event: convert to UTC
                if start_time.tzinfo is not None:
                    start_time_mt = start_time.astimezone(MOUNTAIN_TZ)
                else:
                    start_time_mt = MOUNTAIN_TZ.localize(start_time)

                day_record_id = self._get_day_record_id(start_time_mt)
                if day_record_id:
                    updates['Day'] = [day_record_id]

                start_time_utc = start_time.astimezone(utc) if start_time.tzinfo else utc.localize(start_time)
                updates['Start Time'] = format_airtable_datetime(start_time_utc.replace(tzinfo=None))
                updates['Date'] = start_time_mt.strftime('%Y-%m-%d')

        # Handle end time (only for timed events - all-day handled above)
        if 'End Time' in event_data and not is_all_day:
            end_time = event_data['End Time']
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

            # Convert to UTC for storage
            import pytz
            utc = pytz.UTC
            end_time_utc = end_time.astimezone(utc) if end_time.tzinfo else utc.localize(end_time)
            updates['End Time'] = format_airtable_datetime(end_time_utc.replace(tzinfo=None))

            # Recalculate duration if we have start time
            if 'Start Time' in event_data:
                start_time = event_data['Start Time']
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                # Convert from UTC to Mountain Time
                if start_time.tzinfo is not None:
                    start_time = start_time.astimezone(MOUNTAIN_TZ)
                if is_all_day:
                    start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
                duration = (end_time - start_time).total_seconds() / 60
                updates['Duration (min)'] = int(duration)

        # Handle Title - map to both Name and Title fields
        if 'Title' in event_data:
            updates['Name'] = event_data['Title']
            updates['Title'] = event_data['Title']

        # Copy other fields directly
        for field in ['Calendar', 'Location', 'Description', 'Attendees', 'Status', 'Recurring']:
            if field in event_data:
                updates[field] = event_data[field]

        # Update sync timestamp
        updates['Last Synced'] = format_airtable_datetime(datetime.now())

        logger.info(f"Updating event {record_id}")
        updated = self.table.update(record_id, updates)
        return updated

    def get_event_by_external_id(self, event_id: str) -> Optional[Dict]:
        """
        Find an event by its external Event ID (e.g., Google Calendar ID).

        Args:
            event_id: External event ID

        Returns:
            Dict or None: Event record if found, None otherwise
        """
        formula = f"{{Event ID}} = '{event_id}'"
        records = self.table.all(formula=formula)

        if records:
            return records[0]
        return None

    def delete_event(self, record_id: str) -> bool:
        """
        Delete a calendar event from Airtable.

        Args:
            record_id: Airtable record ID

        Returns:
            bool: True if deleted successfully
        """
        logger.info(f"Deleting event {record_id}")
        self.table.delete(record_id)
        return True

    def sync_event(self, event_data: Dict) -> Dict:
        """
        Sync an event to Airtable (create or update).

        This method checks if an event already exists by Event ID,
        and either creates a new record or updates the existing one.

        Args:
            event_data: Event data dictionary

        Returns:
            Dict: Synced event record
        """
        event_id = event_data.get('Event ID')
        if not event_id:
            raise ValueError("Event ID is required for syncing")

        existing = self.get_event_by_external_id(event_id)

        if existing:
            # Update existing event
            record_id = existing['id']
            return self.update_event(record_id, event_data)
        else:
            # Create new event
            return self.create_event(event_data)

    def get_events_by_day(self, day_id: str) -> List[Dict]:
        """
        Get all events for a specific day.

        Args:
            day_id: Day ID in d/m/yy format (e.g., "17/1/26")

        Returns:
            List[Dict]: List of event records
        """
        # Use SEARCH to find records linked to the day
        formula = f"SEARCH('{day_id}', {{Day}})"
        records = self.table.all(formula=formula)
        return records

    def get_events_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Get all events within a date range.

        Args:
            start_date: Start of range
            end_date: End of range

        Returns:
            List[Dict]: List of event records
        """
        start_str = format_airtable_datetime(start_date)
        end_str = format_airtable_datetime(end_date)

        formula = f"AND(IS_AFTER({{Start Time}}, '{start_str}'), IS_BEFORE({{Start Time}}, '{end_str}'))"
        records = self.table.all(formula=formula)
        return records
