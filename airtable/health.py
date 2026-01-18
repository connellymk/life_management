"""
Airtable Health data sync operations.

This module handles syncing Garmin health data to Airtable:
- Training Sessions (workouts/activities)
- Health Metrics (daily health data)
- Body Metrics (weight/composition)
"""

from datetime import datetime
from typing import List, Dict, Optional
import logging

from airtable.base_client import AirtableClient
from airtable.date_utils import date_to_day_id, date_to_week_id, format_airtable_datetime

logger = logging.getLogger(__name__)


class AirtableTrainingSessionsSync:
    """Sync training sessions (Garmin activities) to Airtable."""

    def __init__(self, client: AirtableClient = None):
        """
        Initialize training sessions sync.

        Args:
            client: AirtableClient instance (creates new if not provided)
        """
        self.client = client or AirtableClient()
        self.table = self.client.get_training_sessions_table()

    def create_session(self, session_data: Dict) -> Dict:
        """
        Create a training session in Airtable.

        Args:
            session_data: Dictionary with session fields

        Returns:
            Dict: Created record from Airtable

        Example session_data:
        {
            'Activity ID': '12345678',
            'Activity Name': 'Morning Run',
            'Activity Type': 'Running',
            'Start Time': datetime(2026, 1, 17, 7, 0),
            'Duration': 3600,  # seconds
            'Distance': 10.5,  # miles
            'Calories': 850,
            'Average HR': 145,
            'Max HR': 165,
            'Average Pace': 9.5,  # min/mile
            'Average Speed': 6.3,  # mph
            'Elevation Gain': 250,  # feet
            'Garmin URL': 'https://connect.garmin.com/modern/activity/12345678',
            'Notes': 'Felt great today!'
        }
        """
        # Convert start time to Day ID
        start_time = session_data.get('Start Time')
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))

        day_value = date_to_day_id(start_time)

        # Look up actual Airtable record ID for Day
        day_record_id = self.client.get_day_record_id(day_value)

        # Build Airtable record
        activity_name = session_data.get('Activity Name')
        record = {
            'Name': activity_name,  # Use Activity Name as Name field
            'Activity ID': str(session_data.get('Activity ID')),
            'Activity Type': session_data.get('Activity Type'),
            'Day': [day_record_id],  # Link to Day table using actual record ID
            'Start Time': format_airtable_datetime(start_time),
            'Source': 'Garmin',  # Set source to Garmin
        }

        # Add optional numeric fields (using actual Airtable field names)
        if session_data.get('Duration') is not None:
            record['Duration (min)'] = session_data.get('Duration')

        if session_data.get('Distance') is not None:
            record['Distance (mi)'] = session_data.get('Distance')

        if session_data.get('Calories') is not None:
            record['Calories'] = session_data.get('Calories')

        if session_data.get('Average HR') is not None:
            record['Avg HR'] = session_data.get('Average HR')

        if session_data.get('Max HR') is not None:
            record['Max HR'] = session_data.get('Max HR')

        if session_data.get('Average Pace') is not None:
            record['Avg Pace (min/mi)'] = session_data.get('Average Pace')

        if session_data.get('Elevation Gain') is not None:
            record['Elevation Gain (ft)'] = session_data.get('Elevation Gain')

        if session_data.get('Garmin URL'):
            record['Garmin URL'] = session_data.get('Garmin URL')

        # Add detailed metrics from activity summary
        if session_data.get('Aerobic Training Effect') is not None:
            record['Aerobic Training Effect'] = session_data.get('Aerobic Training Effect')
            # Also populate old Training Effect field with aerobic TE for backward compatibility
            record['Training Effect'] = session_data.get('Aerobic Training Effect')
        elif session_data.get('Training Effect') is not None:
            # Fallback to old Training Effect field if provided
            record['Training Effect'] = session_data.get('Training Effect')
        if session_data.get('Anaerobic Training Effect') is not None:
            record['Anaerobic Training Effect'] = session_data.get('Anaerobic Training Effect')
        if session_data.get('Activity Training Load') is not None:
            record['Activity Training Load'] = session_data.get('Activity Training Load')
        if session_data.get('Avg Grade Adjusted Speed') is not None:
            record['Avg Grade Adjusted Speed (mph)'] = session_data.get('Avg Grade Adjusted Speed')
        if session_data.get('Avg Moving Speed') is not None:
            record['Avg Moving Speed (mph)'] = session_data.get('Avg Moving Speed')
        if session_data.get('Avg Temperature') is not None:
            record['Avg Temperature (F)'] = session_data.get('Avg Temperature')
        if session_data.get('Body Battery Change') is not None:
            record['Body Battery Change'] = session_data.get('Body Battery Change')
        if session_data.get('Moving Duration') is not None:
            record['Moving Duration (min)'] = session_data.get('Moving Duration')

        if session_data.get('Notes'):
            record['Notes'] = session_data.get('Notes')

        logger.info(f"Creating session '{activity_name}' for {day_value}")
        created = self.table.create(record)
        return created

    def update_session(self, record_id: str, session_data: Dict) -> Dict:
        """
        Update an existing training session in Airtable.

        Args:
            record_id: Airtable record ID
            session_data: Dictionary with fields to update

        Returns:
            Dict: Updated record from Airtable
        """
        # Build update record with field name mapping
        record = {}

        # Convert start time to Day ID if provided
        if 'Start Time' in session_data:
            start_time = session_data['Start Time']
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))

            day_value = date_to_day_id(start_time)

            # Look up actual Airtable record ID for Day
            day_record_id = self.client.get_day_record_id(day_value)

            record['Day'] = [day_record_id]
            record['Start Time'] = format_airtable_datetime(start_time)

        # Add basic fields
        if session_data.get('Activity ID'):
            record['Activity ID'] = str(session_data.get('Activity ID'))
        if session_data.get('Activity Name'):
            record['Name'] = session_data.get('Activity Name')  # Use Activity Name as Name field
        if session_data.get('Activity Type'):
            record['Activity Type'] = session_data.get('Activity Type')

        # Set source to Garmin
        record['Source'] = 'Garmin'

        # Add optional numeric fields (using actual Airtable field names)
        if session_data.get('Duration') is not None:
            record['Duration (min)'] = session_data.get('Duration')

        if session_data.get('Distance') is not None:
            record['Distance (mi)'] = session_data.get('Distance')

        if session_data.get('Calories') is not None:
            record['Calories'] = session_data.get('Calories')

        if session_data.get('Average HR') is not None:
            record['Avg HR'] = session_data.get('Average HR')

        if session_data.get('Max HR') is not None:
            record['Max HR'] = session_data.get('Max HR')

        if session_data.get('Average Pace') is not None:
            record['Avg Pace (min/mi)'] = session_data.get('Average Pace')

        if session_data.get('Elevation Gain') is not None:
            record['Elevation Gain (ft)'] = session_data.get('Elevation Gain')

        if session_data.get('Garmin URL'):
            record['Garmin URL'] = session_data.get('Garmin URL')

        # Add detailed metrics from activity summary
        if session_data.get('Aerobic Training Effect') is not None:
            record['Aerobic Training Effect'] = session_data.get('Aerobic Training Effect')
            # Also populate old Training Effect field with aerobic TE for backward compatibility
            record['Training Effect'] = session_data.get('Aerobic Training Effect')
        elif session_data.get('Training Effect') is not None:
            # Fallback to old Training Effect field if provided
            record['Training Effect'] = session_data.get('Training Effect')
        if session_data.get('Anaerobic Training Effect') is not None:
            record['Anaerobic Training Effect'] = session_data.get('Anaerobic Training Effect')
        if session_data.get('Activity Training Load') is not None:
            record['Activity Training Load'] = session_data.get('Activity Training Load')
        if session_data.get('Avg Grade Adjusted Speed') is not None:
            record['Avg Grade Adjusted Speed (mph)'] = session_data.get('Avg Grade Adjusted Speed')
        if session_data.get('Avg Moving Speed') is not None:
            record['Avg Moving Speed (mph)'] = session_data.get('Avg Moving Speed')
        if session_data.get('Avg Temperature') is not None:
            record['Avg Temperature (F)'] = session_data.get('Avg Temperature')
        if session_data.get('Body Battery Change') is not None:
            record['Body Battery Change'] = session_data.get('Body Battery Change')
        if session_data.get('Moving Duration') is not None:
            record['Moving Duration (min)'] = session_data.get('Moving Duration')

        if session_data.get('Notes'):
            record['Notes'] = session_data.get('Notes')

        logger.info(f"Updating session {record_id}")
        updated = self.table.update(record_id, record)
        return updated

    def get_session_by_activity_id(self, activity_id: str) -> Optional[Dict]:
        """
        Find a session by its Garmin Activity ID.

        Args:
            activity_id: Garmin activity ID

        Returns:
            Dict or None: Session record if found, None otherwise
        """
        formula = f"{{Activity ID}} = '{activity_id}'"
        records = self.table.all(formula=formula)

        if records:
            return records[0]
        return None

    def sync_session(self, session_data: Dict) -> Dict:
        """
        Sync a session to Airtable (create or update).

        Args:
            session_data: Session data dictionary

        Returns:
            Dict: Synced session record
        """
        activity_id = str(session_data.get('Activity ID'))
        if not activity_id:
            raise ValueError("Activity ID is required for syncing")

        existing = self.get_session_by_activity_id(activity_id)

        if existing:
            record_id = existing['id']
            return self.update_session(record_id, session_data)
        else:
            return self.create_session(session_data)

    def get_sessions_by_week(self, week_id: str) -> List[Dict]:
        """
        Get all sessions for a specific week.

        Args:
            week_id: Week ID in W-YY format (e.g., "2-26")

        Returns:
            List[Dict]: List of session records
        """
        formula = f"SEARCH('{week_id}', {{Week}})"
        records = self.table.all(formula=formula)
        return records


