"""
Shared fixtures for orchestrator tests.

Pre-mocks third-party modules (google, garth, notion_client, pytz, etc.)
so that test collection succeeds without installing the full dependency tree.
"""

import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

import pytest

# ── Add project root to path ──────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Pre-mock third-party packages that integration modules import ─────────
# This must happen *before* any orchestrator (or integration) module is
# imported, because the import chain eagerly loads these packages.

_THIRD_PARTY_STUBS = [
    # Google
    "google",
    "google.auth",
    "google.auth.transport",
    "google.auth.transport.requests",
    "google.oauth2",
    "google.oauth2.credentials",
    "google_auth_oauthlib",
    "google_auth_oauthlib.flow",
    "googleapiclient",
    "googleapiclient.discovery",
    "googleapiclient.errors",
    # Garmin
    "garth",
    "garth.data",
    # Notion SDK
    "notion_client",
    # Misc
    "pytz",
    "tenacity",
    "requests",
]

for _mod_name in _THIRD_PARTY_STUBS:
    if _mod_name not in sys.modules:
        sys.modules[_mod_name] = MagicMock()


# ---------------------------------------------------------------------------
# Garmin fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_garmin():
    """Mock GarminSync client."""
    garmin = MagicMock()
    garmin.authenticate.return_value = True
    garmin.get_activities.return_value = []
    garmin.get_daily_metrics.return_value = []
    garmin.get_body_composition.return_value = []
    return garmin


@pytest.fixture
def sample_activities():
    """Sample Garmin activities for testing."""
    return [
        {
            "external_id": "garmin_12345",
            "title": "Morning Run",
            "start_time": "2026-01-15T07:00:00",
            "activity_type": "running",
            "distance": 5.0,
            "duration": 1800,
            "calories": 350,
            "avg_hr": 155,
        },
        {
            "external_id": "garmin_12346",
            "title": "Afternoon Ride",
            "start_time": "2026-01-15T16:00:00",
            "activity_type": "cycling",
            "distance": 25.0,
            "duration": 3600,
            "calories": 600,
            "avg_hr": 140,
        },
    ]


@pytest.fixture
def sample_daily_metrics():
    """Sample daily health metrics."""
    return [
        {
            "date": "2026-01-15",
            "steps": 10500,
            "sleep_hours": 7.5,
            "resting_hr": 58,
            "stress_level": 32,
            "body_battery": 75,
            "calories": 2200,
            "floors_climbed": 12,
        },
        {
            "date": "2026-01-16",
            "steps": 8200,
            "sleep_hours": 6.8,
            "resting_hr": 60,
            "stress_level": 40,
            "body_battery": 60,
            "calories": 2050,
            "floors_climbed": 8,
        },
    ]


@pytest.fixture
def sample_body_metrics():
    """Sample body composition metrics."""
    return [
        {
            "date": "2026-01-15",
            "weight": 165.0,
            "body_fat_pct": 18.5,
            "muscle_mass": 135.0,
        },
        {
            "date": "2026-01-16",
            "weight": 164.5,
            "body_fat_pct": 18.3,
            "muscle_mass": 135.2,
        },
    ]


# ---------------------------------------------------------------------------
# Notion fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_notion_activities():
    """Mock NotionActivitiesSync client."""
    notion = MagicMock()
    notion.get_activity_by_external_id.return_value = None
    notion.create_activity.return_value = {"id": "notion-page-1"}
    notion.update_activity.return_value = {"id": "notion-page-1"}
    return notion


@pytest.fixture
def mock_notion_tracking():
    """Mock NotionDailyTrackingSync client."""
    tracking = MagicMock()
    tracking.sync_daily_metrics.return_value = {"id": "notion-page-2"}
    tracking.sync_body_metrics.return_value = {"id": "notion-page-3"}
    return tracking


@pytest.fixture
def mock_notion_calendar():
    """Mock NotionCalendarSync client."""
    notion = MagicMock()
    notion.get_event_by_external_id.return_value = None
    notion.create_event.return_value = {"id": "notion-cal-page-1"}
    notion.update_event.return_value = {"id": "notion-cal-page-1"}
    notion.delete_event.return_value = True
    return notion


# ---------------------------------------------------------------------------
# State manager fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_state_manager():
    """Mock StateManager."""
    state = MagicMock()
    state.get_last_sync_time.return_value = None
    state.get_sync_token.return_value = None
    state.update_sync_state.return_value = None
    state.log_sync.return_value = None
    return state


