"""
Notion API client for syncing health and training data.
Creates and updates pages in Workouts, Daily Metrics, and Body Metrics databases.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from notion_client import Client
from notion_client.errors import APIResponseError

from core.config import GarminConfig as Config
from core.state_manager import StateManager
from core.utils import setup_logging, RateLimiter, retry_with_backoff, rate_limit

logger = setup_logging("notion_health")


class NotionSync:
    """Client for syncing data to Notion databases."""

    def __init__(self, state_manager: Optional[StateManager] = None):
        """
        Initialize Notion client.

        Args:
            state_manager: State manager instance (creates new if None)
        """
        self.client = Client(auth=Config.NOTION_TOKEN)
        self.state_manager = state_manager or StateManager()

        self.workouts_db_id = Config.NOTION_WORKOUTS_DB_ID
        self.daily_metrics_db_id = Config.NOTION_DAILY_METRICS_DB_ID
        self.body_metrics_db_id = Config.NOTION_BODY_METRICS_DB_ID

    @rate_limit(calls_per_second=3.0)
    def create_workout(self, workout_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a workout page in Notion.

        Args:
            workout_data: Normalized workout data from Garmin

        Returns:
            Notion page ID if successful, None otherwise
        """
        try:
            external_id = workout_data.get("external_id")

            # Check if already exists
            existing_page_id = self.state_manager.get_notion_page_id(external_id)
            if existing_page_id:
                logger.debug(f"Workout {external_id} already exists, updating...")
                return self.update_workout(existing_page_id, workout_data)

            # Build properties
            properties = self._build_workout_properties(workout_data)

            # Create page
            response = self.client.pages.create(parent={"database_id": self.workouts_db_id}, properties=properties)

            page_id = response["id"]
            self.state_manager.save_mapping(external_id, page_id, "workout", "garmin")

            logger.info(f"✓ Created workout: {workout_data.get('title')}")
            return page_id

        except Exception as e:
            logger.error(f"✗ Error creating workout: {e}")
            return None

    @rate_limit(calls_per_second=3.0)
    def update_workout(self, page_id: str, workout_data: Dict[str, Any]) -> Optional[str]:
        """
        Update an existing workout page in Notion.

        Args:
            page_id: Notion page ID
            workout_data: Updated workout data

        Returns:
            Notion page ID if successful, None otherwise
        """
        try:
            properties = self._build_workout_properties(workout_data)

            self.client.pages.update(page_id=page_id, properties=properties)

            logger.debug(f"✓ Updated workout: {workout_data.get('title')}")
            return page_id

        except Exception as e:
            logger.error(f"✗ Error updating workout {page_id}: {e}")
            return None

    def _build_workout_properties(self, workout_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build Notion properties for a workout."""
        properties = {
            "Name": {"title": [{"text": {"content": workout_data.get("title", "Workout")}}]},
            "External ID": {"rich_text": [{"text": {"content": workout_data.get("external_id", "")}}]},
            "Synced At": {"date": {"start": datetime.now().isoformat()}},
        }

        # Date
        if workout_data.get("start_time"):
            properties["Date"] = {"date": {"start": workout_data["start_time"].isoformat()}}

        # Activity Type
        activity_type = workout_data.get("activity_type", "OTHER")
        properties["Activity Type"] = {"select": {"name": self._map_activity_type(activity_type)}}

        # Duration
        if workout_data.get("duration_minutes"):
            properties["Duration"] = {"number": workout_data["duration_minutes"]}

        # Distance
        if workout_data.get("distance"):
            dist = workout_data["distance"]
            unit = workout_data.get("distance_unit", "mi")
            properties["Distance"] = {"number": dist}

        # Elevation
        if workout_data.get("elevation"):
            properties["Elevation Gain"] = {"number": workout_data["elevation"]}

        # Heart Rate
        if workout_data.get("avg_heart_rate"):
            properties["Avg Heart Rate"] = {"number": workout_data["avg_heart_rate"]}
        if workout_data.get("max_heart_rate"):
            properties["Max Heart Rate"] = {"number": workout_data["max_heart_rate"]}

        # Calories
        if workout_data.get("calories"):
            properties["Calories"] = {"number": workout_data["calories"]}

        # Pace
        if workout_data.get("pace"):
            properties["Avg Pace"] = {"rich_text": [{"text": {"content": workout_data["pace"]}}]}

        # Speed
        if workout_data.get("speed"):
            properties["Avg Speed"] = {"number": workout_data["speed"]}

        # Garmin URL
        if workout_data.get("garmin_url"):
            properties["Garmin URL"] = {"url": workout_data["garmin_url"]}

        return properties

    def _map_activity_type(self, garmin_type) -> str:
        """Map Garmin activity type to Notion select option."""
        # Extract type_key from ActivityType object if it has one
        if hasattr(garmin_type, 'type_key'):
            type_key = garmin_type.type_key.upper()
        else:
            type_key = str(garmin_type).upper()

        mapping = {
            "RUNNING": "Run",
            "TRAIL_RUNNING": "Run",
            "CYCLING": "Ride",
            "ROAD_BIKING": "Ride",
            "MOUNTAIN_BIKING": "Ride",
            "VIRTUAL_RIDE": "Ride",
            "INDOOR_CYCLING": "Ride",
            "SWIMMING": "Swim",
            "LAP_SWIMMING": "Swim",
            "OPEN_WATER_SWIMMING": "Swim",
            "STRENGTH_TRAINING": "Strength",
            "CARDIO_TRAINING": "Strength",
            "WALKING": "Walk",
            "HIKING": "Walk",
            "YOGA": "Other",
        }
        return mapping.get(type_key, "Other")

    @rate_limit(calls_per_second=3.0)
    def create_daily_metric(self, metric_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a daily metrics page in Notion.

        Args:
            metric_data: Normalized daily metrics from Garmin

        Returns:
            Notion page ID if successful, None otherwise
        """
        try:
            external_id = metric_data.get("external_id")

            # Check if already exists
            existing_page_id = self.state_manager.get_notion_page_id(external_id)
            if existing_page_id:
                logger.debug(f"Daily metric {external_id} already exists, updating...")
                return self.update_daily_metric(existing_page_id, metric_data)

            # Build properties
            properties = self._build_daily_metric_properties(metric_data)

            # Create page
            response = self.client.pages.create(
                parent={"database_id": self.daily_metrics_db_id}, properties=properties
            )

            page_id = response["id"]
            self.state_manager.save_mapping(external_id, page_id, "daily_metric", "garmin")

            logger.info(f"✓ Created daily metric: {metric_data.get('date')}")
            return page_id

        except Exception as e:
            logger.error(f"✗ Error creating daily metric: {e}")
            return None

    @rate_limit(calls_per_second=3.0)
    def update_daily_metric(self, page_id: str, metric_data: Dict[str, Any]) -> Optional[str]:
        """Update an existing daily metrics page."""
        try:
            properties = self._build_daily_metric_properties(metric_data)
            self.client.pages.update(page_id=page_id, properties=properties)
            logger.debug(f"✓ Updated daily metric: {metric_data.get('date')}")
            return page_id
        except Exception as e:
            logger.error(f"✗ Error updating daily metric {page_id}: {e}")
            return None

    def _build_daily_metric_properties(self, metric_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build Notion properties for daily metrics."""
        date_str = metric_data.get("date", "")

        properties = {
            "Name": {"title": [{"text": {"content": date_str}}]},
            "External ID": {"rich_text": [{"text": {"content": metric_data.get("external_id", "")}}]},
            "Synced At": {"date": {"start": datetime.now().isoformat()}},
        }

        # Add the Date property separately
        if date_str:
            properties["Date"] = {"date": {"start": date_str}}

        # Steps
        if metric_data.get("steps"):
            properties["Steps"] = {"number": metric_data["steps"]}

        # Distance
        if metric_data.get("distance"):
            properties["Distance"] = {"number": metric_data["distance"]}

        # Calories
        if metric_data.get("active_calories"):
            properties["Calories Active"] = {"number": metric_data["active_calories"]}
        if metric_data.get("total_calories"):
            properties["Calories Total"] = {"number": metric_data["total_calories"]}

        # Floors
        if metric_data.get("floors_climbed"):
            properties["Floors Climbed"] = {"number": metric_data["floors_climbed"]}

        # Heart Rate
        if metric_data.get("avg_hr"):
            properties["Avg Heart Rate"] = {"number": metric_data["avg_hr"]}
        if metric_data.get("min_hr"):
            properties["Min Heart Rate"] = {"number": metric_data["min_hr"]}
        if metric_data.get("max_hr"):
            properties["Max Heart Rate"] = {"number": metric_data["max_hr"]}

        # Stress
        if metric_data.get("avg_stress"):
            properties["Stress Avg"] = {"number": metric_data["avg_stress"]}

        # Body Battery
        if metric_data.get("body_battery_max"):
            properties["Body Battery Max"] = {"number": metric_data["body_battery_max"]}

        # Sleep
        if metric_data.get("sleep_hours"):
            properties["Sleep Duration"] = {"number": metric_data["sleep_hours"]}
        if metric_data.get("sleep_score"):
            properties["Sleep Score"] = {"number": metric_data["sleep_score"]}

        # Intensity Minutes
        if metric_data.get("moderate_intensity_minutes") is not None:
            properties["Moderate Intensity Minutes"] = {"number": metric_data["moderate_intensity_minutes"]}
        if metric_data.get("vigorous_intensity_minutes") is not None:
            properties["Vigorous Intensity Minutes"] = {"number": metric_data["vigorous_intensity_minutes"]}

        # VO2 Max
        if metric_data.get("vo2_max"):
            properties["VO2 Max"] = {"number": metric_data["vo2_max"]}

        return properties

    @rate_limit(calls_per_second=3.0)
    def create_body_metric(self, body_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a body metrics page in Notion.

        Args:
            body_data: Normalized body composition data

        Returns:
            Notion page ID if successful, None otherwise
        """
        try:
            external_id = body_data.get("external_id")

            # Check if already exists
            existing_page_id = self.state_manager.get_notion_page_id(external_id)
            if existing_page_id:
                logger.debug(f"Body metric {external_id} already exists, updating...")
                return self.update_body_metric(existing_page_id, body_data)

            # Build properties
            properties = self._build_body_metric_properties(body_data)

            # Create page
            response = self.client.pages.create(
                parent={"database_id": self.body_metrics_db_id}, properties=properties
            )

            page_id = response["id"]
            self.state_manager.save_mapping(external_id, page_id, "body_metric", "garmin")

            logger.info(f"✓ Created body metric: {body_data.get('date')}")
            return page_id

        except Exception as e:
            logger.error(f"✗ Error creating body metric: {e}")
            return None

    @rate_limit(calls_per_second=3.0)
    def update_body_metric(self, page_id: str, body_data: Dict[str, Any]) -> Optional[str]:
        """Update an existing body metrics page."""
        try:
            properties = self._build_body_metric_properties(body_data)
            self.client.pages.update(page_id=page_id, properties=properties)
            logger.debug(f"✓ Updated body metric: {body_data.get('date')}")
            return page_id
        except Exception as e:
            logger.error(f"✗ Error updating body metric {page_id}: {e}")
            return None

    def _build_body_metric_properties(self, body_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build Notion properties for body metrics."""
        date_str = body_data.get("date", "")

        properties = {
            "Name": {"title": [{"text": {"content": date_str}}]},
            "External ID": {"rich_text": [{"text": {"content": body_data.get("external_id", "")}}]},
            "Synced At": {"date": {"start": datetime.now().isoformat()}},
        }

        # Add the Date property separately
        if date_str:
            properties["Date"] = {"date": {"start": date_str}}

        # Weight
        if body_data.get("weight"):
            properties["Weight"] = {"number": body_data["weight"]}

        # BMI
        if body_data.get("bmi"):
            properties["BMI"] = {"number": body_data["bmi"]}

        # Body Fat
        if body_data.get("body_fat_percent"):
            properties["Body Fat %"] = {"number": body_data["body_fat_percent"]}

        # Muscle Mass
        if body_data.get("muscle_mass"):
            properties["Muscle Mass"] = {"number": body_data["muscle_mass"]}

        # Bone Mass
        if body_data.get("bone_mass"):
            properties["Bone Mass"] = {"number": body_data["bone_mass"]}

        # Body Water
        if body_data.get("body_water_percent"):
            properties["Body Water %"] = {"number": body_data["body_water_percent"]}

        return properties
