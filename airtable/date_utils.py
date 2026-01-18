"""
Date conversion utilities for Airtable Day/Week table integration.

Provides helper functions to convert between Python datetime objects
and Airtable Day/Week table ID formats.
"""

from datetime import datetime, timedelta
import platform


def date_to_day_id(date_obj) -> str:
    """
    Convert a date object to Day table ID format (m/d/yy - US format).

    Args:
        date_obj: datetime object, date object, or ISO date string

    Returns:
        str: Date in m/d/yy format (e.g., "1/17/26" for Jan 17, 2026)

    Examples:
        >>> from datetime import datetime
        >>> date_to_day_id(datetime(2026, 1, 17))
        '1/17/26'
        >>> date_to_day_id("2026-01-17")
        '1/17/26'
    """
    if isinstance(date_obj, str):
        # Handle ISO format strings
        date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))

    # Platform-specific formatting (Windows uses # instead of -)
    # US format: month/day/year
    if platform.system() == "Windows":
        return date_obj.strftime("%#m/%#d/%y")
    else:
        return date_obj.strftime("%-m/%-d/%y")


def date_to_week_id(date_obj) -> str:
    """
    Convert a date object to Week table ID format (W-YY).

    Args:
        date_obj: datetime object, date object, or ISO date string

    Returns:
        str: Week in W-YY format (e.g., "2-26" for week 2 of 2026)

    Examples:
        >>> from datetime import datetime
        >>> date_to_week_id(datetime(2026, 1, 12))  # Week 2 of 2026
        '2-26'
        >>> date_to_week_id("2026-01-12")
        '2-26'
    """
    if isinstance(date_obj, str):
        # Handle ISO format strings
        date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))

    week_num = date_obj.isocalendar()[1]  # ISO week number
    year = date_obj.strftime("%y")  # Two-digit year

    return f"{week_num}-{year}"


def get_week_starting_monday(date_obj) -> datetime:
    """
    Get the Monday of the week for a given date.

    Args:
        date_obj: datetime object, date object, or ISO date string

    Returns:
        datetime: Monday of the week containing the given date

    Examples:
        >>> from datetime import datetime
        >>> get_week_starting_monday(datetime(2026, 1, 17))  # Saturday
        datetime.datetime(2026, 1, 12, 0, 0)  # Previous Monday
    """
    if isinstance(date_obj, str):
        # Handle ISO format strings
        date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))

    # Get the Monday of the week (weekday: 0=Monday, 6=Sunday)
    days_since_monday = date_obj.weekday()
    monday = date_obj - timedelta(days=days_since_monday)

    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def day_id_to_date(day_id: str) -> datetime:
    """
    Convert a Day table ID back to a datetime object.

    Args:
        day_id: Day ID in m/d/yy format (e.g., "1/17/26")

    Returns:
        datetime: Date object

    Examples:
        >>> day_id_to_date("1/17/26")
        datetime.datetime(2026, 1, 17, 0, 0)
    """
    return datetime.strptime(day_id, "%m/%d/%y")


def week_id_to_date(week_id: str) -> datetime:
    """
    Convert a Week table ID to the Monday of that week.

    Args:
        week_id: Week ID in W-YY format (e.g., "2-26")

    Returns:
        datetime: Monday of the week

    Examples:
        >>> week_id_to_date("2-26")
        datetime.datetime(2026, 1, 12, 0, 0)
    """
    week_num, year = week_id.split("-")
    week_num = int(week_num)
    year = int(f"20{year}")  # Convert to 4-digit year

    # Get January 4th of the year (always in week 1)
    jan_4 = datetime(year, 1, 4)

    # Calculate the Monday of week 1
    week_1_monday = jan_4 - timedelta(days=jan_4.weekday())

    # Calculate the Monday of the target week
    target_monday = week_1_monday + timedelta(weeks=week_num - 1)

    return target_monday


def format_airtable_datetime(dt: datetime) -> str:
    """
    Format a datetime object for Airtable date/time fields.

    Args:
        dt: datetime object

    Returns:
        str: ISO 8601 formatted string

    Examples:
        >>> from datetime import datetime
        >>> format_airtable_datetime(datetime(2026, 1, 17, 14, 30))
        '2026-01-17T14:30:00'
    """
    return dt.isoformat()
