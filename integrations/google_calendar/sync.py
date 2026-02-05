"""
Google Calendar synchronization module
Handles authentication and fetching events from Google Calendar API
Events are synced to Notion via the calendar orchestrator
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
        Transform a Google Calendar event into Notion event data

        Args:
            event: Google Calendar event dictionary
            source_name: Name of the calendar source (e.g., 'Personal')

        Returns:
            Dictionary of Notion event fields
        """
        from datetime import datetime as dt, timedelta
        import pytz

        # Mountain Time timezone
        mountain_tz = pytz.timezone('America/Denver')
        utc = pytz.UTC

        # Extract event ID
        event_id = event.get("id", "")

        # Extract title
        title = event.get("summary", "(No title)")

        # Extract dates/times
        start = event.get("start", {})
        end = event.get("end", {})

        # Handle both date and dateTime formats
        start_dt_str = start.get("dateTime") or start.get("date")
        end_dt_str = end.get("dateTime") or end.get("date")

        # Determine if this is an all-day event
        is_all_day = "date" in start and "dateTime" not in start

        # Parse start time
        if is_all_day:
            # All-day event: date string (YYYY-MM-DD)
            start_date = dt.fromisoformat(start_dt_str).date()
            # Localize to Mountain Time at midnight
            start_time = mountain_tz.localize(dt.combine(start_date, dt.min.time()))

            # Google's end date is exclusive for all-day events
            # For single-day events, end_date == start_date + 1
            if end_dt_str:
                end_date = dt.fromisoformat(end_dt_str).date()
                # Check if multi-day (difference > 1 day)
                if (end_date - start_date).days > 1:
                    # Multi-day: use actual end date - 1 day (convert from exclusive to inclusive)
                    end_date = end_date - timedelta(days=1)
                    end_time = mountain_tz.localize(dt.combine(end_date, dt.min.time()))
                    end_time = end_time.replace(hour=23, minute=59, second=0)
                else:
                    # Single day: end time is 11:59pm on same day
                    end_time = start_time.replace(hour=23, minute=59, second=0)
            else:
                end_time = start_time.replace(hour=23, minute=59, second=0)
        else:
            # Timed event: ISO datetime string with timezone
            start_time = dt.fromisoformat(start_dt_str.replace('Z', '+00:00'))
            end_time = dt.fromisoformat(end_dt_str.replace('Z', '+00:00')) if end_dt_str else None

        # Extract other fields
        location = event.get("location", "")
        description = event.get("description", "")

        # Extract attendees
        attendees = event.get("attendees", [])
        attendee_list = [
            attendee.get("displayName") or attendee.get("email", "")
            for attendee in attendees
            if attendee.get("self") is not True  # Exclude self
        ]
        attendee_str = ", ".join(attendee_list) if attendee_list else ""

        # Event status (confirmed, tentative, cancelled)
        status_map = {
            "confirmed": "Confirmed",
            "tentative": "Tentative",
            "cancelled": "Cancelled"
        }
        status = status_map.get(event.get("status", "confirmed"), "Confirmed")

        # Check if recurring
        is_recurring = "recurringEventId" in event

        # Build Notion event data
        notion_data = {
            "Event ID": event_id,
            "Title": title,
            "Start Time": start_time,
            "All Day": is_all_day,
            "Calendar": source_name,
            "Status": status,
            "Recurring": is_recurring
        }

        if end_time:
            notion_data["End Time"] = end_time

        if location:
            notion_data["Location"] = location

        if description:
            notion_data["Description"] = description

        if attendee_str:
            notion_data["Attendees"] = attendee_str

        return notion_data

    def sync_calendar_to_notion(
        self,
        calendar_id: str,
        calendar_name: str,
        notion_sync,
        state_manager=None,
        use_incremental: bool = True,
        dry_run: bool = False,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Sync a Google Calendar to Notion

        Args:
            calendar_id: Google Calendar ID
            calendar_name: Display name for the calendar
            notion_sync: NotionCalendarSync instance
            state_manager: StateManager instance for incremental sync
            use_incremental: Use incremental sync if available (much faster)
            dry_run: If True, don't actually create/update in Notion
            start_date: Start date for event range (optional)
            end_date: End date for event range (optional)

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
                    calendar_id, sync_token=sync_token, start_date=start_date, end_date=end_date
                )
                stats["new_sync_token"] = new_sync_token
            else:
                # Fall back to full sync
                events = self.get_calendar_events(calendar_id, start_date=start_date, end_date=end_date)

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
                    # Check if event is cancelled
                    if event.get("status") == "cancelled":
                        # For cancelled events, we should delete from Notion if it exists
                        event_id = event.get("id", "")
                        existing = notion_sync.get_event_by_external_id(event_id)
                        if existing:
                            notion_sync.delete_event(existing['id'])
                            logger.info(f"Deleted cancelled event: {event.get('summary', 'Unknown')}")
                            stats["events_updated"] += 1
                        else:
                            stats["events_skipped"] += 1
                        continue

                    # Transform to Notion format
                    notion_data = self.transform_event_to_notion(
                        event, calendar_name
                    )

                    # Sync to Notion (create or update)
                    existing = notion_sync.get_event_by_external_id(notion_data["Event ID"])

                    if existing:
                        # Update existing event
                        notion_sync.update_event(existing['id'], notion_data)
                        stats["events_updated"] += 1
                    else:
                        # Create new event
                        notion_sync.create_event(notion_data)
                        stats["events_created"] += 1

                except Exception as e:
                    logger.error(
                        f"Error processing event '{event.get('summary', 'Unknown')}': {e}"
                    )
                    logger.exception("Full traceback:")
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
            logger.exception("Full traceback:")
            stats["errors"] += 1

            # Mark sync as failed in state
            if state_manager:
                state_manager.update_sync_state(
                    source=source_key,
                    success=False,
                    error=str(e)
                )

        return stats