class AirtableHealthMetricsSync:
    """Sync daily health metrics to Airtable."""

    def __init__(self, client: AirtableClient = None):
        """
        Initialize health metrics sync.

        Args:
            client: AirtableClient instance (creates new if not provided)
        """
        self.client = client or AirtableClient()
        self.table = self.client.get_health_metrics_table()

    def create_or_update_metrics(self, metrics_data: Dict) -> Dict:
        """
        Create or update health metrics for a specific day.

        Since Health Metrics uses Day as the primary field,
        there should only be one record per day.

        Args:
            metrics_data: Dictionary with health metrics

        Returns:
            Dict: Created or updated record

        Example metrics_data:
        {
            'Date': datetime(2026, 1, 17),
            'Resting HR': 58,
            'HRV': 65,
            'Sleep Duration': 28800,  # seconds (8 hours)
            'Deep Sleep': 7200,
            'REM Sleep': 5400,
            'Light Sleep': 14400,
            'Awake Time': 1800,
            'Sleep Score': 85,
            'Steps': 12500,
            'Floors Climbed': 15,
            'Active Calories': 650,
            'Total Calories': 2400,
            'Intensity Minutes': 45,
            'Moderate Intensity Minutes': 30,
            'Vigorous Intensity Minutes': 15,
            'Stress Level': 35,
            'Max Stress': 75,
            'Body Battery': 80
        }
        """
        # Convert date to Day ID
        date = metrics_data.get('Date')
        if isinstance(date, str):
            date = datetime.fromisoformat(date.replace('Z', '+00:00'))

        day_value = date_to_day_id(date)

        # Look up actual Airtable record ID for Day
        day_record_id = self.client.get_day_record_id(day_value)

        # Check if record already exists for this day
        existing = self.get_metrics_by_day(day_value)

        # Build record - use date as Name field
        record = {
            'Name': day_value,  # Use ISO date format as Name
            'Day': [day_record_id]
        }

        # Add all optional metrics (excluding HRV, Deep Sleep, REM Sleep, Light Sleep)
        for field in [
            'Resting HR',
            'Sleep Duration',
            'Awake Time',
            'Sleep Score',
            'Steps',
            'Floors Climbed',
            'Active Calories',
            'Total Calories',
            'Intensity Minutes',
            'Moderate Intensity Minutes',
            'Vigorous Intensity Minutes',
            'Stress Level',
            'Max Stress',
            'Body Battery',
        ]:
            if metrics_data.get(field) is not None:
                record[field] = metrics_data.get(field)

        if metrics_data.get('Notes'):
            record['Notes'] = metrics_data.get('Notes')

        if existing:
            logger.info(f"Updating health metrics for {day_value}")
            updated = self.table.update(existing['id'], record)
            return updated
        else:
            logger.info(f"Creating health metrics for {day_value}")
            created = self.table.create(record)
            return created

    def get_metrics_by_day(self, day_value: str) -> Optional[Dict]:
        """
        Get health metrics for a specific day.

        Args:
            day_value: Day value in ISO format (e.g., "2026-01-17")

        Returns:
            Dict or None: Metrics record if found
        """
        # Name field is a date type, so we need to use DATESTR to compare
        # DATESTR converts the date to ISO format (YYYY-MM-DD) for comparison
        formula = f"DATESTR({{Name}}) = '{day_value}'"
        records = self.table.all(formula=formula, max_records=1)

        if records:
            return records[0]

        return None


