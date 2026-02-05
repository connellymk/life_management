"""
Pre-built queries for common health analyses.
These queries can be used by Claude for data analysis.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta

from core.database import Database

logger = logging.getLogger(__name__)


class AnalyticsQueries:
    """
    Pre-built SQL queries for common analytics tasks.

    Makes it easy for Claude to analyze data without writing raw SQL.
    """

    def __init__(self, database: Database):
        """
        Initialize analytics queries.

        Args:
            database: Database instance
        """
        self.db = database

    # ==================== HEALTH ANALYTICS ====================

    def weekly_activity_summary(
        self,
        num_weeks: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Get weekly activity summary (steps, calories, exercise).

        Args:
            num_weeks: Number of weeks to analyze

        Returns:
            List of weekly summaries
        """
        start_date = (datetime.now() - timedelta(days=num_weeks * 7)).date()

        query = """
            SELECT
                strftime('%Y-W%W', date) as week,
                AVG(steps) as avg_steps,
                AVG(distance_miles) as avg_distance,
                AVG(calories_active) as avg_active_calories,
                AVG(sleep_duration_hours) as avg_sleep,
                AVG(resting_heart_rate) as avg_resting_hr,
                SUM(moderate_intensity_minutes + vigorous_intensity_minutes) as total_exercise_minutes
            FROM daily_metrics
            WHERE date >= ?
            GROUP BY week
            ORDER BY week DESC
        """

        return self.db.execute_query(query, (start_date,))

    def sleep_vs_activity_correlation(
        self,
        num_days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Analyze correlation between sleep and next-day activity.

        Args:
            num_days: Number of days to analyze

        Returns:
            List of {date, sleep_hours, next_day_steps, next_day_calories}
        """
        start_date = (datetime.now() - timedelta(days=num_days)).date()

        query = """
            SELECT
                m1.date,
                m1.sleep_duration_hours as sleep_hours,
                m1.sleep_score,
                m2.steps as next_day_steps,
                m2.calories_active as next_day_active_calories,
                m2.avg_stress as next_day_stress
            FROM daily_metrics m1
            LEFT JOIN daily_metrics m2 ON m2.date = date(m1.date, '+1 day')
            WHERE m1.date >= ?
              AND m1.sleep_duration_hours IS NOT NULL
            ORDER BY m1.date DESC
        """

        return self.db.execute_query(query, (start_date,))

    def stress_patterns(
        self,
        num_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Analyze stress patterns by day of week.

        Args:
            num_days: Number of days to analyze

        Returns:
            List of {day_of_week, avg_stress, avg_sleep}
        """
        start_date = (datetime.now() - timedelta(days=num_days)).date()

        query = """
            SELECT
                CASE CAST(strftime('%w', date) AS INTEGER)
                    WHEN 0 THEN 'Sunday'
                    WHEN 1 THEN 'Monday'
                    WHEN 2 THEN 'Tuesday'
                    WHEN 3 THEN 'Wednesday'
                    WHEN 4 THEN 'Thursday'
                    WHEN 5 THEN 'Friday'
                    WHEN 6 THEN 'Saturday'
                END as day_of_week,
                AVG(avg_stress) as avg_stress,
                AVG(sleep_duration_hours) as avg_sleep,
                AVG(body_battery_max) as avg_body_battery
            FROM daily_metrics
            WHERE date >= ?
              AND avg_stress IS NOT NULL
            GROUP BY strftime('%w', date)
            ORDER BY strftime('%w', date)
        """

        return self.db.execute_query(query, (start_date,))

    def health_trends(
        self,
        num_days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Get daily health metrics for trend analysis.

        Args:
            num_days: Number of days

        Returns:
            List of daily metrics
        """
        start_date = (datetime.now() - timedelta(days=num_days)).date()

        query = """
            SELECT
                date,
                steps,
                distance_miles,
                sleep_duration_hours,
                sleep_score,
                resting_heart_rate,
                avg_stress,
                body_battery_max,
                (moderate_intensity_minutes + vigorous_intensity_minutes) as total_exercise_minutes
            FROM daily_metrics
            WHERE date >= ?
            ORDER BY date DESC
        """

        return self.db.execute_query(query, (start_date,))
