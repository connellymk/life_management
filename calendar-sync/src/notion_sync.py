"""
Notion synchronization module
Handles creating and updating pages in Notion databases
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from notion_client import Client
from notion_client.errors import APIResponseError

from src.config import Config
from src.utils import logger, retry_with_backoff, RateLimiter


class NotionSync:
    """Handles Notion API operations for syncing calendar events"""

    def __init__(self):
        """Initialize Notion client and rate limiter"""
        if not Config.NOTION_TOKEN:
            raise ValueError("NOTION_TOKEN not set in configuration")

        self.client = Client(auth=Config.NOTION_TOKEN)
        # Notion rate limit: 3 requests per second
        self.rate_limiter = RateLimiter(calls_per_second=2.5)  # Be conservative

        # Cache for database schemas
        self._database_schemas: Dict[str, Any] = {}

        # Simple in-memory cache for external ID -> page ID mapping
        # This will be replaced by SQLite state manager in the enhanced version
        self._external_id_cache: Dict[str, str] = {}

    @retry_with_backoff(max_retries=3, exceptions=(APIResponseError,))
    def test_connection(self) -> bool:
        """
        Test connection to Notion API

        Returns:
            True if connection successful
        """
        try:
            self.rate_limiter.wait_if_needed()
            # Try to list users as a simple test
            self.client.users.me()
            logger.info("Successfully connected to Notion API")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Notion API: {e}")
            return False

    @retry_with_backoff(max_retries=3, exceptions=(APIResponseError,))
    def test_database_access(self, database_id: str) -> bool:
        """
        Test access to a specific database

        Args:
            database_id: Notion database ID

        Returns:
            True if database is accessible
        """
        try:
            self.rate_limiter.wait_if_needed()
            db = self.client.databases.retrieve(database_id=database_id)
            logger.info(f"Successfully accessed database: {db.get('title', [{}])[0].get('plain_text', 'Unknown')}")
            return True
        except APIResponseError as e:
            if e.code == "object_not_found":
                logger.error(f"Database not found: {database_id}")
                logger.error("Make sure the database is shared with your integration")
            else:
                logger.error(f"Error accessing database: {e}")
            return False

    @retry_with_backoff(max_retries=3, exceptions=(APIResponseError,))
    def get_database_schema(self, database_id: str) -> Dict[str, Any]:
        """
        Get database schema (properties)

        Args:
            database_id: Notion database ID

        Returns:
            Database properties dictionary
        """
        if database_id in self._database_schemas:
            return self._database_schemas[database_id]

        try:
            self.rate_limiter.wait_if_needed()
            db = self.client.databases.retrieve(database_id=database_id)
            schema = db.get("properties", {})
            self._database_schemas[database_id] = schema
            return schema
        except Exception as e:
            logger.error(f"Error retrieving database schema: {e}")
            return {}

    def check_event_exists(self, external_id: str) -> Optional[str]:
        """
        Check if an event already exists in Notion by external ID

        Args:
            external_id: External ID to search for

        Returns:
            Notion page ID if found, None otherwise
        """
        # Check cache first
        if external_id in self._external_id_cache:
            return self._external_id_cache[external_id]

        # Query Notion database
        try:
            self.rate_limiter.wait_if_needed()
            results = self.client.databases.query(
                database_id=Config.NOTION_CALENDAR_DB_ID,
                filter={
                    "property": "External ID",
                    "rich_text": {"equals": external_id},
                },
            )

            pages = results.get("results", [])
            if pages:
                page_id = pages[0]["id"]
                # Cache the result
                self._external_id_cache[external_id] = page_id
                return page_id

            return None

        except Exception as e:
            logger.error(f"Error checking if event exists: {e}")
            return None

    @retry_with_backoff(max_retries=3, exceptions=(APIResponseError,))
    def create_event(self, properties: Dict[str, Any]) -> Optional[str]:
        """
        Create a new event page in Notion

        Args:
            properties: Notion page properties

        Returns:
            Created page ID, or None if failed
        """
        try:
            self.rate_limiter.wait_if_needed()
            response = self.client.pages.create(
                parent={"database_id": Config.NOTION_CALENDAR_DB_ID},
                properties=properties,
            )

            page_id = response["id"]

            # Cache the external ID mapping
            external_id = properties.get("External ID", {}).get("rich_text", [{}])[0].get("text", {}).get("content")
            if external_id:
                self._external_id_cache[external_id] = page_id

            logger.debug(f"Created event: {properties['Title']['title'][0]['text']['content']}")
            return page_id

        except APIResponseError as e:
            logger.error(f"Error creating event in Notion: {e}")
            return None

    @retry_with_backoff(max_retries=3, exceptions=(APIResponseError,))
    def update_event(self, page_id: str, properties: Dict[str, Any]) -> bool:
        """
        Update an existing event page in Notion

        Args:
            page_id: Notion page ID to update
            properties: Updated properties

        Returns:
            True if successful, False otherwise
        """
        try:
            self.rate_limiter.wait_if_needed()
            self.client.pages.update(page_id=page_id, properties=properties)
            logger.debug(f"Updated event: {page_id}")
            return True

        except APIResponseError as e:
            logger.error(f"Error updating event in Notion: {e}")
            return False

    def create_or_update_event(
        self, properties: Dict[str, Any], external_id: str
    ) -> str:
        """
        Create a new event or update existing one

        Args:
            properties: Notion page properties
            external_id: External ID for duplicate checking

        Returns:
            'created', 'updated', or 'failed'
        """
        # Check if event already exists
        existing_page_id = self.check_event_exists(external_id)

        if existing_page_id:
            # Update existing event
            if self.update_event(existing_page_id, properties):
                return "updated"
            else:
                return "failed"
        else:
            # Create new event
            page_id = self.create_event(properties)
            if page_id:
                return "created"
            else:
                return "failed"

    def get_all_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all events from the calendar database

        Args:
            limit: Maximum number of events to retrieve

        Returns:
            List of event pages
        """
        try:
            self.rate_limiter.wait_if_needed()
            results = self.client.databases.query(
                database_id=Config.NOTION_CALENDAR_DB_ID,
                page_size=min(limit, 100),  # Notion max is 100 per request
            )

            return results.get("results", [])

        except Exception as e:
            logger.error(f"Error fetching events from Notion: {e}")
            return []

    def clear_cache(self):
        """Clear the internal cache"""
        self._external_id_cache.clear()
        self._database_schemas.clear()
        logger.debug("Cleared Notion sync cache")


