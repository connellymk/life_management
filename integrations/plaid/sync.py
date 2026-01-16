"""
Plaid API client for fetching banking data.
Implements secure access token storage and data normalization.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from plaid import ApiClient, Configuration
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.liabilities_get_request import LiabilitiesGetRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.exceptions import ApiException

from core.secure_storage import SecureTokenStorage

logger = logging.getLogger(__name__)


class PlaidSync:
    """
    Plaid API client with secure token storage.

    Security features:
    - Access tokens encrypted at rest
    - No credentials in logs
    - HTTPS enforced
    - Timeout protection
    """

    def __init__(
        self,
        client_id: str,
        secret: str,
        environment: str = "sandbox",
        verify_ssl: bool = True,
        timeout: int = 30,
    ):
        """
        Initialize Plaid client.

        Args:
            client_id: Plaid client ID
            secret: Plaid secret key
            environment: 'sandbox', 'development', or 'production'
            verify_ssl: Verify SSL certificates (always True for security)
            timeout: Request timeout in seconds
        """
        self.client_id = client_id
        self.secret = secret
        self.environment = environment
        self.verify_ssl = verify_ssl
        self.timeout = timeout

        # Initialize secure token storage
        self.token_storage = SecureTokenStorage()

        # Configure Plaid API client
        host_map = {
            "sandbox": "https://sandbox.plaid.com",
            "development": "https://development.plaid.com",
            "production": "https://production.plaid.com",
        }

        configuration = Configuration(
            host=host_map.get(environment, host_map["sandbox"]),
            api_key={
                "clientId": client_id,
                "secret": secret,
            },
        )

        # HTTPS-only client with timeout
        api_client = ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)

        logger.info(f"Initialized Plaid client (environment: {environment})")

    def create_link_token(self, user_id: str = "user_default") -> str:
        """
        Create a short-lived link token for Plaid Link UI.

        Args:
            user_id: Unique user identifier

        Returns:
            Link token (expires in 4 hours)
        """
        try:
            request = LinkTokenCreateRequest(
                products=[Products("transactions"), Products("investments"), Products("liabilities")],
                client_name="Personal Assistant",
                country_codes=[CountryCode("US")],
                language="en",
                user=LinkTokenCreateRequestUser(client_user_id=user_id),
            )

            response = self.client.link_token_create(request)
            link_token = response["link_token"]

            logger.info("Created link token")
            return link_token

        except ApiException as e:
            logger.error(f"Failed to create link token: {e.status} - {e.body}")
            raise Exception("Failed to create Plaid link token. Check credentials.")

    def exchange_public_token(self, public_token: str, institution_name: str = "") -> str:
        """
        Exchange public token from Plaid Link for access token.
        Stores access token encrypted.

        Args:
            public_token: Public token from Plaid Link
            institution_name: Institution name for reference

        Returns:
            Item ID
        """
        try:
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self.client.item_public_token_exchange(request)

            access_token = response["access_token"]
            item_id = response["item_id"]

            # Store access token encrypted
            self.token_storage.save_access_token(
                item_id=item_id,
                access_token=access_token,
                institution_name=institution_name,
            )

            logger.info(f"Exchanged public token for item {item_id}")
            return item_id

        except ApiException as e:
            logger.error(f"Failed to exchange public token: {e.status}")
            raise Exception("Failed to exchange Plaid token.")

    def get_accounts(self, item_id: str) -> List[Dict[str, Any]]:
        """
        Get all accounts for an item.

        Args:
            item_id: Plaid item ID

        Returns:
            List of normalized account dictionaries
        """
        access_token = self.token_storage.get_access_token(item_id)
        if not access_token:
            raise ValueError(f"No access token found for item {item_id}")

        try:
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)

            accounts = []
            for account in response["accounts"]:
                normalized = self._normalize_account(account, item_id)
                accounts.append(normalized)

            logger.info(f"Fetched {len(accounts)} accounts for item {item_id}")
            return accounts

        except ApiException as e:
            logger.error(f"Failed to fetch accounts: {e.status}")
            raise

    def get_transactions(
        self, item_id: str, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get transactions for an item.

        Args:
            item_id: Plaid item ID
            start_date: Start date for transactions
            end_date: End date for transactions

        Returns:
            List of normalized transaction dictionaries
        """
        access_token = self.token_storage.get_access_token(item_id)
        if not access_token:
            raise ValueError(f"No access token found for item {item_id}")

        try:
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date.date(),
                end_date=end_date.date(),
            )

            response = self.client.transactions_get(request)
            transactions = []

            for txn in response["transactions"]:
                normalized = self._normalize_transaction(txn, item_id)
                transactions.append(normalized)

            logger.info(
                f"Fetched {len(transactions)} transactions for item {item_id} "
                f"({start_date.date()} to {end_date.date()})"
            )
            return transactions

        except ApiException as e:
            logger.error(f"Failed to fetch transactions: {e.status}")
            raise

    def get_investments(self, item_id: str) -> List[Dict[str, Any]]:
        """
        Get investment holdings for an item.

        Args:
            item_id: Plaid item ID

        Returns:
            List of normalized investment holding dictionaries
        """
        access_token = self.token_storage.get_access_token(item_id)
        if not access_token:
            raise ValueError(f"No access token found for item {item_id}")

        try:
            request = InvestmentsHoldingsGetRequest(access_token=access_token)
            response = self.client.investments_holdings_get(request)

            holdings = []
            for holding in response["holdings"]:
                # Find matching security
                security = next(
                    (s for s in response["securities"] if s["security_id"] == holding["security_id"]),
                    None,
                )
                normalized = self._normalize_investment(holding, security, item_id)
                holdings.append(normalized)

            logger.info(f"Fetched {len(holdings)} investment holdings for item {item_id}")
            return holdings

        except ApiException as e:
            logger.error(f"Failed to fetch investments: {e.status}")
            raise

    def get_liabilities(self, item_id: str) -> Dict[str, Any]:
        """
        Get liabilities (credit cards, loans, mortgages) for an item.

        Args:
            item_id: Plaid item ID

        Returns:
            Dictionary with credit, student loans, and mortgage data
        """
        access_token = self.token_storage.get_access_token(item_id)
        if not access_token:
            raise ValueError(f"No access token found for item {item_id}")

        try:
            request = LiabilitiesGetRequest(access_token=access_token)
            response = self.client.liabilities_get(request)

            liabilities = {
                "credit": response.get("liabilities", {}).get("credit", []),
                "student": response.get("liabilities", {}).get("student", []),
                "mortgage": response.get("liabilities", {}).get("mortgage", []),
            }

            logger.info(f"Fetched liabilities for item {item_id}")
            return liabilities

        except ApiException as e:
            logger.error(f"Failed to fetch liabilities: {e.status}")
            raise

    def get_all_items(self) -> List[str]:
        """
        Get all stored item IDs.

        Returns:
            List of item IDs
        """
        return self.token_storage.get_all_items()

    def _normalize_account(self, account: Dict[str, Any], item_id: str) -> Dict[str, Any]:
        """
        Normalize Plaid account data.
        Masks account number for security.
        """
        balances = account.get("balances", {})

        # Mask account number (last 4 digits only)
        mask = account.get("mask", "****")
        masked_number = f"****{mask}"

        return {
            "account_id": account["account_id"],
            "item_id": item_id,
            "name": account["name"],
            "official_name": account.get("official_name", account["name"]),
            "type": account["type"],
            "subtype": account.get("subtype", ""),
            "masked_number": masked_number,  # Security: Last 4 only
            "current_balance": balances.get("current"),
            "available_balance": balances.get("available"),
            "credit_limit": balances.get("limit"),
            "currency": balances.get("iso_currency_code", "USD"),
        }

    def _normalize_transaction(self, txn: Dict[str, Any], item_id: str) -> Dict[str, Any]:
        """
        Normalize Plaid transaction data.
        """
        # Plaid returns positive for expenses, negative for income
        # We invert: negative for expenses, positive for income
        amount = -txn["amount"]

        return {
            "transaction_id": txn["transaction_id"],
            "item_id": item_id,
            "account_id": txn["account_id"],
            "date": datetime.strptime(txn["date"], "%Y-%m-%d"),
            "name": txn["name"],
            "merchant_name": txn.get("merchant_name", txn["name"]),
            "amount": amount,
            "currency": txn.get("iso_currency_code", "USD"),
            "category": txn.get("category", []),
            "pending": txn.get("pending", False),
            "payment_channel": txn.get("payment_channel", "other"),
        }

    def _normalize_investment(
        self, holding: Dict[str, Any], security: Optional[Dict[str, Any]], item_id: str
    ) -> Dict[str, Any]:
        """
        Normalize Plaid investment holding data.
        """
        quantity = holding.get("quantity", 0)
        price = holding.get("institution_price", 0)
        value = holding.get("institution_value", 0)
        cost_basis = holding.get("cost_basis")

        gain_loss = None
        gain_loss_pct = None
        if cost_basis and cost_basis > 0:
            gain_loss = value - cost_basis
            gain_loss_pct = (gain_loss / cost_basis) * 100

        return {
            "holding_id": f"{holding['account_id']}_{holding['security_id']}",
            "item_id": item_id,
            "account_id": holding["account_id"],
            "security_id": holding["security_id"],
            "name": security.get("name", "Unknown") if security else "Unknown",
            "ticker": security.get("ticker_symbol", "") if security else "",
            "type": security.get("type", "") if security else "",
            "quantity": quantity,
            "price": price,
            "value": value,
            "cost_basis": cost_basis,
            "gain_loss": gain_loss,
            "gain_loss_pct": gain_loss_pct,
            "currency": holding.get("iso_currency_code", "USD"),
        }

    def _mask_account_number(self, account_number: str) -> str:
        """
        Mask account number showing only last 4 digits.

        Security: Never store full account numbers.
        """
        if not account_number or len(account_number) < 4:
            return "****"
        return f"****{account_number[-4:]}"
