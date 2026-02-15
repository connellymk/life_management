"""
Obsidian export module
Exports Google Calendar events to Obsidian vault as markdown files
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


from core.utils import logger


class ObsidianExporter:
    """Handles exporting data to Obsidian vault in markdown format"""

    def __init__(self, vault_path: str, events_folder: str = "1. Life Areas/Calendar/Events"):
        """
        Initialize Obsidian exporter

        Args:
            vault_path: Path to Obsidian vault root
            events_folder: Folder within vault for calendar events
        """
        self.vault_path = Path(vault_path)
        self.events_folder = self.vault_path / events_folder

        # Create events folder if it doesn't exist
        self.events_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Obsidian exporter initialized: {self.events_folder}")

    def export_events(self, events: List[Dict[str, Any]], calendar_name: str = "Google Calendar", dry_run: bool = False) -> Dict[str, int]:
        """
        Export calendar events to Obsidian markdown files

        Args:
            events: List of event dictionaries from Google Calendar API
            calendar_name: Name of the calendar (for tagging)
            dry_run: If True, don't write files, just log what would happen

        Returns:
            Dictionary with counts: {"created": n, "updated": n, "skipped": n}
        """
        stats = {"created": 0, "updated": 0, "skipped": 0}

        for event in events:
            try:
                result = self._export_event(event, calendar_name, dry_run)
                stats[result] += 1
            except Exception as e:
                logger.error(f"Error exporting event {event.get('summary', 'Unknown')}: {e}")
                stats["skipped"] += 1

        logger.info(f"Export complete: {stats['created']} created, {stats['updated']} updated, {stats['skipped']} skipped")
        return stats

    def _export_event(self, event: Dict[str, Any], calendar_name: str, dry_run: bool) -> str:
        """
        Export a single event to markdown file

        Returns:
            "created", "updated", or "skipped"
        """
        # Extract event details
        event_id = event.get("id", "")
        summary = event.get("summary", "Untitled Event")

        # Handle all-day events vs timed events
        start = event.get("start", {})
        end = event.get("end", {})

        if "dateTime" in start:
            # Timed event
            start_dt = self._parse_datetime(start["dateTime"])
            end_dt = self._parse_datetime(end["dateTime"])
            is_all_day = False
            date_str = start_dt.strftime("%Y-%m-%d")
            time_str = start_dt.strftime("%I:%M %p")
            end_time_str = end_dt.strftime("%I:%M %p")
        else:
            # All-day event
            start_dt = datetime.strptime(start["date"], "%Y-%m-%d")
            end_dt = datetime.strptime(end["date"], "%Y-%m-%d")
            is_all_day = True
            date_str = start_dt.strftime("%Y-%m-%d")
            time_str = "All Day"
            end_time_str = ""

        # Get other details
        location = event.get("location", "")
        description = event.get("description", "")
        status = event.get("status", "confirmed").capitalize()
        recurring = event.get("recurringEventId") is not None

        # Get attendees
        attendees_list = event.get("attendees", [])
        attendees = ", ".join([a.get("email", "") for a in attendees_list])

        # Generate filename (sanitize for filesystem)
        safe_summary = self._sanitize_filename(summary)
        filename = f"{date_str} - {safe_summary}.md"
        filepath = self.events_folder / filename

        # Check if file exists
        exists = filepath.exists()

        if dry_run:
            action = "update" if exists else "create"
            logger.info(f"[DRY RUN] Would {action}: {filepath}")
            return "updated" if exists else "created"

        # Generate markdown content
        content = self._generate_event_markdown(
            summary=summary,
            date=date_str,
            time=time_str,
            end_time=end_time_str,
            calendar=calendar_name,
            location=location,
            status=status,
            recurring=recurring,
            attendees=attendees,
            description=description,
            event_id=event_id,
            is_all_day=is_all_day
        )

        # Write file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            action = "Updated" if exists else "Created"
            logger.info(f"{action} event: {filepath}")
            return "updated" if exists else "created"

        except Exception as e:
            logger.error(f"Failed to write {filepath}: {e}")
            return "skipped"

    def _generate_event_markdown(
        self,
        summary: str,
        date: str,
        time: str,
        end_time: str,
        calendar: str,
        location: str,
        status: str,
        recurring: bool,
        attendees: str,
        description: str,
        event_id: str,
        is_all_day: bool
    ) -> str:
        """Generate markdown content for an event"""

        # Build frontmatter
        frontmatter = f"""---
tags: event
date: {date}
time: {time}
calendar: {calendar}
location: {location}
status: {status}
recurring: {recurring}
all_day: {is_all_day}
event_id: {event_id}
---

"""

        # Build content
        content = f"""# {summary}

## 📅 When
**Date:** {date}
**Time:** {time}{f" - {end_time}" if end_time and not is_all_day else ""}

## 📍 Details
**Calendar:** {calendar}
**Status:** {status}
{"**Recurring:** Yes" if recurring else ""}
{"**All Day Event**" if is_all_day else ""}

"""

        if location:
            content += f"""## 🗺️ Location
{location}

"""

        if attendees:
            content += f"""## 👥 Attendees
{attendees}

"""

        if description:
            content += f"""## 📝 Description
{description}

"""

        content += """## 📝 Notes
<!-- Add your notes about this event here -->

"""

        return frontmatter + content

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility"""
        # Remove or replace problematic characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '-')

        # Limit length
        max_length = 100
        if len(filename) > max_length:
            filename = filename[:max_length]

        # Remove trailing dots and spaces
        filename = filename.rstrip('. ')

        return filename

    def _parse_datetime(self, dt_string: str) -> datetime:
        """Parse datetime string from Google Calendar API"""
        try:
            # Try parsing with timezone
            return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        except:
            # Fallback to basic parsing
            return datetime.strptime(dt_string[:19], "%Y-%m-%dT%H:%M:%S")

    def clean_old_events(self, days_old: int = 90, dry_run: bool = False) -> int:
        """
        Remove event files older than specified days

        Args:
            days_old: Remove events older than this many days
            dry_run: If True, don't delete, just log what would happen

        Returns:
            Number of files deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        deleted = 0

        for filepath in self.events_folder.glob("*.md"):
            try:
                # Extract date from filename (assumes YYYY-MM-DD prefix)
                filename = filepath.name
                date_str = filename[:10]
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                if file_date < cutoff_date:
                    if dry_run:
                        logger.info(f"[DRY RUN] Would delete old event: {filepath}")
                    else:
                        filepath.unlink()
                        logger.info(f"Deleted old event: {filepath}")
                    deleted += 1

            except Exception as e:
                logger.warning(f"Could not process {filepath}: {e}")

        logger.info(f"Cleaned {deleted} old event files")
        return deleted
