"""
Google Calendar synchronization module
Handles authentication and syncing events from Google Calendar to Notion
"""

import os
import pickle
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from core.config import GoogleCalendarConfig as Config
from core.utils import (
    logger,
    retry_with_backoff,
    safe_get,
    truncate_string,
    generate_external_id,
)


class GoogleCalendarSync:
    """Handles Google Calendar authentication and event syncing"""

    def __init__(self):
        self.credentials: Optional[Credentials] = None
        self.service = None

    def authenticate(self) -> bool:
        """
        Authenticate with Google Calendar API using OAuth 2.0

        Returns:
            True if authentication successful, False otherwise
        """
        creds = None
        token_path = Config.BASE_DIR / Config.GOOGLE_TOKEN_PATH
        client_secret_path = Config.BASE_DIR / Config.GOOGLE_CLIENT_SECRET_PATH

        # Check if we have saved credentials
        if token_path.exists():
            try:
                with open(token_path, "rb") as token:
                    creds = pickle.load(token)
                logger.info("Loaded existing Google Calendar credentials")
            except Exception as e:
                logger.warning(f"Could not load saved credentials: {e}")
                creds = None

        # If credentials are invalid or don't exist, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("Refreshing Google Calendar credentials")
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Could not refresh credentials: {e}")
                    creds = None

            if not creds:
                # No valid credentials, need to authenticate
                if not client_secret_path.exists():
                    logger.error(
                        f"Google client secret file not found at {client_secret_path}"
                    )
                    logger.error(
                        "Please follow the setup guide in SETUP_GUIDES.md to obtain credentials"
                    )
                    return False

                try:
                    logger.info("Starting OAuth flow for Google Calendar")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(client_secret_path), Config.GOOGLE_SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    logger.info("Successfully authenticated with Google Calendar")
                except Exception as e:
                    logger.error(f"OAuth flow failed: {e}")
                    return False

            # Save the credentials for future use
            try:
                token_path.parent.mkdir(parents=True, exist_ok=True)
                with open(token_path, "wb") as token:
                    pickle.dump(creds, token)
                logger.info(f"Saved credentials to {token_path}")
            except Exception as e:
                logger.warning(f"Could not save credentials: {e}")

        self.credentials = creds

        # Build the service
        try:
            self.service = build("calendar", "v3", credentials=creds)
            logger.info("Google Calendar API service initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to build Calendar service: {e}")
            return False

    @retry_with_backoff(max_retries=3, exceptions=(HttpError,))
    def get_calendar_events(
        self,
        calendar_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_results: int = 250,
    ) -> List[Dict[str, Any]]:
        """
        Fetch events from a Google Calendar

        Args:
            calendar_id: Google Calendar ID (use 'primary' for primary calendar)
            start_date: Start date for events (default: SYNC_LOOKBACK_DAYS ago)
            end_date: End date for events (default: SYNC_LOOKAHEAD_DAYS from now)
            max_results: Maximum number of events to fetch

        Returns:
            List of event dictionaries
        """
        if not self.service:
            logger.error("Not authenticated with Google Calendar")
            return []

        # Set default date range if not provided
        if start_date is None:
            start_date = datetime.now(timezone.utc) - timedelta(
                days=Config.SYNC_LOOKBACK_DAYS
            )
        if end_date is None:
            end_date = datetime.now(timezone.utc) + timedelta(
                days=Config.SYNC_LOOKAHEAD_DAYS
            )

        # Ensure timezone-aware datetimes
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        try:
            logger.info(f"Fetching events from calendar '{calendar_id}'")
            logger.info(
                f"Date range: {start_date.date()} to {end_date.date()}"
            )

            events_result = (
                self.service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=start_date.isoformat(),
                    timeMax=end_date.isoformat(),
                    maxResults=max_results,
                    singleEvents=True,  # Expand recurring events
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            logger.info(f"Found {len(events)} events in calendar '{calendar_id}'")

            return events

        except HttpError as error:
            logger.error(f"Error fetching calendar events: {error}")
            raise

    @retry_with_backoff(max_retries=3, exceptions=(HttpError,))
    def get_calendar_events_incremental(
        self,
        calendar_id: str,
        sync_token: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Fetch events using incremental sync (much faster)

        Args:
            calendar_id: Google Calendar ID
            sync_token: Token from previous sync (None for initial sync)
            start_date: Start date for initial sync
            end_date: End date for initial sync

        Returns:
            Tuple of (events list, new sync token)
        """
        if not self.service:
            logger.error("Not authenticated with Google Calendar")
            return [], None

        try:
            if sync_token:
                # Incremental sync - only get changes since last sync
                logger.info(f"Incremental sync for '{calendar_id}' using sync token")
                events_result = (
                    self.service.events()
                    .list(
                        calendarId=calendar_id,
                        syncToken=sync_token,
                        singleEvents=True,
                    )
                    .execute()
                )
            else:
                # Initial sync - get all events in date range
                if start_date is None:
                    start_date = datetime.now(timezone.utc) - timedelta(
                        days=Config.SYNC_LOOKBACK_DAYS
                    )
                if end_date is None:
                    end_date = datetime.now(timezone.utc) + timedelta(
                        days=Config.SYNC_LOOKAHEAD_DAYS
                    )

                # Ensure timezone-aware
                if start_date.tzinfo is None:
                    start_date = start_date.replace(tzinfo=timezone.utc)
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=timezone.utc)

                logger.info(f"Initial sync for '{calendar_id}'")
                logger.info(f"Date range: {start_date.date()} to {end_date.date()}")

                events_result = (
                    self.service.events()
                    .list(
                        calendarId=calendar_id,
                        timeMin=start_date.isoformat(),
                        timeMax=end_date.isoformat(),
                        singleEvents=True,
                        orderBy="startTime",
                    )
                    .execute()
                )

            events = events_result.get("items", [])
            new_sync_token = events_result.get("nextSyncToken")

            logger.info(
                f"Found {len(events)} {'changed' if sync_token else 'total'} events"
            )

            if new_sync_token:
                logger.debug(f"Received new sync token for next incremental sync")

            return events, new_sync_token

        except HttpError as error:
            # Sync token might be invalid/expired
            if error.resp.status == 410:  # Gone - sync token invalid
                logger.warning("Sync token invalid, performing full sync")
                return self.get_calendar_events_incremental(
                    calendar_id, sync_token=None, start_date=start_date, end_date=end_date
                )
            else:
                logger.error(f"Error fetching calendar events: {error}")
                raise

    def transform_event_to_notion(
        self, event: Dict[str, Any], source_name: str
    ) -> Dict[str, Any]:
        """
        Transform a Google Calendar event into Notion page properties

        Args:
            event: Google Calendar event dictionary
            source_name: Name of the calendar source (e.g., 'Personal')

        Returns:
            Dictionary of Notion page properties
        """
        # Extract event ID
        event_id = event.get("id", "")
        external_id = generate_external_id(
            f"google_{source_name.lower().replace(' ', '_')}", event_id
        )

        # Extract title
        title = event.get("summary", "(No title)")

        # Extract dates/times
        start = event.get("start", {})
        end = event.get("end", {})

        # Handle both date and dateTime formats
        # All-day events use 'date', timed events use 'dateTime'
        start_dt = start.get("dateTime") or start.get("date")
        end_dt = end.get("dateTime") or end.get("date")

        # Extract other fields
        location = event.get("location", "")
        description = event.get("description", "")
        html_link = event.get("htmlLink", "")

        # Extract attendees
        attendees = event.get("attendees", [])
        attendee_names = [
            attendee.get("displayName") or attendee.get("email", "")
            for attendee in attendees
            if attendee.get("self") is not True  # Exclude self
        ]

        # Event status (confirmed, tentative, cancelled)
        status = event.get("status", "confirmed")

        # Build Notion properties
        # Note: This is the structure for Notion API properties
        notion_properties = {
            "Title": {"title": [{"text": {"content": truncate_string(title, 2000)}}]},
            "External ID": {"rich_text": [{"text": {"content": external_id}}]},
            "Source": {"select": {"name": source_name}},
            "Last Synced": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
        }

        # Determine if this is an all-day event
        is_all_day = "date" in start and "dateTime" not in start

        # Add start time
        if start_dt:
            if is_all_day:
                # All-day event: Just set the start date, no end
                # (Google's end date is exclusive, so we ignore it for single-day events)
                from datetime import datetime as dt, timedelta
                start_date = dt.fromisoformat(start_dt).date()
                end_date = dt.fromisoformat(end_dt).date() if end_dt else start_date

                # Check if it's truly multi-day (more than 1 day difference)
                if (end_date - start_date).days > 1:
                    # Multi-day event: use date range
                    # Subtract 1 day from end since Google uses exclusive end dates
                    actual_end = (end_date - timedelta(days=1)).isoformat()
                    notion_properties["Start Time"] = {"date": {"start": start_dt, "end": actual_end}}
                else:
                    # Single all-day event: just start date
                    notion_properties["Start Time"] = {"date": {"start": start_dt}}
            else:
                # Timed event: use separate Start Time and End Time
                notion_properties["Start Time"] = {"date": {"start": start_dt}}
                if end_dt:
                    notion_properties["End Time"] = {"date": {"start": end_dt}}

        # Add location
        if location:
            notion_properties["Location"] = {
                "rich_text": [{"text": {"content": truncate_string(location, 2000)}}]
            }

        # Add description
        if description:
            notion_properties["Description"] = {
                "rich_text": [{"text": {"content": truncate_string(description, 2000)}}]
            }

        # Add URL
        if html_link:
            notion_properties["URL"] = {"url": html_link}

        # Add attendees (as multi-select)
        if attendee_names:
            # Notion multi-select doesn't allow commas, so replace them
            # Also limit to 100 chars per name and take first 10 attendees
            sanitized_names = []
            for name in attendee_names[:10]:
                # Replace commas with spaces (e.g., "Lastname, Firstname" -> "Lastname Firstname")
                sanitized_name = name.replace(",", " ").strip()
                # Remove any double spaces
                sanitized_name = " ".join(sanitized_name.split())
                sanitized_names.append(sanitized_name[:100])

            notion_properties["Attendees"] = {
                "multi_select": [{"name": name} for name in sanitized_names]
            }

        # Add sync status
        sync_status = "Active" if status == "confirmed" else "Cancelled"
        notion_properties["Sync Status"] = {"select": {"name": sync_status}}

        return notion_properties

    def sync_calendar_to_notion(
        self,
        calendar_id: str,
        calendar_name: str,
        notion_sync,
        state_manager=None,
        use_incremental: bool = True,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Sync a Google Calendar to Notion

        Args:
            calendar_id: Google Calendar ID
            calendar_name: Display name for the calendar
            notion_sync: NotionSync instance
            state_manager: StateManager instance for incremental sync
            use_incremental: Use incremental sync if available (much faster)
            dry_run: If True, don't actually create/update in Notion

        Returns:
            Dictionary with sync statistics
        """
        logger.info(f"Starting sync for calendar: {calendar_name}")

        stats = {
            "calendar_name": calendar_name,
            "events_fetched": 0,
            "events_created": 0,
            "events_updated": 0,
            "events_skipped": 0,
            "errors": 0,
            "incremental": False,
            "new_sync_token": None,
        }

        try:
            # Try incremental sync if enabled and state manager available
            source_key = f"google_{calendar_name.lower().replace(' ', '_')}"
            sync_token = None

            if use_incremental and state_manager:
                sync_token = state_manager.get_sync_token(source_key)
                if sync_token:
                    logger.info("Using incremental sync (only fetching changes)")
                    stats["incremental"] = True

            if use_incremental and state_manager:
                # Use incremental sync
                events, new_sync_token = self.get_calendar_events_incremental(
                    calendar_id, sync_token=sync_token
                )
                stats["new_sync_token"] = new_sync_token
            else:
                # Fall back to full sync
                events = self.get_calendar_events(calendar_id)

            stats["events_fetched"] = len(events)

            if not events:
                logger.info(f"No events found in calendar '{calendar_name}'")
                return stats

            if dry_run:
                logger.info(f"[DRY RUN] Would sync {len(events)} events")
                # Show sample events
                for i, event in enumerate(events[:5]):
                    title = event.get("summary", "(No title)")
                    start = safe_get(event, "start", "dateTime") or safe_get(
                        event, "start", "date"
                    )
                    logger.info(f"  {i+1}. {title} ({start})")
                if len(events) > 5:
                    logger.info(f"  ... and {len(events) - 5} more events")
                return stats

            # Process each event
            for event in events:
                try:
                    # Transform to Notion format
                    notion_properties = self.transform_event_to_notion(
                        event, calendar_name
                    )

                    # Get external ID for duplicate checking
                    external_id = notion_properties["External ID"]["rich_text"][0][
                        "text"
                    ]["content"]

                    # Create or update in Notion
                    result = notion_sync.create_or_update_event(
                        notion_properties, external_id
                    )

                    if result == "created":
                        stats["events_created"] += 1
                    elif result == "updated":
                        stats["events_updated"] += 1
                    else:
                        stats["events_skipped"] += 1

                except Exception as e:
                    logger.error(
                        f"Error processing event '{event.get('summary', 'Unknown')}': {e}"
                    )
                    stats["errors"] += 1

            logger.info(
                f"Sync completed for '{calendar_name}': "
                f"{stats['events_created']} created, "
                f"{stats['events_updated']} updated, "
                f"{stats['events_skipped']} skipped, "
                f"{stats['errors']} errors"
            )

            # Save sync token for next incremental sync
            if state_manager and stats["new_sync_token"]:
                state_manager.update_sync_state(
                    source=source_key,
                    success=True,
                    sync_token=stats["new_sync_token"]
                )
                logger.debug("Saved sync token for next incremental sync")

        except Exception as e:
            logger.error(f"Error syncing calendar '{calendar_name}': {e}")
            stats["errors"] += 1

            # Mark sync as failed in state
            if state_manager:
                state_manager.update_sync_state(
                    source=source_key,
                    success=False,
                    error=str(e)
                )

        return stats


if __name__ == "__main__":
    # Test Google Calendar authentication
    print("Testing Google Calendar authentication...\n")

    sync = GoogleCalendarSync()
    if sync.authenticate():
        print("✓ Successfully authenticated with Google Calendar!\n")

        # Try fetching events from primary calendar
        print("Fetching events from primary calendar...\n")
        events = sync.get_calendar_events("primary", max_results=5)

        if events:
            print(f"Found {len(events)} events:\n")
            for i, event in enumerate(events[:5], 1):
                title = event.get("summary", "(No title)")
                start = safe_get(event, "start", "dateTime") or safe_get(
                    event, "start", "date"
                )
                print(f"{i}. {title}")
                print(f"   Start: {start}")
                print()
        else:
            print("No events found in the specified date range")
    else:
        print("✗ Failed to authenticate with Google Calendar")
        print("Please check the logs and setup guide")
