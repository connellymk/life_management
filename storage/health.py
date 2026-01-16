"""
Health data storage operations for SQL database.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import date

from core.database import Database

logger = logging.getLogger(__name__)


class HealthStorage:
    """
    Storage operations for health data.

    Handles CRUD operations for:
    - Daily metrics
    - Body metrics
    """

    def __init__(self, database: Database):
        """
        Initialize health storage.

        Args:
            database: Database instance
        """
        self.db = database

    # ==================== DAILY METRICS ====================

    def save_daily_metric(self, metric_data: Dict[str, Any]) -> bool:
        """
        Save or update a daily metric entry.

        Args:
            metric_data: Normalized daily metric data from Garmin

        Returns:
            True if successful
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Extract date
                metric_date = metric_data.get('date')
                if isinstance(metric_date, str):
                    from datetime import datetime
                    metric_date = datetime.fromisoformat(metric_date).date()

                cursor.execute("""
                    INSERT INTO daily_metrics (
                        date, steps, distance_miles, floors_climbed,
                        calories_active, calories_total, sleep_duration_hours, sleep_score,
                        resting_heart_rate, min_heart_rate, max_heart_rate,
                        avg_stress, body_battery_max,
                        moderate_intensity_minutes, vigorous_intensity_minutes, vo2_max,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(date) DO UPDATE SET
                        steps = excluded.steps,
                        distance_miles = excluded.distance_miles,
                        floors_climbed = excluded.floors_climbed,
                        calories_active = excluded.calories_active,
                        calories_total = excluded.calories_total,
                        sleep_duration_hours = excluded.sleep_duration_hours,
                        sleep_score = excluded.sleep_score,
                        resting_heart_rate = excluded.resting_heart_rate,
                        min_heart_rate = excluded.min_heart_rate,
                        max_heart_rate = excluded.max_heart_rate,
                        avg_stress = excluded.avg_stress,
                        body_battery_max = excluded.body_battery_max,
                        moderate_intensity_minutes = excluded.moderate_intensity_minutes,
                        vigorous_intensity_minutes = excluded.vigorous_intensity_minutes,
                        vo2_max = excluded.vo2_max,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    metric_date,
                    metric_data.get('steps'),
                    metric_data.get('distance'),
                    metric_data.get('floors_climbed'),
                    metric_data.get('active_calories'),
                    metric_data.get('total_calories'),
                    metric_data.get('sleep_hours'),
                    metric_data.get('sleep_score'),
                    metric_data.get('avg_hr'),
                    metric_data.get('min_hr'),
                    metric_data.get('max_hr'),
                    metric_data.get('avg_stress'),
                    metric_data.get('body_battery_max'),
                    metric_data.get('moderate_intensity_minutes'),
                    metric_data.get('vigorous_intensity_minutes'),
                    metric_data.get('vo2_max')
                ))

            if cursor.rowcount > 0:
                logger.debug(f"Saved daily metric for {metric_date}")
            return True

        except Exception as e:
            logger.error(f"Error saving daily metric: {e}")
            return False

    def get_daily_metrics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Get daily metrics with optional date filters.

        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum results

        Returns:
            List of daily metric dictionaries
        """
        query = "SELECT * FROM daily_metrics WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)

        return self.db.execute_query(query, tuple(params))

    def get_daily_metric(self, metric_date: date) -> Optional[Dict[str, Any]]:
        """Get daily metric for a specific date."""
        query = "SELECT * FROM daily_metrics WHERE date = ?"
        results = self.db.execute_query(query, (metric_date,))
        return results[0] if results else None

    def get_metric_count(self) -> int:
        """Get total daily metric count."""
        result = self.db.execute_query("SELECT COUNT(*) as count FROM daily_metrics")
        return result[0]['count'] if result else 0

    # ==================== BODY METRICS ====================

    def save_body_metric(self, metric_data: Dict[str, Any]) -> bool:
        """
        Save or update a body metric entry.

        Args:
            metric_data: Body composition data

        Returns:
            True if successful
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Extract date
                metric_date = metric_data.get('date')
                if isinstance(metric_date, str):
                    from datetime import datetime
                    metric_date = datetime.fromisoformat(metric_date).date()

                cursor.execute("""
                    INSERT INTO body_metrics (
                        date, weight_lbs, bmi, body_fat_pct,
                        muscle_mass_lbs, bone_mass_lbs, body_water_pct
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(date) DO UPDATE SET
                        weight_lbs = excluded.weight_lbs,
                        bmi = excluded.bmi,
                        body_fat_pct = excluded.body_fat_pct,
                        muscle_mass_lbs = excluded.muscle_mass_lbs,
                        bone_mass_lbs = excluded.bone_mass_lbs,
                        body_water_pct = excluded.body_water_pct
                """, (
                    metric_date,
                    metric_data.get('weight'),
                    metric_data.get('bmi'),
                    metric_data.get('body_fat_pct'),
                    metric_data.get('muscle_mass'),
                    metric_data.get('bone_mass'),
                    metric_data.get('body_water_pct')
                ))

            logger.debug(f"Saved body metric for {metric_date}")
            return True

        except Exception as e:
            logger.error(f"Error saving body metric: {e}")
            return False

    def get_body_metrics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 90
    ) -> List[Dict[str, Any]]:
        """Get body metrics with optional date filters."""
        query = "SELECT * FROM body_metrics WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)

        return self.db.execute_query(query, tuple(params))

    def get_body_metric(self, metric_date: date) -> Optional[Dict[str, Any]]:
        """Get body metric for a specific date."""
        query = "SELECT * FROM body_metrics WHERE date = ?"
        results = self.db.execute_query(query, (metric_date,))
        return results[0] if results else None
