"""
SQLite database module for storing high-volume data.
Provides CRUD operations for health data.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Database:
    """
    SQLite database manager for personal assistant data.

    Handles:
    - Health data (daily metrics, body metrics)
    - Schema migrations
    - CRUD operations
    """

    def __init__(self, db_path: str = "data.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_database_exists()
        logger.info(f"Initialized database at {db_path}")

    def _ensure_database_exists(self):
        """Create database file if it doesn't exist."""
        db_file = Path(self.db_path)
        if not db_file.exists():
            logger.info(f"Creating new database at {self.db_path}")
            # Touch the file
            db_file.touch()
            # Set restrictive permissions (owner only)
            try:
                db_file.chmod(0o600)
            except Exception as e:
                logger.warning(f"Could not set database file permissions: {e}")

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Yields:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def initialize_schema(self):
        """
        Create all tables and indexes if they don't exist.
        Safe to run multiple times (uses IF NOT EXISTS).
        """
        logger.info("Initializing database schema...")

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Health Tables
            self._create_daily_metrics_table(cursor)
            self._create_body_metrics_table(cursor)

            conn.commit()

        logger.info("✓ Database schema initialized")

    def _create_daily_metrics_table(self, cursor):
        """Create daily_metrics table and indexes."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL UNIQUE,
                steps INTEGER,
                distance_miles REAL,
                floors_climbed REAL,
                calories_active INTEGER,
                calories_total INTEGER,
                sleep_duration_hours REAL,
                sleep_score INTEGER,
                resting_heart_rate INTEGER,
                min_heart_rate INTEGER,
                max_heart_rate INTEGER,
                avg_stress INTEGER,
                body_battery_max INTEGER,
                moderate_intensity_minutes INTEGER,
                vigorous_intensity_minutes INTEGER,
                vo2_max REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(date DESC)")

    def _create_body_metrics_table(self, cursor):
        """Create body_metrics table and indexes."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS body_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL UNIQUE,
                weight_lbs REAL,
                bmi REAL,
                body_fat_pct REAL,
                muscle_mass_lbs REAL,
                bone_mass_lbs REAL,
                body_water_pct REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_body_metrics_date ON body_metrics(date DESC)")

    def get_table_counts(self) -> Dict[str, int]:
        """
        Get row counts for all tables.

        Returns:
            Dictionary mapping table names to row counts
        """
        tables = [
            "daily_metrics", "body_metrics"
        ]

        counts = {}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cursor.fetchone()[0]

        return counts

    def vacuum(self):
        """
        Optimize database by reclaiming unused space.
        Run periodically for better performance.
        """
        logger.info("Running VACUUM on database...")
        with self.get_connection() as conn:
            conn.execute("VACUUM")
        logger.info("✓ Database optimized")

    def get_database_size(self) -> int:
        """
        Get database file size in bytes.

        Returns:
            File size in bytes
        """
        db_file = Path(self.db_path)
        if db_file.exists():
            return db_file.stat().st_size
        return 0

    def verify_schema(self) -> Tuple[bool, List[str]]:
        """
        Verify that all expected tables exist.

        Returns:
            Tuple of (is_valid, list of errors)
        """
        expected_tables = [
            "daily_metrics", "body_metrics"
        ]

        errors = []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}

            for table in expected_tables:
                if table not in existing_tables:
                    errors.append(f"Missing table: {table}")

        return len(errors) == 0, errors

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as list of dicts.

        Args:
            query: SQL query string
            params: Query parameters (for safety)

        Returns:
            List of dictionaries (column_name: value)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            columns = [description[0] for description in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results

    def backup(self, backup_path: str):
        """
        Create a backup of the database.

        Args:
            backup_path: Path for backup file
        """
        logger.info(f"Creating database backup at {backup_path}")

        with self.get_connection() as conn:
            backup_conn = sqlite3.connect(backup_path)
            conn.backup(backup_conn)
            backup_conn.close()

        # Set restrictive permissions on backup
        try:
            Path(backup_path).chmod(0o600)
        except Exception as e:
            logger.warning(f"Could not set backup file permissions: {e}")

        logger.info("✓ Database backup created")
