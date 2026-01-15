"""
State management system using SQLite
Tracks sync history, event mappings, and provides fast duplicate checking
Supports all integrations (calendar, health, finance, etc.)
"""

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List, Any
from contextlib import contextmanager

from core.utils import logger


class StateManager:
    """Manages sync state using SQLite database"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize state manager

        Args:
            db_path: Path to SQLite database (default: state.db in project root)
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent / "state.db"
        else:
            db_path = Path(db_path)

        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Sync state table - tracks last sync time per source
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_state (
                    source TEXT PRIMARY KEY,
                    last_sync_timestamp TEXT,
                    last_success_timestamp TEXT,
                    sync_token TEXT,
                    last_error TEXT,
                    total_synced INTEGER DEFAULT 0,
                    total_errors INTEGER DEFAULT 0,
                    updated_at TEXT
                )
            """)

            # Event mapping table - maps external IDs to Notion page IDs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS event_mapping (
                    external_id TEXT PRIMARY KEY,
                    notion_page_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    synced_properties TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)

            # Create indexes for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_mapping_source
                ON event_mapping(source)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_mapping_notion_id
                ON event_mapping(notion_page_id)
            """)

            # Sync log table - detailed sync history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    items_synced INTEGER,
                    items_updated INTEGER,
                    items_failed INTEGER,
                    duration_seconds REAL,
                    error_message TEXT,
                    details TEXT
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_log_timestamp
                ON sync_log(timestamp DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_log_source
                ON sync_log(source)
            """)

            logger.debug(f"Initialized state database at {self.db_path}")

    # ========== Sync State Methods ==========

    def get_last_sync_time(self, source: str) -> Optional[datetime]:
        """
        Get the last successful sync time for a source

        Args:
            source: Source name (e.g., 'google_personal', 'garmin')

        Returns:
            Last sync datetime or None if never synced
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT last_success_timestamp FROM sync_state WHERE source = ?",
                (source,)
            )
            row = cursor.fetchone()

            if row and row[0]:
                return datetime.fromisoformat(row[0])
            return None

    def get_sync_token(self, source: str) -> Optional[str]:
        """
        Get the sync token for incremental syncing

        Args:
            source: Source name

        Returns:
            Sync token or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sync_token FROM sync_state WHERE source = ?",
                (source,)
            )
            row = cursor.fetchone()
            return row[0] if row and row[0] else None

    def update_sync_state(
        self,
        source: str,
        success: bool,
        sync_token: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        Update sync state after a sync operation

        Args:
            source: Source name
            success: Whether sync was successful
            sync_token: New sync token (for incremental sync)
            error: Error message if sync failed
        """
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if source exists
            cursor.execute("SELECT source FROM sync_state WHERE source = ?", (source,))
            exists = cursor.fetchone() is not None

            if exists:
                if success:
                    cursor.execute("""
                        UPDATE sync_state
                        SET last_sync_timestamp = ?,
                            last_success_timestamp = ?,
                            sync_token = COALESCE(?, sync_token),
                            last_error = NULL,
                            total_synced = total_synced + 1,
                            updated_at = ?
                        WHERE source = ?
                    """, (now, now, sync_token, now, source))
                else:
                    cursor.execute("""
                        UPDATE sync_state
                        SET last_sync_timestamp = ?,
                            last_error = ?,
                            total_errors = total_errors + 1,
                            updated_at = ?
                        WHERE source = ?
                    """, (now, error, now, source))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO sync_state
                    (source, last_sync_timestamp, last_success_timestamp,
                     sync_token, last_error, total_synced, total_errors, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    source,
                    now,
                    now if success else None,
                    sync_token,
                    error if not success else None,
                    1 if success else 0,
                    0 if success else 1,
                    now
                ))

    # ========== Event Mapping Methods ==========

    def get_notion_page_id(self, external_id: str) -> Optional[str]:
        """
        Get Notion page ID for an external ID (fast local lookup)

        Args:
            external_id: External ID from source system

        Returns:
            Notion page ID or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT notion_page_id FROM event_mapping WHERE external_id = ?",
                (external_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def mapping_exists(self, external_id: str) -> bool:
        """
        Check if a mapping exists for an external ID

        Args:
            external_id: External ID to check

        Returns:
            True if mapping exists
        """
        return self.get_notion_page_id(external_id) is not None

    def save_mapping(
        self,
        external_id: str,
        notion_page_id: str,
        source: str,
        event_type: str,
        synced_properties: Optional[List[str]] = None
    ):
        """
        Save or update event mapping

        Args:
            external_id: External ID from source system
            notion_page_id: Notion page ID
            source: Source name
            event_type: Type of event (calendar, workout, transaction, etc.)
            synced_properties: List of properties that are synced from source
        """
        now = datetime.now(timezone.utc).isoformat()
        synced_props_json = json.dumps(synced_properties) if synced_properties else None

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if mapping exists
            cursor.execute(
                "SELECT external_id FROM event_mapping WHERE external_id = ?",
                (external_id,)
            )
            exists = cursor.fetchone() is not None

            if exists:
                cursor.execute("""
                    UPDATE event_mapping
                    SET notion_page_id = ?,
                        source = ?,
                        event_type = ?,
                        synced_properties = ?,
                        updated_at = ?
                    WHERE external_id = ?
                """, (notion_page_id, source, event_type, synced_props_json, now, external_id))
            else:
                cursor.execute("""
                    INSERT INTO event_mapping
                    (external_id, notion_page_id, source, event_type,
                     synced_properties, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (external_id, notion_page_id, source, event_type,
                      synced_props_json, now, now))

    def get_synced_properties(self, external_id: str) -> List[str]:
        """
        Get list of properties that are synced from source (shouldn't be edited in Notion)

        Args:
            external_id: External ID

        Returns:
            List of property names
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT synced_properties FROM event_mapping WHERE external_id = ?",
                (external_id,)
            )
            row = cursor.fetchone()

            if row and row[0]:
                return json.loads(row[0])
            return []

    def delete_mapping(self, external_id: str):
        """
        Delete an event mapping

        Args:
            external_id: External ID to delete
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM event_mapping WHERE external_id = ?",
                (external_id,)
            )

    # ========== Sync Log Methods ==========

    def log_sync(
        self,
        source: str,
        status: str,
        items_synced: int = 0,
        items_updated: int = 0,
        items_failed: int = 0,
        duration: float = 0,
        error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log a sync operation

        Args:
            source: Source name
            status: Sync status (success, partial, failure)
            items_synced: Number of items synced
            items_updated: Number of items updated
            items_failed: Number of items failed
            duration: Duration in seconds
            error: Error message if any
            details: Additional details as dict
        """
        now = datetime.now(timezone.utc).isoformat()
        details_json = json.dumps(details) if details else None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sync_log
                (timestamp, source, status, items_synced, items_updated,
                 items_failed, duration_seconds, error_message, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (now, source, status, items_synced, items_updated,
                  items_failed, duration, error, details_json))

    def get_recent_syncs(
        self,
        source: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent sync operations

        Args:
            source: Filter by source (None for all)
            limit: Number of records to return

        Returns:
            List of sync log dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if source:
                cursor.execute("""
                    SELECT * FROM sync_log
                    WHERE source = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (source, limit))
            else:
                cursor.execute("""
                    SELECT * FROM sync_log
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    # ========== Statistics Methods ==========

    def get_sync_stats(self, source: Optional[str] = None) -> Dict[str, Any]:
        """
        Get sync statistics

        Args:
            source: Filter by source (None for all)

        Returns:
            Dictionary with statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if source:
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_syncs,
                        SUM(items_synced) as total_items_synced,
                        SUM(items_updated) as total_items_updated,
                        SUM(items_failed) as total_items_failed,
                        AVG(duration_seconds) as avg_duration,
                        MAX(timestamp) as last_sync
                    FROM sync_log
                    WHERE source = ?
                """, (source,))
            else:
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_syncs,
                        SUM(items_synced) as total_items_synced,
                        SUM(items_updated) as total_items_updated,
                        SUM(items_failed) as total_items_failed,
                        AVG(duration_seconds) as avg_duration,
                        MAX(timestamp) as last_sync
                    FROM sync_log
                """)

            row = cursor.fetchone()
            if row:
                return dict(row)
            return {}

    def count_mappings(self, event_type: Optional[str] = None) -> int:
        """
        Count event mappings

        Args:
            event_type: Filter by event type (None for all)

        Returns:
            Number of mappings
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if event_type:
                cursor.execute(
                    "SELECT COUNT(*) FROM event_mapping WHERE event_type = ?",
                    (event_type,)
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM event_mapping")

            return cursor.fetchone()[0]

    def get_db_size(self) -> float:
        """
        Get database file size in MB

        Returns:
            Size in megabytes
        """
        if self.db_path.exists():
            size_bytes = self.db_path.stat().st_size
            return size_bytes / (1024 * 1024)
        return 0.0

    # ========== Maintenance Methods ==========

    def cleanup_old_logs(self, days: int = 30):
        """
        Delete sync logs older than specified days

        Args:
            days: Delete logs older than this many days
        """
        cutoff = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        cutoff = cutoff.replace(day=cutoff.day - days)
        cutoff_str = cutoff.isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM sync_log WHERE timestamp < ?",
                (cutoff_str,)
            )
            deleted = cursor.rowcount

        logger.info(f"Deleted {deleted} sync log entries older than {days} days")

    def reset_state(self, source: Optional[str] = None):
        """
        Reset sync state (for testing or troubleshooting)

        Args:
            source: Reset specific source (None for all)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if source:
                cursor.execute("DELETE FROM sync_state WHERE source = ?", (source,))
                cursor.execute("DELETE FROM event_mapping WHERE source = ?", (source,))
                logger.info(f"Reset state for source: {source}")
            else:
                cursor.execute("DELETE FROM sync_state")
                cursor.execute("DELETE FROM event_mapping")
                cursor.execute("DELETE FROM sync_log")
                logger.info("Reset all state")
