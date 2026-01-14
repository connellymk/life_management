#!/usr/bin/env python3
"""
Test authentication for all configured services
Run this script to verify that your OAuth credentials are set up correctly
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.google_sync import GoogleCalendarSync
from src.notion_sync import NotionSync
from src.utils import logger


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def test_configuration():
    """Test configuration validity"""
    print_section("Testing Configuration")

    errors = Config.validate()
    if errors:
        print("\n❌ Configuration errors found:\n")
        for error in errors:
            print(f"  ✗ {error}")
        print("\nPlease fix these errors in your .env file")
        print("See SETUP_GUIDES.md for instructions\n")
        return False
    else:
        print("\n✓ Configuration is valid\n")
        Config.print_config()
        return True


def test_google_calendar():
    """Test Google Calendar authentication"""
    print_section("Testing Google Calendar")

    try:
        sync = GoogleCalendarSync()
        print("\nAuthenticating with Google Calendar...")
        print("(A browser window will open for OAuth)")

        if not sync.authenticate():
            print("\n❌ Failed to authenticate with Google Calendar")
            print("Check the logs for details")
            return False

        print("\n✓ Successfully authenticated with Google Calendar!")

        # Try fetching a few events to verify access
        print("\nFetching sample events from primary calendar...")
        events = sync.get_calendar_events("primary", max_results=5)

        if events:
            print(f"\n✓ Found {len(events)} events (showing first 5):\n")
            for i, event in enumerate(events[:5], 1):
                title = event.get("summary", "(No title)")
                start = event.get("start", {})
                start_str = start.get("dateTime", start.get("date", "Unknown"))
                print(f"  {i}. {title}")
                print(f"     Start: {start_str}")
        else:
            print("\nℹ No events found in the configured date range")
            print("  This is normal if your calendar is empty or events are outside the sync window")

        return True

    except Exception as e:
        print(f"\n❌ Error testing Google Calendar: {e}")
        logger.exception("Google Calendar test failed")
        return False


def test_notion():
    """Test Notion API connection"""
    print_section("Testing Notion")

    try:
        sync = NotionSync()

        # Test basic connection
        print("\nTesting Notion API connection...")
        if not sync.test_connection():
            print("\n❌ Failed to connect to Notion API")
            print("Check your NOTION_TOKEN in .env file")
            return False

        print("✓ Successfully connected to Notion API!")

        # Test calendar database access
        if Config.NOTION_CALENDAR_DB_ID:
            print("\nTesting Calendar Events database access...")
            if not sync.test_database_access(Config.NOTION_CALENDAR_DB_ID):
                print("\n❌ Cannot access Calendar Events database")
                print("\nMake sure you:")
                print("  1. Created the database in Notion")
                print("  2. Shared it with your integration")
                print("  3. Copied the correct database ID to .env")
                return False

            print("✓ Calendar Events database is accessible!")

            # Get and display schema
            print("\nFetching database properties...")
            schema = sync.get_database_schema(Config.NOTION_CALENDAR_DB_ID)

            if schema:
                print(f"\n✓ Database has {len(schema)} properties:")
                expected_props = {
                    "Title", "Start Time", "End Time", "Source", "Location",
                    "Description", "External ID", "Attendees", "Last Synced",
                    "URL", "Sync Status"
                }
                found_props = set(schema.keys())

                for prop in sorted(found_props):
                    prop_type = schema[prop].get("type", "unknown")
                    status = "✓" if prop in expected_props else "ℹ"
                    print(f"  {status} {prop} ({prop_type})")

                missing = expected_props - found_props
                if missing:
                    print(f"\n⚠ Missing expected properties: {', '.join(missing)}")
                    print("  The sync may not work correctly without these properties")
                    print("  See SETUP_GUIDES.md for the complete property list")

        else:
            print("\n⚠ NOTION_CALENDAR_DB_ID not set in .env")
            print("  You'll need to set this before running the sync")

        return True

    except Exception as e:
        print(f"\n❌ Error testing Notion: {e}")
        logger.exception("Notion test failed")
        return False


def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("  Calendar Sync - Authentication Test")
    print("=" * 60)

    results = {
        "Configuration": test_configuration(),
        "Google Calendar": test_google_calendar(),
        "Notion": test_notion(),
    }

    # Summary
    print_section("Test Summary")
    print()
    all_passed = True
    for service, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {service}")
        if not passed:
            all_passed = False

    print()

    if all_passed:
        print("=" * 60)
        print("  🎉 All tests passed! You're ready to sync!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Run a dry-run sync:")
        print("     python sync_orchestrator.py --dry-run")
        print()
        print("  2. Run an actual sync:")
        print("     python sync_orchestrator.py")
        print()
        return 0
    else:
        print("=" * 60)
        print("  ❌ Some tests failed")
        print("=" * 60)
        print("\nPlease fix the errors above before proceeding")
        print("See SETUP_GUIDES.md for detailed setup instructions")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