# ---------------------------------------------------------------------------
# Google Calendar fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_google_sync():
    """Mock GoogleCalendarSync client."""
    google = MagicMock()
    google.authenticate.return_value = True
    google.sync_calendar_to_notion.return_value = {
        "calendar_name": "Personal",
        "events_fetched": 0,
        "events_created": 0,
        "events_updated": 0,
        "events_deleted": 0,
        "events_skipped": 0,
        "errors": 0,
        "incremental": False,
        "new_sync_token": None,
    }
    return google


@pytest.fixture
def sample_calendar_sync_stats():
    """Sample stats returned from sync_calendar_to_notion."""
    return {
        "calendar_name": "Personal",
        "events_fetched": 5,
        "events_created": 3,
        "events_updated": 2,
        "events_deleted": 0,
        "events_skipped": 0,
        "errors": 0,
        "incremental": True,
        "new_sync_token": "token_abc123",
    }


# ---------------------------------------------------------------------------
# Kroger fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_kroger_client():
    """Mock KrogerClient."""
    client = MagicMock()
    client.client_id = "test-client-id"
    client.client_secret = "test-client-secret"
    client.redirect_uri = "http://localhost:8000/callback"
    client.location_id = "70600170"
    client._client_token = "mock-client-token"
    client._client_token_expires = 9999999999.0
    client._user_token = "mock-user-token"
    client._user_token_expires = 9999999999.0
    client._refresh_token = "mock-refresh-token"
    client.authenticate_user.return_value = True
    client.find_locations.return_value = []
    client.search_products.return_value = []
    client.search_and_select_product.return_value = None
    client.add_to_cart.return_value = True
    return client


@pytest.fixture
def sample_kroger_locations():
    """Sample Kroger location data."""
    return [
        {
            "location_id": "70600170",
            "name": "Smith's Food & Drug",
            "chain": "SMITHS",
            "address": {
                "addressLine1": "455 S 500 E",
                "city": "Salt Lake City",
                "state": "UT",
                "zipCode": "84102",
            },
            "phone": "801-355-2411",
        },
        {
            "location_id": "70600094",
            "name": "Smith's Food & Drug",
            "chain": "SMITHS",
            "address": {
                "addressLine1": "876 E 800 S",
                "city": "Salt Lake City",
                "state": "UT",
                "zipCode": "84105",
            },
            "phone": "801-363-5434",
        },
    ]


@pytest.fixture
def sample_kroger_products():
    """Sample Kroger product search results."""
    return [
        {
            "upc": "0000000004225",
            "product_id": "0000000004225",
            "brand": "Fresh Avocados",
            "description": "Fresh Large Ripe Avocado",
            "size": "1 each",
            "price": 2.79,
            "price_display": "$2.79",
            "in_stock": True,
        },
        {
            "upc": "0001111042010",
            "product_id": "0001111042010",
            "brand": "Heritage Farm",
            "description": "Heritage Farm® Boneless Skinless Chicken Thighs",
            "size": "1 lb",
            "price": 3.99,
            "price_display": "$3.99",
            "in_stock": True,
        },
        {
            "upc": "0000000094072",
            "product_id": "0000000094072",
            "brand": "Fresh Potatoes",
            "description": "Organic Gold Jewel Sweet Potatoes",
            "size": "1 lb",
            "price": 2.79,
            "price_display": "$2.79",
            "in_stock": True,
        },
    ]


@pytest.fixture
def sample_kroger_product_out_of_stock():
    """Sample out-of-stock product."""
    return {
        "upc": "0099999999999",
        "product_id": "0099999999999",
        "brand": "Specialty Brand",
        "description": "Rare Ingredient",
        "size": "8 oz",
        "price": 12.99,
        "price_display": "$12.99",
        "in_stock": False,
    }


@pytest.fixture
def sample_kroger_api_product_response():
    """Raw Kroger API product response (before client parsing)."""
    return {
        "data": [
            {
                "productId": "0000000004225",
                "upc": "0000000004225",
                "brand": "Fresh Avocados",
                "description": "Fresh Large Ripe Avocado",
                "items": [
                    {
                        "size": "1 each",
                        "price": {"regular": 2.79, "promo": 0},
                        "fulfillment": {"curbside": True, "inStore": True},
                    }
                ],
            },
        ],
    }


@pytest.fixture
def sample_kroger_api_location_response():
    """Raw Kroger API location response (before client parsing)."""
    return {
        "data": [
            {
                "locationId": "70600170",
                "name": "Smith's Food & Drug",
                "chain": "SMITHS",
                "address": {
                    "addressLine1": "455 S 500 E",
                    "city": "Salt Lake City",
                    "state": "UT",
                    "zipCode": "84102",
                },
                "phone": "801-355-2411",
            },
        ],
    }
