"""
Notion Calendar Events sync operations.

This module handles syncing Google Calendar events to Notion,
linking each event to the appropriate Daily Tracking record via the Day relation.
"""

from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, TYPE_CHECKING
import logging
import pytz
import requests

from core.config import Config

if TYPE_CHECKING:
    from notion.health import NotionDailyTrackingSync

logger = logging.getLogger(__name__)

# Bozeman, MT timezone
MOUNTAIN_TZ = pytz.timezone('America/Denver')

# Notion API base URL
NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class NotionCalendarSync:
    """Sync calendar events to Notion."""

    def __init__(self, token: str = None, daily_tracking_sync: 'NotionDailyTrackingSync' = None):
        """
        Initialize Notion calendar sync.

        Args:
            token: Notion API token (uses Config.NOTION_TOKEN if not provided)
            daily_tracking_sync: Optional NotionDailyTrackingSync instance for Day relations
        """
        self.token = token or Config.NOTION_TOKEN
        if not self.token:
            raise ValueError("Notion token is required. Set NOTION_TOKEN in .env")

        # Data source IDs from config
        self.data_source_id = Config.NOTION_CALENDAR_DB_ID

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }

        # Store reference for Day relations (uses Daily Tracking as Day table)
        self._daily_tracking_sync = daily_tracking_sync

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

    def _get_day_page_id(self, date_obj: datetime) -> Optional[str]:
        """
        Get the Day (Daily Tracking) page ID for a given date.

        Uses the NotionDailyTrackingSync to look up or create the Day record.

        Args:
            date_obj: datetime object (should be in Mountain Time)

        Returns:
            Page ID for the Day record, or None if not available
        """
        if not self._daily_tracking_sync:
            logger.debug("No daily_tracking_sync provided, skipping Day relation")
            return None

        # Format date as ISO string
        iso_date = date_obj.strftime('%Y-%m-%d')

        # Use the Daily Tracking sync to get or create the Day page
        return self._daily_tracking_sync.get_day_page_id(iso_date, create_if_missing=True)

    def _format_datetime_for_notion(self, dt: datetime) -> str:
        """
        Format datetime for Notion API (ISO 8601).

        Args:
            dt: datetime object

        Returns:
            ISO 8601 formatted string
        """
        if dt.tzinfo is None:
            # Assume UTC if no timezone
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    def _format_date_for_notion(self, dt: datetime) -> str:
        """
        Format date only (no time) for Notion API.

        Args:
            dt: datetime object

        Returns:
            Date string in YYYY-MM-DD format
        """
        return dt.strftime('%Y-%m-%d')

    def get_event_by_external_id(self, external_id: str) -> Optional[Dict]:
        """
        Find an event by its External ID.

        Args:
            external_id: External event ID (e.g., Google Calendar event ID)

        Returns:
            Page data if found, None otherwise
        """
        try:
            response = self._make_request(
                "POST",
                f"/databases/{self.data_source_id}/query",
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
            logger.error(f"Error finding event by external ID: {e}")

        return None

    def get_all_synced_events(self, source: Optional[str] = None) -> List[Dict]:
        """
        Get all events with an External ID (synced events).

        Args:
            source: Optional source filter (e.g., "Personal", "School and Research")

        Returns:
            List of page data for synced events
        """
        all_results = []
        has_more = True
        next_cursor = None

        filter_obj = {
            "property": "External ID",
            "rich_text": {
                "is_not_empty": True
            }
        }

        # Add source filter if specified
        if source:
            filter_obj = {
                "and": [
                    filter_obj,
                    {
                        "property": "Source",
                        "select": {
                            "equals": source
                        }
                    }
                ]
            }

        while has_more:
            query = {
                "filter": filter_obj,
                "page_size": 100
            }

            if next_cursor:
                query["start_cursor"] = next_cursor

            try:
                response = self._make_request(
                    "POST",
                    f"/databases/{self.data_source_id}/query",
                    query
                )

                all_results.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                next_cursor = response.get("next_cursor")

            except Exception as e:
                logger.error(f"Error fetching synced events: {e}")
                break

        return all_results

    def create_event(self, event_data: Dict) -> Dict:
        """
        Create a calendar event in Notion.

        Args:
            event_data: Dictionary with event fields:
                - Event ID: External ID from Google Calendar
                - Title: Event title
                - Start Time: datetime object
                - End Time: datetime object (optional)
                - All Day: bool
                - Calendar: Source calendar name (maps to Source)
                - Location: string (optional)
                - Description: string (optional)
                - Attendees: list of attendee names/emails (optional)
                - Status: string (optional)

        Returns:
            Created page data from Notion
        """
        # Parse start time
        start_time = event_data.get('Start Time')
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))

        is_all_day = event_data.get('All Day', False)
        end_time = event_data.get('End Time')

        if end_time and isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

        # Convert to Mountain Time for Day lookup
        if start_time.tzinfo:
            start_time_mt = start_time.astimezone(MOUNTAIN_TZ)
        else:
            start_time_mt = MOUNTAIN_TZ.localize(start_time)

        # Build properties
        properties = {
            "Title": {
                "title": [{"text": {"content": event_data.get('Title', '(No title)')}}]
            },
            "External ID": {
                "rich_text": [{"text": {"content": event_data.get('Event ID', '')}}]
            },
            "Last Synced": {
                "date": {"start": self._format_datetime_for_notion(datetime.now(timezone.utc))}
            },
            "Sync Status": {
                "select": {"name": "Active"}
            }
        }

        # Map Calendar to Source
        calendar_name = event_data.get('Calendar', 'Personal')
        properties["Source"] = {"select": {"name": calendar_name}}

        # Handle start/end times
        if is_all_day:
            # All-day event: just use date
            properties["Start Time"] = {
                "date": {"start": self._format_date_for_notion(start_time_mt)}
            }
            if end_time:
                end_time_mt = end_time.astimezone(MOUNTAIN_TZ) if end_time.tzinfo else MOUNTAIN_TZ.localize(end_time)
                properties["End Time"] = {
                    "date": {"start": self._format_date_for_notion(end_time_mt)}
                }
        else:
            # Timed event: include time
            properties["Start Time"] = {
                "date": {"start": self._format_datetime_for_notion(start_time)}
            }
            if end_time:
                properties["End Time"] = {
                    "date": {"start": self._format_datetime_for_notion(end_time)}
                }

        # Add location
        if event_data.get('Location'):
            properties["Location"] = {
                "rich_text": [{"text": {"content": event_data['Location'][:2000]}}]
            }

        # Add description
        if event_data.get('Description'):
            properties["Description"] = {
                "rich_text": [{"text": {"content": event_data['Description'][:2000]}}]
            }

        # Add attendees as multi-select
        if event_data.get('Attendees'):
            attendees = event_data['Attendees']
            if isinstance(attendees, str):
                attendees = [a.strip() for a in attendees.split(',') if a.strip()]
            # Sanitize attendee names for multi-select (no commas, max 100 chars)
            attendee_options = []
            for name in attendees[:10]:  # Limit to 10 attendees
                sanitized = name.replace(',', ' ').strip()[:100]
                if sanitized:
                    attendee_options.append({"name": sanitized})
            if attendee_options:
                properties["Attendees"] = {"multi_select": attendee_options}

        # Add URL if available
        if event_data.get('URL'):
            properties["userDefined:URL"] = {"url": event_data['URL']}

        # Link to Daily Tracking record
        day_page_id = self._get_day_page_id(start_time_mt)
        if day_page_id:
            properties["Daily Tracking"] = {
                "relation": [{"id": day_page_id}]
            }

        # Create the page
        page_data = {
            "parent": {"database_id": self.data_source_id},
            "properties": properties
        }

        logger.info(f"Creating event '{event_data.get('Title')}' for {start_time_mt.strftime('%Y-%m-%d')}")

        try:
            result = self._make_request("POST", "/pages", page_data)
            return result
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            raise

    def update_event(self, page_id: str, event_data: Dict) -> Dict:
        """
        Update an existing calendar event in Notion.

        Args:
            page_id: Notion page ID
            event_data: Dictionary with fields to update

        Returns:
            Updated page data from Notion
        """
        properties = {}

        is_all_day = event_data.get('All Day', False)

        # Handle start time
        if 'Start Time' in event_data:
            start_time = event_data['Start Time']
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))

            if start_time.tzinfo:
                start_time_mt = start_time.astimezone(MOUNTAIN_TZ)
            else:
                start_time_mt = MOUNTAIN_TZ.localize(start_time)

            if is_all_day:
                properties["Start Time"] = {
                    "date": {"start": self._format_date_for_notion(start_time_mt)}
                }
            else:
                properties["Start Time"] = {
                    "date": {"start": self._format_datetime_for_notion(start_time)}
                }

            # Update Daily Tracking relation
            day_page_id = self._get_day_page_id(start_time_mt)
            if day_page_id:
                properties["Daily Tracking"] = {
                    "relation": [{"id": day_page_id}]
                }

        # Handle end time
        if 'End Time' in event_data:
            end_time = event_data['End Time']
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

            if end_time.tzinfo:
                end_time_mt = end_time.astimezone(MOUNTAIN_TZ)
            else:
                end_time_mt = MOUNTAIN_TZ.localize(end_time)

            if is_all_day:
                properties["End Time"] = {
                    "date": {"start": self._format_date_for_notion(end_time_mt)}
                }
            else:
                properties["End Time"] = {
                    "date": {"start": self._format_datetime_for_notion(end_time)}
                }

        # Handle title
        if 'Title' in event_data:
            properties["Title"] = {
                "title": [{"text": {"content": event_data['Title']}}]
            }

        # Handle Calendar -> Source
        if 'Calendar' in event_data:
            properties["Source"] = {"select": {"name": event_data['Calendar']}}

        # Handle other fields
        if 'Location' in event_data:
            properties["Location"] = {
                "rich_text": [{"text": {"content": event_data['Location'][:2000]}}]
            }

        if 'Description' in event_data:
            properties["Description"] = {
                "rich_text": [{"text": {"content": event_data['Description'][:2000]}}]
            }

        if 'Attendees' in event_data:
            attendees = event_data['Attendees']
            if isinstance(attendees, str):
                attendees = [a.strip() for a in attendees.split(',') if a.strip()]
            attendee_options = []
            for name in attendees[:10]:
                sanitized = name.replace(',', ' ').strip()[:100]
                if sanitized:
                    attendee_options.append({"name": sanitized})
            properties["Attendees"] = {"multi_select": attendee_options}

        if 'URL' in event_data:
            properties["userDefined:URL"] = {"url": event_data['URL']}

        # Always update sync timestamp and status
        properties["Last Synced"] = {
            "date": {"start": self._format_datetime_for_notion(datetime.now(timezone.utc))}
        }
        properties["Sync Status"] = {"select": {"name": "Updated"}}

        logger.info(f"Updating event {page_id}")

        try:
            result = self._make_request("PATCH", f"/pages/{page_id}", {"properties": properties})
            return result
        except Exception as e:
            logger.error(f"Error updating event: {e}")
            raise

    def delete_event(self, page_id: str) -> bool:
        """
        Delete (archive) a calendar event in Notion.

        Args:
            page_id: Notion page ID

        Returns:
            True if deleted successfully
        """
        logger.info(f"Archiving event {page_id}")

        try:
            self._make_request("PATCH", f"/pages/{page_id}", {"archived": True})
            return True
        except Exception as e:
            logger.error(f"Error archiving event: {e}")
            return False

    def mark_event_cancelled(self, page_id: str) -> Dict:
        """
        Mark an event as cancelled without deleting it.

        Args:
            page_id: Notion page ID

        Returns:
            Updated page data
        """
        properties = {
            "Sync Status": {"select": {"name": "Cancelled"}},
            "Last Synced": {
                "date": {"start": self._format_datetime_for_notion(datetime.now(timezone.utc))}
            }
        }

        logger.info(f"Marking event {page_id} as cancelled")

        try:
            result = self._make_request("PATCH", f"/pages/{page_id}", {"properties": properties})
            return result
        except Exception as e:
            logger.error(f"Error marking event as cancelled: {e}")
            raise

    def sync_event(self, event_data: Dict) -> Dict:
        """
        Sync an event to Notion (create or update).

        This method checks if an event already exists by External ID,
        and either creates a new record or updates the existing one.

        Args:
            event_data: Event data dictionary

        Returns:
            Synced event page data
        """
        event_id = event_data.get('Event ID')
        if not event_id:
            raise ValueError("Event ID is required for syncing")

        existing = self.get_event_by_external_id(event_id)

        if existing:
            page_id = existing['id']
            return self.update_event(page_id, event_data)
        else:
            return self.create_event(event_data)
