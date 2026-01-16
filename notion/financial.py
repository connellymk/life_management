"""
Notion API client for syncing financial data from Plaid.
Creates and updates pages in Accounts, Transactions, Balances, Investments, and Bills databases.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from notion_client import Client
from notion_client.errors import APIResponseError

from core.config import PlaidConfig as Config
from core.state_manager import StateManager
from core.utils import setup_logging, rate_limit

logger = setup_logging("notion_financial")


class NotionFinancialSync:
    """Client for syncing financial data to Notion databases."""

    def __init__(self, state_manager: Optional[StateManager] = None):
        """
        Initialize Notion client.

        Args:
            state_manager: State manager instance (creates new if None)
        """
        self.client = Client(auth=Config.NOTION_TOKEN)
        self.state_manager = state_manager or StateManager()

        self.accounts_db_id = Config.NOTION_ACCOUNTS_DB_ID
        self.transactions_db_id = Config.NOTION_TRANSACTIONS_DB_ID
        self.balances_db_id = Config.NOTION_BALANCES_DB_ID
        self.investments_db_id = Config.NOTION_INVESTMENTS_DB_ID
        self.bills_db_id = Config.NOTION_BILLS_DB_ID

    @rate_limit(calls_per_second=3.0)
    def create_or_update_account(self, account_data: Dict[str, Any]) -> Optional[str]:
        """
        Create or update an account page in Notion.

        Args:
            account_data: Normalized account data from Plaid

        Returns:
            Notion page ID if successful, None otherwise
        """
        try:
            external_id = f"plaid_account_{account_data['account_id']}"

            # Check if already exists
            existing_page_id = self.state_manager.get_notion_page_id(external_id)
            if existing_page_id:
                return self._update_account(existing_page_id, account_data)

            # Create new account
            properties = self._build_account_properties(account_data)
            response = self.client.pages.create(
                parent={"database_id": self.accounts_db_id}, properties=properties
            )

            page_id = response["id"]
            self.state_manager.save_mapping(
                external_id, page_id, "account", f"plaid_{account_data['item_id']}"
            )

            logger.info(f"✓ Created account: {account_data['name']}")
            return page_id

        except Exception as e:
            logger.error(f"✗ Error creating account: {e}")
            return None

    def _update_account(self, page_id: str, account_data: Dict[str, Any]) -> Optional[str]:
        """Update an existing account page."""
        try:
            properties = self._build_account_properties(account_data)
            self.client.pages.update(page_id=page_id, properties=properties)

            logger.debug(f"✓ Updated account: {account_data['name']}")
            return page_id

        except Exception as e:
            logger.error(f"✗ Error updating account: {e}")
            return None

    def _build_account_properties(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build Notion properties for an account."""
        # Map Plaid account types to Notion select options
        type_map = {
            "depository": "Checking" if account_data.get("subtype") == "checking" else "Savings",
            "credit": "Credit Card",
            "loan": "Loan",
            "investment": "Investment",
            "mortgage": "Mortgage",
        }
        account_type = type_map.get(account_data["type"], "Checking")

        properties = {
            "Name": {"title": [{"text": {"content": account_data["name"]}}]},
            "Account ID": {"rich_text": [{"text": {"content": account_data["account_id"]}}]},
            "Institution": {"rich_text": [{"text": {"content": account_data.get("official_name", account_data["name"])}}]},
            "Account Type": {"select": {"name": account_type}},
            "Masked Number": {"rich_text": [{"text": {"content": account_data["masked_number"]}}]},
            "Status": {"select": {"name": "Active"}},
            "Synced At": {"date": {"start": datetime.now().isoformat()}},
        }

        # Add balances if available
        if account_data.get("current_balance") is not None:
            properties["Current Balance"] = {"number": round(account_data["current_balance"], 2)}
        if account_data.get("available_balance") is not None:
            properties["Available Balance"] = {"number": round(account_data["available_balance"], 2)}
        if account_data.get("credit_limit") is not None:
            properties["Credit Limit"] = {"number": round(account_data["credit_limit"], 2)}

        return properties

    @rate_limit(calls_per_second=3.0)
    def create_transaction(self, transaction_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a transaction page in Notion.

        Args:
            transaction_data: Normalized transaction data from Plaid

        Returns:
            Notion page ID if successful, None otherwise
        """
        try:
            external_id = f"plaid_txn_{transaction_data['transaction_id']}"

            # Check if already exists
            existing_page_id = self.state_manager.get_notion_page_id(external_id)
            if existing_page_id:
                logger.debug(f"Transaction {external_id} already exists, skipping...")
                return existing_page_id

            # Get related account page ID
            account_external_id = f"plaid_account_{transaction_data['account_id']}"
            account_page_id = self.state_manager.get_notion_page_id(account_external_id)

            if not account_page_id:
                logger.warning(
                    f"No account page found for transaction {transaction_data['name']}"
                )

            # Create transaction
            properties = self._build_transaction_properties(transaction_data, account_page_id)
            response = self.client.pages.create(
                parent={"database_id": self.transactions_db_id}, properties=properties
            )

            page_id = response["id"]
            self.state_manager.save_mapping(
                external_id, page_id, "transaction", f"plaid_{transaction_data['item_id']}"
            )

            logger.info(f"✓ Created transaction: {transaction_data['name']} (${transaction_data['amount']:.2f})")
            return page_id

        except Exception as e:
            logger.error(f"✗ Error creating transaction: {e}")
            return None

    def _build_transaction_properties(
        self, transaction_data: Dict[str, Any], account_page_id: Optional[str]
    ) -> Dict[str, Any]:
        """Build Notion properties for a transaction."""
        # Map Plaid categories to Notion multi-select
        categories = transaction_data.get("category", [])
        category_names = self._map_transaction_categories(categories)

        properties = {
            "Name": {"title": [{"text": {"content": transaction_data["name"]}}]},
            "Transaction ID": {"rich_text": [{"text": {"content": transaction_data["transaction_id"]}}]},
            "Date": {"date": {"start": transaction_data["date"].date().isoformat()}},
            "Amount": {"number": round(transaction_data["amount"], 2)},
            "Merchant": {"rich_text": [{"text": {"content": transaction_data.get("merchant_name", transaction_data["name"])}}]},
            "Pending": {"checkbox": transaction_data.get("pending", False)},
            "Payment Channel": {"select": {"name": transaction_data.get("payment_channel", "Other").title()}},
            "Synced At": {"date": {"start": datetime.now().isoformat()}},
        }

        # Add account relation if available
        if account_page_id:
            properties["Account"] = {"relation": [{"id": account_page_id}]}

        # Add categories as multi-select
        if category_names:
            properties["Category"] = {"multi_select": [{"name": cat} for cat in category_names]}

        return properties

    def _map_transaction_categories(self, plaid_categories: List[str]) -> List[str]:
        """Map Plaid categories to Notion multi-select options."""
        # Plaid categories are hierarchical, e.g., ["Food and Drink", "Restaurants"]
        # Map to our simplified categories
        category_map = {
            "Food and Drink": "Food & Drink",
            "Restaurants": "Food & Drink",
            "Groceries": "Food & Drink",
            "Shops": "Shopping",
            "General Merchandise": "Shopping",
            "Transportation": "Transport",
            "Travel": "Travel",
            "Payment": "Bills",
            "Transfer": "Transfer",
            "Income": "Income",
            "Healthcare": "Healthcare",
            "Entertainment": "Entertainment",
            "Recreation": "Entertainment",
        }

        notion_categories = []
        for cat in plaid_categories:
            mapped = category_map.get(cat)
            if mapped and mapped not in notion_categories:
                notion_categories.append(mapped)

        # Default to "Other" if no categories matched
        return notion_categories if notion_categories else ["Other"]

    @rate_limit(calls_per_second=3.0)
    def create_balance_snapshot(self, account_data: Dict[str, Any], date: datetime) -> Optional[str]:
        """
        Create a balance snapshot page in Notion.

        Args:
            account_data: Account data with current balances
            date: Date for this snapshot

        Returns:
            Notion page ID if successful, None otherwise
        """
        try:
            external_id = f"plaid_balance_{account_data['account_id']}_{date.date().isoformat()}"

            # Check if already exists
            existing_page_id = self.state_manager.get_notion_page_id(external_id)
            if existing_page_id:
                logger.debug(f"Balance snapshot {external_id} already exists, skipping...")
                return existing_page_id

            # Get related account page ID
            account_external_id = f"plaid_account_{account_data['account_id']}"
            account_page_id = self.state_manager.get_notion_page_id(account_external_id)

            # Create balance snapshot
            properties = self._build_balance_properties(account_data, account_page_id, date)
            response = self.client.pages.create(
                parent={"database_id": self.balances_db_id}, properties=properties
            )

            page_id = response["id"]
            self.state_manager.save_mapping(
                external_id, page_id, "balance", f"plaid_{account_data['item_id']}"
            )

            logger.info(
                f"✓ Created balance snapshot: {account_data['name']} - {date.date()}"
            )
            return page_id

        except Exception as e:
            logger.error(f"✗ Error creating balance snapshot: {e}")
            return None

    def _build_balance_properties(
        self, account_data: Dict[str, Any], account_page_id: Optional[str], date: datetime
    ) -> Dict[str, Any]:
        """Build Notion properties for a balance snapshot."""
        properties = {
            "Name": {"title": [{"text": {"content": f"{account_data['name']} - {date.date().isoformat()}"}}]},
            "Date": {"date": {"start": date.date().isoformat()}},
            "Synced At": {"date": {"start": datetime.now().isoformat()}},
        }

        # Add account relation if available
        if account_page_id:
            properties["Account"] = {"relation": [{"id": account_page_id}]}

        # Add balances if available
        if account_data.get("current_balance") is not None:
            properties["Current Balance"] = {"number": round(account_data["current_balance"], 2)}
        if account_data.get("available_balance") is not None:
            properties["Available Balance"] = {"number": round(account_data["available_balance"], 2)}
        if account_data.get("credit_limit") is not None:
            properties["Credit Limit"] = {"number": round(account_data["credit_limit"], 2)}

        return properties

    @rate_limit(calls_per_second=3.0)
    def create_or_update_investment(self, investment_data: Dict[str, Any]) -> Optional[str]:
        """
        Create or update an investment holding page in Notion.

        Args:
            investment_data: Normalized investment data from Plaid

        Returns:
            Notion page ID if successful, None otherwise
        """
        try:
            external_id = f"plaid_investment_{investment_data['holding_id']}"

            # Check if already exists
            existing_page_id = self.state_manager.get_notion_page_id(external_id)
            if existing_page_id:
                return self._update_investment(existing_page_id, investment_data)

            # Get related account page ID
            account_external_id = f"plaid_account_{investment_data['account_id']}"
            account_page_id = self.state_manager.get_notion_page_id(account_external_id)

            # Create investment
            properties = self._build_investment_properties(investment_data, account_page_id)
            response = self.client.pages.create(
                parent={"database_id": self.investments_db_id}, properties=properties
            )

            page_id = response["id"]
            self.state_manager.save_mapping(
                external_id, page_id, "investment", f"plaid_{investment_data['item_id']}"
            )

            logger.info(f"✓ Created investment: {investment_data['name']}")
            return page_id

        except Exception as e:
            logger.error(f"✗ Error creating investment: {e}")
            return None

    def _update_investment(self, page_id: str, investment_data: Dict[str, Any]) -> Optional[str]:
        """Update an existing investment holding page."""
        try:
            account_external_id = f"plaid_account_{investment_data['account_id']}"
            account_page_id = self.state_manager.get_notion_page_id(account_external_id)

            properties = self._build_investment_properties(investment_data, account_page_id)
            self.client.pages.update(page_id=page_id, properties=properties)

            logger.debug(f"✓ Updated investment: {investment_data['name']}")
            return page_id

        except Exception as e:
            logger.error(f"✗ Error updating investment: {e}")
            return None

    def _build_investment_properties(
        self, investment_data: Dict[str, Any], account_page_id: Optional[str]
    ) -> Dict[str, Any]:
        """Build Notion properties for an investment holding."""
        # Map Plaid security types to Notion select options
        type_map = {
            "equity": "Stock",
            "etf": "ETF",
            "mutual fund": "Mutual Fund",
            "bond": "Bond",
            "cash": "Cash",
        }
        asset_type = type_map.get(investment_data.get("type", "").lower(), "Other")

        properties = {
            "Name": {"title": [{"text": {"content": investment_data["name"]}}]},
            "Holding ID": {"rich_text": [{"text": {"content": investment_data["holding_id"]}}]},
            "Ticker Symbol": {"rich_text": [{"text": {"content": investment_data.get("ticker", "")}}]},
            "Asset Type": {"select": {"name": asset_type}},
            "Quantity": {"number": round(investment_data.get("quantity", 0), 4)},
            "Price Per Share": {"number": round(investment_data.get("price", 0), 2)},
            "Total Value": {"number": round(investment_data.get("value", 0), 2)},
            "Date": {"date": {"start": datetime.now().date().isoformat()}},
            "Synced At": {"date": {"start": datetime.now().isoformat()}},
        }

        # Add account relation if available
        if account_page_id:
            properties["Account"] = {"relation": [{"id": account_page_id}]}

        # Add cost basis and gains if available
        if investment_data.get("cost_basis") is not None:
            properties["Cost Basis"] = {"number": round(investment_data["cost_basis"], 2)}
        if investment_data.get("gain_loss") is not None:
            properties["Gain/Loss"] = {"number": round(investment_data["gain_loss"], 2)}
        if investment_data.get("gain_loss_pct") is not None:
            properties["Gain/Loss %"] = {"number": round(investment_data["gain_loss_pct"], 2)}

        return properties

    def get_account_count(self) -> int:
        """Get count of accounts in Notion database."""
        try:
            response = self.client.databases.query(database_id=self.accounts_db_id)
            return len(response.get("results", []))
        except Exception as e:
            logger.error(f"Error getting account count: {e}")
            return 0

    def get_transaction_count(self) -> int:
        """Get count of transactions in Notion database."""
        try:
            response = self.client.databases.query(database_id=self.transactions_db_id)
            return len(response.get("results", []))
        except Exception as e:
            logger.error(f"Error getting transaction count: {e}")
            return 0
