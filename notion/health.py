"""
Notion Health data sync operations.

This module handles syncing Garmin health data to Notion:
- Garmin Activities (workouts/activities)
- Daily Tracking (daily health data + body metrics combined)
"""

from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import logging
import requests

from core.config import Config

logger = logging.getLogger(__name__)

# Notion API base URL
NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class NotionHealthSync:
    """Base class for Notion health sync with shared functionality."""

    def __init__(self, token: str = None):
        """
        Initialize Notion health sync.

        Args:
            token: Notion API token (uses Config.NOTION_TOKEN if not provided)
        """
        self.token = token or Config.NOTION_TOKEN
        if not self.token:
            raise ValueError("Notion token is required. Set NOTION_TOKEN in .env")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the Notion API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body data

        Returns:
            Response JSON data
        """
        url = f"{NOTION_API_URL}{endpoint}"

        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            json=data,
        )

        if not response.ok:
            logger.error(f"Notion API error: {response.status_code} - {response.text}")
            response.raise_for_status()

        return response.json()

    def _format_datetime_for_notion(self, dt: datetime) -> str:
        """Format datetime for Notion API (ISO 8601)."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    def _format_date_for_notion(self, dt: datetime) -> str:
        """Format date only (no time) for Notion API."""
        return dt.strftime('%Y-%m-%d')


