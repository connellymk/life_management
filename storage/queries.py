"""
Pre-built queries for common financial and health analyses.
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

    # ==================== FINANCIAL ANALYTICS ====================

    def monthly_spending_by_category(
        self,
        start_date: Optional[date] = None,
        num_months: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Get monthly spending grouped by category.

        Args:
            start_date: Start date (defaults to 6 months ago)
            num_months: Number of months to analyze

        Returns:
            List of {month, category, total, transaction_count}
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=num_months * 30)).date()

        query = """
            SELECT
                strftime('%Y-%m', date) as month,
                category_primary as category,
                SUM(amount) as total,
                COUNT(*) as transaction_count
            FROM transactions
            WHERE date >= ?
              AND amount < 0
              AND category_primary IS NOT NULL
            GROUP BY month, category
            ORDER BY month DESC, total ASC
        """

        return self.db.execute_query(query, (start_date,))

    def top_merchants(
        self,
        start_date: Optional[date] = None,
        num_days: int = 30,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get top merchants by spending.

        Args:
            start_date: Start date (defaults to 30 days ago)
            num_days: Number of days to analyze
            limit: Number of top merchants to return

        Returns:
            List of {merchant_name, total_spent, transaction_count}
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=num_days)).date()

        query = """
            SELECT
                merchant_name,
                SUM(amount) as total_spent,
                COUNT(*) as transaction_count
            FROM transactions
            WHERE date >= ?
              AND amount < 0
            GROUP BY merchant_name
            ORDER BY total_spent ASC
            LIMIT ?
        """

        return self.db.execute_query(query, (start_date, limit))

    def net_worth_trend(
        self,
        num_days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Get net worth over time.

        Args:
            num_days: Number of days of history

        Returns:
            List of {date, net_worth}
        """
        start_date = (datetime.now() - timedelta(days=num_days)).date()

        query = """
            SELECT
                date,
                SUM(current_balance) as net_worth
            FROM balances
            WHERE date >= ?
            GROUP BY date
            ORDER BY date DESC
        """

        return self.db.execute_query(query, (start_date,))

    def spending_comparison(
        self,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare current month spending to last month.

        Args:
            category: Optional category filter

        Returns:
            Dictionary with this_month, last_month, change, change_pct
        """
        today = datetime.now().date()
        this_month_start = today.replace(day=1)
        last_month_end = this_month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)

        if category:
            query = """
                SELECT
                    SUM(CASE WHEN date >= ? THEN amount ELSE 0 END) as this_month,
                    SUM(CASE WHEN date >= ? AND date < ? THEN amount ELSE 0 END) as last_month
                FROM transactions
                WHERE amount < 0
                  AND category_primary = ?
            """
            params = (this_month_start, last_month_start, this_month_start, category)
        else:
            query = """
                SELECT
                    SUM(CASE WHEN date >= ? THEN amount ELSE 0 END) as this_month,
                    SUM(CASE WHEN date >= ? AND date < ? THEN amount ELSE 0 END) as last_month
                FROM transactions
                WHERE amount < 0
            """
            params = (this_month_start, last_month_start, this_month_start)

        result = self.db.execute_query(query, params)

        if result:
            this_month = abs(result[0]['this_month'] or 0)
            last_month = abs(result[0]['last_month'] or 0)
            change = this_month - last_month
            change_pct = (change / last_month * 100) if last_month > 0 else 0

            return {
                'this_month': this_month,
                'last_month': last_month,
                'change': change,
                'change_pct': change_pct,
                'category': category
            }

        return {}

    def large_transactions(
        self,
        threshold: float = 100,
        num_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Find large transactions above threshold.

        Args:
            threshold: Minimum transaction amount
            num_days: Number of days to look back

        Returns:
            List of large transactions
        """
        start_date = (datetime.now() - timedelta(days=num_days)).date()

        query = """
            SELECT date, name, merchant_name, amount, category_primary
            FROM transactions
            WHERE date >= ?
              AND ABS(amount) >= ?
            ORDER BY ABS(amount) DESC
        """

        return self.db.execute_query(query, (start_date, threshold))

    def account_summary(self) -> List[Dict[str, Any]]:
        """
        Get summary of all accounts with latest balances.

        Returns:
            List of accounts with balances
        """
        query = """
            SELECT
                a.name,
                a.type,
                a.masked_number,
                a.institution_name,
                b.current_balance,
                b.available_balance,
                b.date as last_updated
            FROM accounts a
            LEFT JOIN (
                SELECT account_id, current_balance, available_balance, date
                FROM balances
                WHERE (account_id, date) IN (
                    SELECT account_id, MAX(date)
                    FROM balances
                    GROUP BY account_id
                )
            ) b ON a.account_id = b.account_id
            ORDER BY a.type, a.name
        """

        return self.db.execute_query(query)

    def investment_performance(self) -> List[Dict[str, Any]]:
        """
        Get investment performance with gains/losses.

        Returns:
            List of holdings with calculated performance
        """
        query = """
            SELECT
                name,
                ticker,
                quantity,
                price,
                value,
                cost_basis,
                (value - COALESCE(cost_basis, value)) as gain_loss,
                CASE
                    WHEN cost_basis > 0 THEN
                        ((value - cost_basis) / cost_basis * 100)
                    ELSE 0
                END as gain_loss_pct
            FROM investments
            WHERE date = (SELECT MAX(date) FROM investments)
            ORDER BY value DESC
        """

        return self.db.execute_query(query)

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