class AirtableBodyMetricsSync:
    """Sync body metrics (weight, composition) to Airtable."""

    def __init__(self, client: AirtableClient = None):
        """
        Initialize body metrics sync.

        Args:
            client: AirtableClient instance (creates new if not provided)
        """
        self.client = client or AirtableClient()
        self.table = self.client.get_body_metrics_table()

    def create_measurement(self, measurement_data: Dict) -> Dict:
        """
        Create a body measurement in Airtable.

        Args:
            measurement_data: Dictionary with measurement data

        Returns:
            Dict: Created record

        Example measurement_data:
        {
            'Date': datetime(2026, 1, 17),
            'Time': datetime(2026, 1, 17, 7, 30),
            'Weight': 175.5,
            'BMI': 23.5,
            'Body Fat %': 15.2,
            'Muscle Mass': 145.3,
            'Bone Mass': 8.2,
            'Body Water %': 58.5
        }
        """
        # Convert date to Day ID
        date = measurement_data.get('Date')
        if isinstance(date, str):
            date = datetime.fromisoformat(date.replace('Z', '+00:00'))

        day_value = date_to_day_id(date)

        # Look up actual Airtable record ID for Day
        day_record_id = self.client.get_day_record_id(day_value)

        # Build record
        record = {
            'Day': [day_record_id],
            'Date': format_airtable_datetime(date),
        }

        # Add timestamp if provided
        if measurement_data.get('Time'):
            time = measurement_data.get('Time')
            if isinstance(time, str):
                time = datetime.fromisoformat(time.replace('Z', '+00:00'))
            record['Time'] = format_airtable_datetime(time)

        # Add measurements
        for field in ['Weight', 'BMI', 'Body Fat %', 'Muscle Mass', 'Bone Mass', 'Body Water %']:
            if measurement_data.get(field) is not None:
                record[field] = measurement_data.get(field)

        if measurement_data.get('Notes'):
            record['Notes'] = measurement_data.get('Notes')

        logger.info(f"Creating body measurement for {day_value}")
        created = self.table.create(record)
        return created