class NotionActivitiesSync(NotionHealthSync):
    """Sync Garmin activities to Notion Garmin Activities database."""

    def __init__(self, token: str = None):
        """
        Initialize activities sync.

        Args:
            token: Notion API token
        """
        super().__init__(token)
        self.database_id = Config.NOTION_WORKOUTS_DB_ID
        if not self.database_id:
            raise ValueError("NOTION_WORKOUTS_DB_ID not set in config")

    def get_activity_by_external_id(self, external_id: str) -> Optional[Dict]:
        """
        Find an activity by its External ID.

        Args:
            external_id: External activity ID (Garmin activity ID)

        Returns:
            Page data if found, None otherwise
        """
        try:
            response = self._make_request(
                "POST",
                f"/databases/{self.database_id}/query",
                {
                    "filter": {
                        "property": "External ID",
                        "rich_text": {
                            "equals": external_id
                        }
                    },
                    "page_size": 1
                }
            )

            results = response.get("results", [])
            if results:
                return results[0]

        except Exception as e:
            logger.error(f"Error finding activity by external ID: {e}")

        return None

    def create_activity(self, activity_data: Dict) -> Dict:
        """
        Create an activity in Notion.

        Args:
            activity_data: Dictionary with activity fields from Garmin

        Returns:
            Created page data from Notion
        """
        # Map activity type from Garmin format to Notion select options
        activity_type_mapping = {
            'Running': 'Run',
            'Cycling': 'Bike',
            'Swimming': 'Swim',
            'Walking': 'Walk',
            'Strength': 'Strength',
            'Hiking': 'Walk',
            'Other': 'Other',
        }

        activity_type = activity_data.get('activity_type', 'Other')
        notion_activity_type = activity_type_mapping.get(activity_type, 'Other')

        # Build properties
        properties = {
            "Name": {
                "title": [{"text": {"content": activity_data.get('title', 'Workout')}}]
            },
            "External ID": {
                "rich_text": [{"text": {"content": str(activity_data.get('external_id', ''))}}]
            },
            "Activity Type": {
                "select": {"name": notion_activity_type}
            },
            "Synced At": {
                "date": {"start": self._format_datetime_for_notion(datetime.now(timezone.utc))}
            }
        }

        # Add date
        start_time = activity_data.get('start_time')
        if start_time:
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            properties["Date"] = {
                "date": {"start": self._format_datetime_for_notion(start_time)}
            }

        # Add numeric fields
        if activity_data.get('duration_minutes') is not None:
            properties["Duration"] = {"number": round(activity_data['duration_minutes'], 1)}

        if activity_data.get('distance') is not None:
            properties["Distance"] = {"number": round(activity_data['distance'], 2)}

        if activity_data.get('calories') is not None:
            properties["Calories"] = {"number": activity_data['calories']}

        if activity_data.get('avg_heart_rate') is not None:
            properties["Avg Heart Rate"] = {"number": activity_data['avg_heart_rate']}

        if activity_data.get('max_heart_rate') is not None:
            properties["Max Heart Rate"] = {"number": activity_data['max_heart_rate']}

        if activity_data.get('elevation') is not None:
            properties["Elevation Gain"] = {"number": round(activity_data['elevation'], 0)}

        if activity_data.get('pace') is not None:
            properties["Avg Pace"] = {"rich_text": [{"text": {"content": str(activity_data['pace'])}}]}

        if activity_data.get('speed') is not None:
            properties["Avg Speed"] = {"number": activity_data['speed']}

        if activity_data.get('garmin_url'):
            properties["Garmin URL"] = {"url": activity_data['garmin_url']}

        # Create the page
        page_data = {
            "parent": {"database_id": self.database_id},
            "properties": properties
        }

        logger.info(f"Creating activity '{activity_data.get('title')}'")

        try:
            result = self._make_request("POST", "/pages", page_data)
            return result
        except Exception as e:
            logger.error(f"Error creating activity: {e}")
            raise

    def update_activity(self, page_id: str, activity_data: Dict) -> Dict:
        """
        Update an existing activity in Notion.

        Args:
            page_id: Notion page ID
            activity_data: Dictionary with fields to update

        Returns:
            Updated page data from Notion
        """
        # Map activity type
        activity_type_mapping = {
            'Running': 'Run',
            'Cycling': 'Bike',
            'Swimming': 'Swim',
            'Walking': 'Walk',
            'Strength': 'Strength',
            'Hiking': 'Walk',
            'Other': 'Other',
        }

        properties = {}

        if 'title' in activity_data:
            properties["Name"] = {
                "title": [{"text": {"content": activity_data['title']}}]
            }

        if 'activity_type' in activity_data:
            notion_type = activity_type_mapping.get(activity_data['activity_type'], 'Other')
            properties["Activity Type"] = {"select": {"name": notion_type}}

        if 'start_time' in activity_data:
            start_time = activity_data['start_time']
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            properties["Date"] = {
                "date": {"start": self._format_datetime_for_notion(start_time)}
            }

        if activity_data.get('duration_minutes') is not None:
            properties["Duration"] = {"number": round(activity_data['duration_minutes'], 1)}

        if activity_data.get('distance') is not None:
            properties["Distance"] = {"number": round(activity_data['distance'], 2)}

        if activity_data.get('calories') is not None:
            properties["Calories"] = {"number": activity_data['calories']}

        if activity_data.get('avg_heart_rate') is not None:
            properties["Avg Heart Rate"] = {"number": activity_data['avg_heart_rate']}

        if activity_data.get('max_heart_rate') is not None:
            properties["Max Heart Rate"] = {"number": activity_data['max_heart_rate']}

        if activity_data.get('elevation') is not None:
            properties["Elevation Gain"] = {"number": round(activity_data['elevation'], 0)}

        if activity_data.get('pace') is not None:
            properties["Avg Pace"] = {"rich_text": [{"text": {"content": str(activity_data['pace'])}}]}

        if activity_data.get('speed') is not None:
            properties["Avg Speed"] = {"number": activity_data['speed']}

        if activity_data.get('garmin_url'):
            properties["Garmin URL"] = {"url": activity_data['garmin_url']}

        # Update sync timestamp
        properties["Synced At"] = {
            "date": {"start": self._format_datetime_for_notion(datetime.now(timezone.utc))}
        }

        logger.info(f"Updating activity {page_id}")

        try:
            result = self._make_request("PATCH", f"/pages/{page_id}", {"properties": properties})
            return result
        except Exception as e:
            logger.error(f"Error updating activity: {e}")
            raise

    def sync_activity(self, activity_data: Dict) -> Dict:
        """
        Sync an activity to Notion (create or update).

        Args:
            activity_data: Activity data dictionary

        Returns:
            Synced activity page data
        """
        external_id = str(activity_data.get('external_id', ''))
        if not external_id:
            raise ValueError("External ID is required for syncing")

        existing = self.get_activity_by_external_id(external_id)

        if existing:
            page_id = existing['id']
            return self.update_activity(page_id, activity_data)
        else:
            return self.create_activity(activity_data)


