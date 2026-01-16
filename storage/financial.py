"""
Financial data storage operations for SQL database.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date

from core.database import Database

logger = logging.getLogger(__name__)


class FinancialStorage:
    """
    Storage operations for financial data.

    Handles CRUD operations for:
    - Accounts
    - Transactions
    - Balances
    - Investments
    - Bills
    """

    def __init__(self, database: Database):
        """
        Initialize financial storage.

        Args:
            database: Database instance
        """
        self.db = database

    # ==================== ACCOUNTS ====================

    def save_account(self, account_data: Dict[str, Any]) -> bool:
        """
        Save or update an account.

        Args:
            account_data: Normalized account data from Plaid

        Returns:
            True if successful
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO accounts (
                        account_id, item_id, name, official_name, type, subtype,
                        masked_number, institution_name, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(account_id) DO UPDATE SET
                        name = excluded.name,
                        official_name = excluded.official_name,
                        type = excluded.type,
                        subtype = excluded.subtype,
                        masked_number = excluded.masked_number,
                        institution_name = excluded.institution_name,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    account_data['account_id'],
                    account_data['item_id'],
                    account_data['name'],
                    account_data.get('official_name', account_data['name']),
                    account_data['type'],
                    account_data.get('subtype', ''),
                    account_data['masked_number'],
                    account_data.get('official_name', account_data['name'])
                ))

            logger.debug(f"Saved account: {account_data['name']}")
            return True

        except Exception as e:
            logger.error(f"Error saving account: {e}")
            return False

    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get account by ID."""
        query = "SELECT * FROM accounts WHERE account_id = ?"
        results = self.db.execute_query(query, (account_id,))
        return results[0] if results else None

    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Get all accounts."""
        return self.db.execute_query("SELECT * FROM accounts ORDER BY name")

    # ==================== TRANSACTIONS ====================

    def save_transaction(self, txn_data: Dict[str, Any]) -> bool:
        """
        Save a transaction (skips if already exists).

        Args:
            txn_data: Normalized transaction data from Plaid

        Returns:
            True if successful
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Extract primary and detailed categories
                categories = txn_data.get('category', [])
                category_primary = categories[0] if categories else None
                category_detailed = categories[1] if len(categories) > 1 else None

                cursor.execute("""
                    INSERT OR IGNORE INTO transactions (
                        transaction_id, account_id, item_id, date, amount, name,
                        merchant_name, category_primary, category_detailed,
                        pending, payment_channel, iso_currency_code
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    txn_data['transaction_id'],
                    txn_data['account_id'],
                    txn_data['item_id'],
                    txn_data['date'].date() if isinstance(txn_data['date'], datetime) else txn_data['date'],
                    txn_data['amount'],
                    txn_data['name'],
                    txn_data.get('merchant_name', txn_data['name']),
                    category_primary,
                    category_detailed,
                    txn_data.get('pending', False),
                    txn_data.get('payment_channel', 'other'),
                    txn_data.get('currency', 'USD')
                ))

            if cursor.rowcount > 0:
                logger.debug(f"Saved transaction: {txn_data['name']} (${txn_data['amount']:.2f})")
            return True

        except Exception as e:
            logger.error(f"Error saving transaction: {e}")
            return False

    def get_transactions(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        account_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get transactions with optional filters.

        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            account_id: Filter by account
            limit: Maximum results

        Returns:
            List of transaction dictionaries
        """
        query = "SELECT * FROM transactions WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        if account_id:
            query += " AND account_id = ?"
            params.append(account_id)

        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)

        return self.db.execute_query(query, tuple(params))

    def get_transaction_count(self, account_id: Optional[str] = None) -> int:
        """Get total transaction count."""
        query = "SELECT COUNT(*) as count FROM transactions"
        params = ()

        if account_id:
            query += " WHERE account_id = ?"
            params = (account_id,)

        result = self.db.execute_query(query, params)
        return result[0]['count'] if result else 0

    # ==================== BALANCES ====================

    def save_balance(self, account_id: str, balance_data: Dict[str, Any], snapshot_date: date) -> bool:
        """
        Save a balance snapshot.

        Args:
            account_id: Account ID
            balance_data: Account data with balances
            snapshot_date: Date for this snapshot

        Returns:
            True if successful
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO balances (
                        account_id, date, current_balance, available_balance, credit_limit
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(account_id, date) DO UPDATE SET
                        current_balance = excluded.current_balance,
                        available_balance = excluded.available_balance,
                        credit_limit = excluded.credit_limit
                """, (
                    account_id,
                    snapshot_date,
                    balance_data.get('current_balance'),
                    balance_data.get('available_balance'),
                    balance_data.get('credit_limit')
                ))

            logger.debug(f"Saved balance snapshot for account {account_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving balance: {e}")
            return False

    def get_balances(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        account_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get balance snapshots with optional filters."""
        query = "SELECT * FROM balances WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        if account_id:
            query += " AND account_id = ?"
            params.append(account_id)

        query += " ORDER BY date DESC"

        return self.db.execute_query(query, tuple(params))

    def get_net_worth(self, snapshot_date: Optional[date] = None) -> float:
        """
        Calculate net worth for a specific date.

        Args:
            snapshot_date: Date to calculate (defaults to latest)

        Returns:
            Net worth (sum of all account balances)
        """
        if snapshot_date:
            query = """
                SELECT SUM(current_balance) as net_worth
                FROM balances
                WHERE date = ?
            """
            params = (snapshot_date,)
        else:
            # Get latest date for each account
            query = """
                SELECT SUM(b.current_balance) as net_worth
                FROM balances b
                INNER JOIN (
                    SELECT account_id, MAX(date) as max_date
                    FROM balances
                    GROUP BY account_id
                ) latest ON b.account_id = latest.account_id AND b.date = latest.max_date
            """
            params = ()

        result = self.db.execute_query(query, params)
        return result[0]['net_worth'] if result and result[0]['net_worth'] else 0.0

    # ==================== INVESTMENTS ====================

    def save_investment(self, investment_data: Dict[str, Any], snapshot_date: date) -> bool:
        """
        Save an investment holding snapshot.

        Args:
            investment_data: Normalized investment data from Plaid
            snapshot_date: Date for this snapshot

        Returns:
            True if successful
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO investments (
                        holding_id, account_id, security_id, name, ticker, type,
                        quantity, price, value, cost_basis, date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(holding_id, date) DO UPDATE SET
                        quantity = excluded.quantity,
                        price = excluded.price,
                        value = excluded.value,
                        cost_basis = excluded.cost_basis
                """, (
                    investment_data['holding_id'],
                    investment_data['account_id'],
                    investment_data['security_id'],
                    investment_data['name'],
                    investment_data.get('ticker', ''),
                    investment_data.get('type', ''),
                    investment_data.get('quantity', 0),
                    investment_data.get('price', 0),
                    investment_data.get('value', 0),
                    investment_data.get('cost_basis'),
                    snapshot_date
                ))

            logger.debug(f"Saved investment: {investment_data['name']}")
            return True

        except Exception as e:
            logger.error(f"Error saving investment: {e}")
            return False

    def get_investments(
        self,
        snapshot_date: Optional[date] = None,
        account_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get investment holdings.

        Args:
            snapshot_date: Date to get (defaults to latest)
            account_id: Filter by account

        Returns:
            List of investment dictionaries with gain/loss calculated
        """
        if snapshot_date:
            query = "SELECT * FROM investments WHERE date = ?"
            params = [snapshot_date]
        else:
            # Get latest date
            query = """
                SELECT * FROM investments
                WHERE date = (SELECT MAX(date) FROM investments)
            """
            params = []

        if account_id:
            query += " AND account_id = ?" if "WHERE" in query else " WHERE account_id = ?"
            params.append(account_id)

        query += " ORDER BY value DESC"

        results = self.db.execute_query(query, tuple(params))

        # Calculate gain/loss for each holding
        for holding in results:
            if holding['cost_basis'] and holding['cost_basis'] > 0:
                holding['gain_loss'] = holding['value'] - holding['cost_basis']
                holding['gain_loss_pct'] = (holding['gain_loss'] / holding['cost_basis']) * 100
            else:
                holding['gain_loss'] = None
                holding['gain_loss_pct'] = None

        return results

    # ==================== BILLS ====================

    def save_bill(self, bill_data: Dict[str, Any]) -> bool:
        """
        Save or update a bill.

        Args:
            bill_data: Bill data

        Returns:
            True if successful
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO bills (
                        bill_id, account_id, name, amount, frequency, category,
                        next_payment_date, last_payment_date, auto_pay, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(bill_id) DO UPDATE SET
                        amount = excluded.amount,
                        next_payment_date = excluded.next_payment_date,
                        last_payment_date = excluded.last_payment_date,
                        status = excluded.status,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    bill_data['bill_id'],
                    bill_data.get('account_id'),
                    bill_data['name'],
                    bill_data.get('amount'),
                    bill_data.get('frequency'),
                    bill_data.get('category'),
                    bill_data.get('next_payment_date'),
                    bill_data.get('last_payment_date'),
                    bill_data.get('auto_pay', False),
                    bill_data.get('status', 'active')
                ))

            logger.debug(f"Saved bill: {bill_data['name']}")
            return True

        except Exception as e:
            logger.error(f"Error saving bill: {e}")
            return False

    def get_bills(self, status: str = 'active') -> List[Dict[str, Any]]:
        """Get bills by status."""
        query = "SELECT * FROM bills WHERE status = ? ORDER BY next_payment_date"
        return self.db.execute_query(query, (status,))
