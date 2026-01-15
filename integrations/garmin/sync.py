"""
Garmin Connect API client for syncing health and training data.
Uses the garth library for authentication and data retrieval.
"""

from datetime import datetime, timedelta, date
from pathlib import Path
from typing import List, Dict, Any, Optional
import garth
from garth import Activity, DailySteps, DailySleep, DailyStress, WeightData, DailyHRV

from core.config import GarminConfig as Config
from core.utils import (
    setup_logging,
    retry_api_call,
    convert_meters_to_miles,
    convert_meters_to_feet,
    convert_kg_to_lbs,
    convert_pace_to_imperial,
)

logger = setup_logging("garmin_sync")


class GarminSync:
    """Client for syncing data from Garmin Connect."""

    def __init__(self):
        """Initialize Garmin Connect client."""
        self.email = Config.GARMIN_EMAIL
        self.password = Config.GARMIN_PASSWORD
        self.unit_system = Config.UNIT_SYSTEM
        self.tokens_dir = Path(__file__).parent.parent / "credentials"
        self.tokens_dir.mkdir(exist_ok=True)
        self.client = None
        self._authenticated = False

    def authenticate(self) -> bool:
        """
        Authenticate with Garmin Connect.
        Uses cached tokens if available, otherwise performs fresh login.

        Returns:
            bool: True if authentication successful
        """
        try:
            # Try to load existing tokens
            token_path = self.tokens_dir / "garmin_tokens"
            if token_path.exists():
                logger.info("Loading cached Garmin tokens...")
                garth.resume(str(self.tokens_dir))
                garth.client.username = self.email
                self._authenticated = True
                logger.info("✓ Successfully loaded Garmin tokens")
                return True
        except Exception as e:
            logger.warning(f"Could not load cached tokens: {e}")

        # Fresh login
        try:
            logger.info(f"Authenticating with Garmin Connect as {self.email}...")
            garth.login(self.email, self.password)
            garth.save(str(self.tokens_dir))
            self._authenticated = True
            logger.info("✓ Successfully authenticated with Garmin Connect")
            return True
        except Exception as e:
            logger.error(f"✗ Garmin authentication failed: {e}")
            return False

    @retry_api_call
    def get_activities(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch activities from Garmin Connect.

        Args:
            start_date: Start date for activity fetch (default: SYNC_LOOKBACK_DAYS ago)
            end_date: End date for activity fetch (default: now)

        Returns:
            List of activity dictionaries with normalized data
        """
        if not self._authenticated:
            if not self.authenticate():
                return []

        # Default date range
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=Config.SYNC_LOOKBACK_DAYS)

        try:
            logger.info(f"Fetching activities from {start_date.date()} to {end_date.date()}...")

            # Fetch recent activities (activities are returned newest first)
            # For 90 days of activities, fetch in batches until we hit the start_date
            all_activities = []
            offset = 0
            batch_size = 20

            while offset < 200:  # Safety limit (covers ~200 activities)
                activities = Activity.list(limit=batch_size, start=offset)
                if not activities:
                    break

                # Filter by date range (activities are sorted newest first)
                found_old_activity = False
                for activity in activities:
                    # activity.start_time_local is already a datetime object
                    activity_date = activity.start_time_local
                    # Make it timezone-aware if it isn't
                    if activity_date.tzinfo is None:
                        activity_date = activity_date.replace(tzinfo=start_date.tzinfo)

                    if start_date <= activity_date <= end_date:
                        all_activities.append(activity)
                    elif activity_date < start_date:
                        # Activities are sorted newest first, so we can stop
                        found_old_activity = True
                        break

                # If we found an activity older than our start date, we're done
                if found_old_activity or len(activities) < batch_size:
                    break

                offset += batch_size

            logger.info(f"Found {len(all_activities)} activities")

            # Normalize activity data
            normalized_activities = []
            for activity in all_activities:
                normalized = self._normalize_activity(activity)
                if normalized:
                    normalized_activities.append(normalized)

            return normalized_activities

        except Exception as e:
            logger.error(f"Error fetching activities: {e}")
            return []

    def _normalize_activity(self, activity: Activity) -> Optional[Dict[str, Any]]:
        """
        Normalize activity data to a consistent format.

        Args:
            activity: Activity object from garth

        Returns:
            Normalized activity dictionary
        """
        try:
            # Extract basic info from activity object (don't fetch summary to avoid rate limits)
            activity_id = str(activity.activity_id) if hasattr(activity, 'activity_id') else ""
            activity_name = activity.activity_name if hasattr(activity, 'activity_name') else "Workout"
            activity_type = activity.activity_type if hasattr(activity, 'activity_type') else "OTHER"

            # Date/time (start_time_local is already a datetime object)
            start_time = activity.start_time_local

            # Duration (seconds)
            duration_seconds = activity.duration or 0
            duration_minutes = duration_seconds / 60 if duration_seconds else 0

            # Distance (convert based on unit system)
            distance_meters = activity.distance or 0
            if self.unit_system == "imperial":
                distance = convert_meters_to_miles(distance_meters)
                distance_unit = "mi"
            else:
                distance = distance_meters / 1000  # km
                distance_unit = "km"

            # Elevation (convert based on unit system)
            elevation_meters = activity.elevation_gain or 0
            if self.unit_system == "imperial":
                elevation = convert_meters_to_feet(elevation_meters)
                elevation_unit = "ft"
            else:
                elevation = elevation_meters
                elevation_unit = "m"

            # Heart rate
            avg_hr = activity.average_hr
            max_hr = activity.max_hr

            # Calories
            calories = activity.calories

            # Pace/speed
            avg_speed_mps = activity.average_speed  # meters per second
            pace = None
            if avg_speed_mps and avg_speed_mps > 0:
                if self.unit_system == "imperial":
                    pace = convert_pace_to_imperial(avg_speed_mps)
                else:
                    # Convert to min/km
                    km_per_second = avg_speed_mps / 1000
                    seconds_per_km = 1 / km_per_second if km_per_second > 0 else 0
                    minutes = int(seconds_per_km / 60)
                    seconds = int(seconds_per_km % 60)
                    pace = f"{minutes}:{seconds:02d}"

            # URL
            garmin_url = f"https://connect.garmin.com/modern/activity/{activity_id}"

            return {
                "external_id": activity_id,
                "title": activity_name,
                "activity_type": activity_type,
                "start_time": start_time,
                "duration_minutes": round(duration_minutes, 2),
                "distance": round(distance, 2) if distance else None,
                "distance_unit": distance_unit,
                "elevation": round(elevation, 2) if elevation else None,
                "elevation_unit": elevation_unit,
                "avg_heart_rate": avg_hr,
                "max_heart_rate": max_hr,
                "calories": calories,
                "pace": pace,
                "garmin_url": garmin_url,
                "raw_data": activity,  # Keep raw data for debugging
            }

        except Exception as e:
            logger.error(f"Error normalizing activity {activity.get('activityId')}: {e}")
            return None

    @retry_api_call
    def get_daily_metrics(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch daily health metrics from Garmin Connect.

        Args:
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: today)

        Returns:
            List of daily metrics dictionaries
        """
        if not self._authenticated:
            if not self.authenticate():
                return []

        # Default date range (last 30 days)
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        try:
            logger.info(f"Fetching daily metrics from {start_date.date()} to {end_date.date()}...")

            daily_metrics = []
            current_date = start_date

            # Calculate number of days to fetch
            num_days = (end_date - start_date).days + 1

            # Fetch metrics in bulk using new API
            try:
                steps_list = DailySteps.list(end=end_date.date(), period=num_days)
                sleep_list = DailySleep.list(end=end_date.date(), period=num_days)
                stress_list = DailyStress.list(end=end_date.date(), period=num_days)
                hrv_list = DailyHRV.list(end=end_date.date(), period=num_days)

                # Create dictionaries for quick lookup by date
                steps_by_date = {s.calendar_date: s for s in steps_list}
                sleep_by_date = {s.calendar_date: s for s in sleep_list}
                stress_by_date = {s.calendar_date: s for s in stress_list}
                hrv_by_date = {h.calendar_date: h for h in hrv_list}

                # Iterate through each day and combine metrics
                current_date = start_date
                while current_date <= end_date:
                    date_obj = current_date.date()

                    # Get metrics for this date
                    steps = steps_by_date.get(date_obj)
                    sleep_data = sleep_by_date.get(date_obj)
                    stress_data = stress_by_date.get(date_obj)
                    hrv_data = hrv_by_date.get(date_obj)

                    # Normalize the data
                    try:
                        normalized = self._normalize_daily_metrics(date_obj, steps, sleep_data, stress_data, hrv_data)
                        if normalized:
                            daily_metrics.append(normalized)
                    except Exception as e:
                        logger.warning(f"Could not normalize metrics for {date_obj}: {e}")

                    current_date += timedelta(days=1)

            except Exception as e:
                logger.error(f"Error fetching daily metrics in bulk: {e}")

            logger.info(f"Found {len(daily_metrics)} days of metrics")
            return daily_metrics

        except Exception as e:
            logger.error(f"Error fetching daily metrics: {e}")
            return []

    def _normalize_daily_metrics(
        self, date_obj: date, steps_data, sleep_data, stress_data, hrv_data
    ) -> Optional[Dict[str, Any]]:
        """Normalize daily metrics data from garth objects."""
        try:
            date_str = date_obj.isoformat()
            metrics = {
                "date": date_str,
                "external_id": f"daily_{date_str}",
            }

            # Steps
            if steps_data:
                metrics["steps"] = steps_data.total_steps
                metrics["distance_meters"] = steps_data.total_distance
                # Note: active_calories not available in DailySteps, may need separate query

            # Sleep
            if sleep_data:
                if hasattr(sleep_data, 'sleep_time_seconds'):
                    metrics["sleep_hours"] = round(sleep_data.sleep_time_seconds / 3600, 1)
                elif hasattr(sleep_data, 'total_sleep_seconds'):
                    metrics["sleep_hours"] = round(sleep_data.total_sleep_seconds / 3600, 1)

            # Stress
            if stress_data and hasattr(stress_data, 'avg_stress_level'):
                metrics["avg_stress"] = stress_data.avg_stress_level

            # HRV / Heart Rate
            if hrv_data:
                if hasattr(hrv_data, 'last_night_avg'):
                    metrics["hrv_avg"] = hrv_data.last_night_avg

            return metrics

        except Exception as e:
            logger.error(f"Error normalizing daily metrics for {date_obj}: {e}")
            return None

    @retry_api_call
    def get_body_composition(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch body composition data from Garmin Connect.

        Args:
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: today)

        Returns:
            List of body composition measurements
        """
        if not self._authenticated:
            if not self.authenticate():
                return []

        # Default date range
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        try:
            logger.info(f"Fetching body composition from {start_date.date()} to {end_date.date()}...")

            # Calculate number of days
            num_days = (end_date - start_date).days + 1

            # Fetch weight data using new API
            weight_data_list = WeightData.list(end=end_date.date(), days=num_days)

            measurements = []
            for entry in weight_data_list:
                normalized = self._normalize_body_composition(entry)
                if normalized:
                    measurements.append(normalized)

            logger.info(f"Found {len(measurements)} body composition measurements")
            return measurements

        except Exception as e:
            logger.error(f"Error fetching body composition: {e}")
            return []

    def _normalize_body_composition(self, entry: WeightData) -> Optional[Dict[str, Any]]:
        """Normalize body composition data from garth WeightData object."""
        try:
            # WeightData should have timestamp and weight attributes
            if not hasattr(entry, 'weight') or not entry.weight:
                return None

            # Extract date from timestamp
            timestamp = entry.timestamp if hasattr(entry, 'timestamp') else None
            if timestamp:
                date_str = timestamp.date().isoformat()
            else:
                return None

            weight_kg = entry.weight  # Weight in kg

            # Convert weight based on unit system
            if self.unit_system == "imperial":
                weight = convert_kg_to_lbs(weight_kg)
                weight_unit = "lbs"
            else:
                weight = weight_kg
                weight_unit = "kg"

            metrics = {
                "date": date_str,
                "external_id": f"body_{date_str}",
                "weight": round(weight, 1),
                "weight_unit": weight_unit,
            }

            # Add optional body composition metrics if available
            if hasattr(entry, 'bmi') and entry.bmi:
                metrics["bmi"] = entry.bmi
            if hasattr(entry, 'body_fat_percentage') and entry.body_fat_percentage:
                metrics["body_fat_percent"] = entry.body_fat_percentage
            if hasattr(entry, 'muscle_mass') and entry.muscle_mass:
                metrics["muscle_mass"] = entry.muscle_mass
            if hasattr(entry, 'bone_mass') and entry.bone_mass:
                metrics["bone_mass"] = entry.bone_mass
            if hasattr(entry, 'body_water_percentage') and entry.body_water_percentage:
                metrics["body_water_percent"] = entry.body_water_percentage

            return metrics

        except Exception as e:
            logger.error(f"Error normalizing body composition: {e}")
            return None