if __name__ == "__main__":
    # Test Notion connection
    print("Testing Notion connection...\n")

    try:
        notion = NotionSync()

        # Test API connection
        print("1. Testing API connection...")
        if notion.test_connection():
            print("   ✓ Connected to Notion API\n")
        else:
            print("   ✗ Failed to connect to Notion API\n")
            exit(1)

        # Test calendar database access
        if Config.NOTION_CALENDAR_DB_ID:
            print("2. Testing Calendar Events database access...")
            if notion.test_database_access(Config.NOTION_CALENDAR_DB_ID):
                print("   ✓ Calendar Events database accessible\n")

                # Get schema
                print("3. Fetching database schema...")
                schema = notion.get_database_schema(Config.NOTION_CALENDAR_DB_ID)
                if schema:
                    print(f"   ✓ Found {len(schema)} properties:")
                    for prop_name, prop_config in schema.items():
                        prop_type = prop_config.get("type", "unknown")
                        print(f"     - {prop_name} ({prop_type})")
                    print()
            else:
                print("   ✗ Cannot access Calendar Events database\n")
                print("   Make sure the database is shared with your integration")
        else:
            print("2. NOTION_CALENDAR_DB_ID not set in .env file\n")

        print("✓ All Notion tests completed!")

    except Exception as e:
        print(f"✗ Error during testing: {e}")
        exit(1)
