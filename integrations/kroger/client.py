"""
Kroger API client for product search and cart management.
Supports all Kroger-family stores (Smith's, Ralphs, Fred Meyer, etc.)
via the unified Kroger API at api.kroger.com.

Authentication uses OAuth 2.0:
  - Client Credentials grant for public data (product search, locations)
  - Authorization Code grant with PKCE for user-specific operations (cart)
"""

import base64
import hashlib
import json
import os
import secrets
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode, urlparse, parse_qs

import requests

from core.config import KrogerConfig as Config
from core.utils import setup_logging, retry_with_backoff

logger = setup_logging("kroger_client")

BASE_URL = "https://api.kroger.com/v1"
TOKEN_URL = f"{BASE_URL}/connect/oauth2/token"
AUTHORIZE_URL = f"{BASE_URL}/connect/oauth2/authorize"


class KrogerClient:
    """Client for the Kroger public API (product search, locations, cart)."""

    def __init__(self):
        """Initialize Kroger API client."""
        self.client_id = Config.KROGER_CLIENT_ID
        self.client_secret = Config.KROGER_CLIENT_SECRET
        self.redirect_uri = Config.KROGER_REDIRECT_URI
        self.location_id = Config.KROGER_LOCATION_ID

        self._tokens_path = Path(__file__).parent.parent.parent / "credentials" / "kroger_tokens.json"
        self._tokens_path.parent.mkdir(exist_ok=True)

        self._client_token: Optional[str] = None
        self._client_token_expires: float = 0

        self._user_token: Optional[str] = None
        self._user_token_expires: float = 0
        self._refresh_token: Optional[str] = None

        self._load_tokens()

    # ── Token persistence ──────────────────────────────────────────────

    def _load_tokens(self):
        """Load cached user tokens from disk."""
        if self._tokens_path.exists():
            try:
                data = json.loads(self._tokens_path.read_text())
                self._refresh_token = data.get("refresh_token")
                self._user_token = data.get("access_token")
                self._user_token_expires = data.get("expires_at", 0)
                if self._user_token and time.time() < self._user_token_expires:
                    logger.info("Loaded cached Kroger user tokens")
                elif self._refresh_token:
                    logger.info("Cached Kroger access token expired, will refresh")
                    self._user_token = None
            except Exception as e:
                logger.warning(f"Could not load cached Kroger tokens: {e}")

    def _save_tokens(self):
        """Persist user tokens to disk."""
        data = {
            "access_token": self._user_token,
            "refresh_token": self._refresh_token,
            "expires_at": self._user_token_expires,
        }
        self._tokens_path.write_text(json.dumps(data, indent=2))

    # ── Client Credentials (public data) ───────────────────────────────

    def _get_basic_auth(self) -> str:
        """Return Base64-encoded client_id:client_secret."""
        pair = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(pair.encode()).decode()

    @retry_with_backoff(max_retries=2, exceptions=(requests.RequestException,))
    def _ensure_client_token(self):
        """Obtain or refresh the client credentials token."""
        if self._client_token and time.time() < self._client_token_expires:
            return

        logger.info("Requesting Kroger client credentials token...")
        resp = requests.post(
            TOKEN_URL,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {self._get_basic_auth()}",
            },
            data={"grant_type": "client_credentials", "scope": "product.compact"},
        )
        resp.raise_for_status()
        body = resp.json()

        self._client_token = body["access_token"]
        self._client_token_expires = time.time() + body.get("expires_in", 1800) - 60
        logger.info("+ Kroger client token obtained")

    # ── Authorization Code + PKCE (user-specific) ──────────────────────

    @staticmethod
    def _generate_pkce() -> tuple[str, str]:
        """Generate PKCE code_verifier and code_challenge (S256)."""
        verifier = secrets.token_urlsafe(64)
        digest = hashlib.sha256(verifier.encode()).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        return verifier, challenge

    def authenticate_user(self) -> bool:
        """
        Run the full OAuth 2.0 Authorization Code + PKCE flow.
        Opens a browser for user consent and listens on a local redirect URI.

        Returns:
            True if authentication succeeded.
        """
        # If we already have a valid user token, skip
        if self._user_token and time.time() < self._user_token_expires:
            return True

        # Try refreshing first
        if self._refresh_token:
            if self._refresh_user_token():
                return True

        # Full auth flow
        verifier, challenge = self._generate_pkce()
        state = secrets.token_urlsafe(16)

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "cart.basic:write profile.compact product.compact",
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        auth_url = f"{AUTHORIZE_URL}?{urlencode(params)}"

        # Parse redirect URI to get port
        parsed = urlparse(self.redirect_uri)
        port = parsed.port or 8000

        # Start local server to capture the callback
        auth_code = [None]
        received_state = [None]

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                qs = parse_qs(urlparse(self.path).query)
                auth_code[0] = qs.get("code", [None])[0]
                received_state[0] = qs.get("state", [None])[0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<html><body><h2>Kroger authorization complete.</h2>"
                    b"<p>You can close this tab.</p></body></html>"
                )

            def log_message(self, format, *args):
                pass  # silence request logs

        server = HTTPServer(("127.0.0.1", port), CallbackHandler)

        logger.info("Opening browser for Kroger authorization...")
        print(f"\nOpening browser for Kroger login.\nIf it doesn't open, visit:\n{auth_url}\n")
        webbrowser.open(auth_url)

        # Wait for single callback
        server.handle_request()
        server.server_close()

        if not auth_code[0]:
            logger.error("No authorization code received")
            return False
        if received_state[0] != state:
            logger.error("State mismatch in OAuth callback")
            return False

        # Exchange code for tokens
        return self._exchange_code(auth_code[0], verifier)

    def _exchange_code(self, code: str, verifier: str) -> bool:
        """Exchange authorization code for access + refresh tokens."""
        try:
            resp = requests.post(
                TOKEN_URL,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {self._get_basic_auth()}",
                },
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "code_verifier": verifier,
                },
            )
            resp.raise_for_status()
            body = resp.json()

            self._user_token = body["access_token"]
            self._user_token_expires = time.time() + body.get("expires_in", 1800) - 60
            self._refresh_token = body.get("refresh_token")
            self._save_tokens()

            logger.info("+ Kroger user authentication successful")
            return True

        except Exception as e:
            logger.error(f"Failed to exchange authorization code: {e}")
            return False

    def _refresh_user_token(self) -> bool:
        """Refresh the user access token using the refresh token."""
        if not self._refresh_token:
            return False

        try:
            logger.info("Refreshing Kroger user token...")
            resp = requests.post(
                TOKEN_URL,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {self._get_basic_auth()}",
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                },
            )
            resp.raise_for_status()
            body = resp.json()

            self._user_token = body["access_token"]
            self._user_token_expires = time.time() + body.get("expires_in", 1800) - 60
            self._refresh_token = body.get("refresh_token", self._refresh_token)
            self._save_tokens()

            logger.info("+ Kroger user token refreshed")
            return True

        except Exception as e:
            logger.warning(f"Token refresh failed, will need re-authorization: {e}")
            self._refresh_token = None
            self._save_tokens()
            return False

    # ── Locations API ──────────────────────────────────────────────────

    @retry_with_backoff(max_retries=2, exceptions=(requests.RequestException,))
    def find_locations(
        self,
        zip_code: str,
        chain: str = "SMITHS",
        radius_miles: int = 10,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search for Kroger-family store locations.

        Args:
            zip_code: ZIP code to search near.
            chain: Store chain filter (SMITHS, KROGER, RALPHS, etc.).
            radius_miles: Search radius in miles.
            limit: Maximum results.

        Returns:
            List of location dictionaries.
        """
        self._ensure_client_token()

        params = {
            "filter.zipCode.near": zip_code,
            "filter.chain": chain,
            "filter.radiusInMiles": radius_miles,
            "filter.limit": limit,
        }

        resp = requests.get(
            f"{BASE_URL}/locations",
            headers={"Authorization": f"Bearer {self._client_token}"},
            params=params,
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])

        locations = []
        for loc in data:
            locations.append({
                "location_id": loc.get("locationId"),
                "name": loc.get("name"),
                "chain": loc.get("chain"),
                "address": loc.get("address", {}),
                "phone": loc.get("phone"),
            })

        logger.info(f"Found {len(locations)} {chain} locations near {zip_code}")
        return locations

    # ── Product Search API ─────────────────────────────────────────────

    @retry_with_backoff(max_retries=2, exceptions=(requests.RequestException,))
    def search_products(
        self,
        term: str,
        location_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for products at a specific store location.

        Args:
            term: Search keyword (e.g., "avocado", "chicken thighs").
            location_id: Store location ID (defaults to configured location).
            limit: Maximum results (1-50).

        Returns:
            List of product dictionaries with UPC, name, price, etc.
        """
        self._ensure_client_token()
        loc = location_id or self.location_id

        params = {
            "filter.term": term,
            "filter.limit": min(limit, 50),
        }
        if loc:
            params["filter.locationId"] = loc

        resp = requests.get(
            f"{BASE_URL}/products",
            headers={"Authorization": f"Bearer {self._client_token}"},
            params=params,
        )
        resp.raise_for_status()
        raw_products = resp.json().get("data", [])

        products = []
        for p in raw_products:
            # Extract price from items (first available)
            price = None
            price_str = None
            items = p.get("items", [])
            if items:
                price_info = items[0].get("price", {})
                price = price_info.get("regular")
                promo = price_info.get("promo")
                if promo and promo > 0:
                    price_str = f"${promo:.2f} (reg ${price:.2f})" if price else f"${promo:.2f}"
                elif price:
                    price_str = f"${price:.2f}"

            # Extract size info
            size = None
            if items:
                size = items[0].get("size")

            products.append({
                "upc": p.get("upc"),
                "product_id": p.get("productId"),
                "brand": p.get("brand"),
                "description": p.get("description"),
                "size": size,
                "price": price,
                "price_display": price_str,
                "in_stock": any(
                    item.get("fulfillment", {}).get("curbside", False)
                    or item.get("fulfillment", {}).get("inStore", False)
                    for item in items
                ),
            })

        return products

    # ── Cart API ───────────────────────────────────────────────────────

    @retry_with_backoff(max_retries=2, exceptions=(requests.RequestException,))
    def add_to_cart(self, items: List[Dict[str, Any]]) -> bool:
        """
        Add items to the authenticated user's cart.

        Args:
            items: List of dicts with "upc" (str) and "quantity" (int).
                   Example: [{"upc": "0001111042010", "quantity": 2}]

        Returns:
            True if items were added successfully.
        """
        if not self._user_token or time.time() >= self._user_token_expires:
            if not self.authenticate_user():
                logger.error("Cannot add to cart: user not authenticated")
                return False

        resp = requests.put(
            f"{BASE_URL}/cart/add",
            headers={
                "Authorization": f"Bearer {self._user_token}",
                "Content-Type": "application/json",
            },
            json={"items": items},
        )
        resp.raise_for_status()
        logger.info(f"+ Added {len(items)} item(s) to Kroger cart")
        return True

    # ── High-level helpers ─────────────────────────────────────────────

    def search_and_select_product(
        self,
        term: str,
        location_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Search for a product and return the best match.
        Prefers in-stock items and picks the first result.

        Args:
            term: Search keyword.
            location_id: Optional store location.

        Returns:
            Best-match product dict, or None.
        """
        products = self.search_products(term, location_id=location_id, limit=5)
        if not products:
            return None

        # Prefer in-stock products
        in_stock = [p for p in products if p.get("in_stock")]
        return in_stock[0] if in_stock else products[0]