class NotionDailyTrackingSync(NotionHealthSync):
    """
    Sync daily metrics and body metrics to Notion Daily Tracking database.

    This database combines daily health metrics and body composition data
    into a single record per day.
    """

    def __init__(self, token: str = None):
        """
        Initialize daily tracking sync.

        Args:
            token: Notion API token
        """
        super().__init__(token)
        self.database_id = Config.NOTION_DAILY_TRACKING_DB_ID
        if not self.database_id:
            raise ValueError("NOTION_DAILY_TRACKING_DB_ID not set in config")

    def get_tracking_by_date(self, date_str: str) -> Optional[Dict]:
        """
        Find a daily tracking record by date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Page data if found, None otherwise
        """
        try:
            response = self._make_request(
                "POST",
                f"/databases/{self.database_id}/query",
                {
                    "filter": {
                        "property": "Date",
                        "date": {
                            "equals": date_str
                        }
                    },
                    "page_size": 1
                }
            )

            results = response.get("results", [])
            if results:
                return results[0]

        except Exception as e:
            logger.error(f"Error finding tracking record for {date_str}: {e}")

        return None

    def create_or_update_tracking(self, tracking_data: Dict) -> Dict:
        """
        Create or update daily tracking record.

        Combines daily health metrics and body metrics into a single record.

        Args:
            tracking_data: Dictionary with tracking fields

        Returns:
            Created or updated page data
        """
        date = tracking_data.get('date')
        if isinstance(date, datetime):
            date_str = date.strftime('%Y-%m-%d')
        else:
            date_str = date

        # Check if record already exists
        existing = self.get_tracking_by_date(date_str)

        # Build properties
        properties = {
            "Name": {
                "title": [{"text": {"content": date_str}}]
            },
            "Date": {
                "date": {"start": date_str}
            }
        }

        # Daily health metrics
        if tracking_data.get('steps') is not None:
            properties["Steps"] = {"number": tracking_data['steps']}

        if tracking_data.get('floors_climbed') is not None:
            properties["Floors Climbed"] = {"number": tracking_data['floors_climbed']}

        if tracking_data.get('active_calories') is not None:
            properties["Active Calories"] = {"number": tracking_data['active_calories']}

        if tracking_data.get('total_calories') is not None:
            properties["Total Calories"] = {"number": tracking_data['total_calories']}

        if tracking_data.get('avg_hr') is not None:
            properties["Resting HR"] = {"number": tracking_data['avg_hr']}

        if tracking_data.get('sleep_hours') is not None:
            properties["Sleep Duration (Hrs)"] = {"number": round(tracking_data['sleep_hours'], 1)}

        if tracking_data.get('sleep_score') is not None:
            properties["Sleep Score"] = {"number": tracking_data['sleep_score']}

        if tracking_data.get('avg_stress') is not None:
            properties["Stress Level"] = {"number": tracking_data['avg_stress']}

        if tracking_data.get('body_battery_max') is not None:
            properties["Body Battery"] = {"number": tracking_data['body_battery_max']}

        if tracking_data.get('moderate_intensity_minutes') is not None:
            properties["Moderate Intensity Minutes"] = {"number": tracking_data['moderate_intensity_minutes']}

        if tracking_data.get('vigorous_intensity_minutes') is not None:
            properties["Vigorous Intensity Minutes"] = {"number": tracking_data['vigorous_intensity_minutes']}

        # Calculate total intensity minutes
        moderate = tracking_data.get('moderate_intensity_minutes') or 0
        vigorous = tracking_data.get('vigorous_intensity_minutes') or 0
        if moderate or vigorous:
            properties["Intensity Minutes"] = {"number": moderate + vigorous}

        # Body metrics
        if tracking_data.get('weight') is not None:
            properties["Weight (lbs)"] = {"number": round(tracking_data['weight'], 1)}

        if tracking_data.get('body_fat_percent') is not None:
            properties["Body Fat %"] = {"number": round(tracking_data['body_fat_percent'], 1)}

        if tracking_data.get('muscle_mass') is not None:
            properties["Muscle Mass (lbs)"] = {"number": round(tracking_data['muscle_mass'], 1)}

        if tracking_data.get('body_water_percent') is not None:
            properties["Water %"] = {"number": round(tracking_data['body_water_percent'], 1)}

        if existing:
            logger.info(f"Updating daily tracking for {date_str}")
            try:
                result = self._make_request("PATCH", f"/pages/{existing['id']}", {"properties": properties})
                return result
            except Exception as e:
                logger.error(f"Error updating tracking: {e}")
                raise
        else:
            logger.info(f"Creating daily tracking for {date_str}")
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": properties
            }
            try:
                result = self._make_request("POST", "/pages", page_data)
                return result
            except Exception as e:
                logger.error(f"Error creating tracking: {e}")
                raise

    def sync_daily_metrics(self, metrics_data: Dict) -> Dict:
        """
        Sync daily health metrics to Notion.

        Args:
            metrics_data: Daily metrics data dictionary

        Returns:
            Synced page data
        """
        return self.create_or_update_tracking(metrics_data)

    def sync_body_metrics(self, body_data: Dict) -> Dict:
        """
        Sync body composition metrics to Notion.

        Args:
            body_data: Body metrics data dictionary

        Returns:
            Synced page data
        """
        return self.create_or_update_tracking(body_data)
