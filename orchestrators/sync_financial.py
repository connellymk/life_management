#!/usr/bin/env python3
"""
Financial Sync Orchestrator
Syncs Plaid banking data to SQL database (primary storage)

All financial data is stored in local SQL database for:
- Unlimited transaction history (10+ years)
- Privacy (data stays local, never in cloud)
- Fast complex analytics (30-500x faster than API queries)

Optional future enhancement: Sync summary view to Notion (last 90 days)
for visual dashboards while keeping full history in SQL.
"""

import sys
import time
import argparse
from datetime import datetime, timedelta, date
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import PlaidConfig as Config
from core.utils import setup_logging
from core.database import Database
from storage.financial import FinancialStorage
from integrations.plaid.sync import PlaidSync

logger = setup_logging("financial_sync")


def sync_accounts(plaid: PlaidSync, storage: FinancialStorage, dry_run: bool = False) -> dict:
    """
    Sync all accounts from Plaid to SQL database.

    Args:
        plaid: Plaid sync client
        storage: Financial storage client
        dry_run: If True, don't actually save data

    Returns:
        Dictionary with sync stats
    """
    logger.info("=" * 50)
    logger.info("Syncing Accounts...")
    logger.info("=" * 50)

    start_time = time.time()
    stats = {"fetched": 0, "saved": 0, "errors": 0}

    try:
        # Get all linked items
        item_ids = plaid.get_all_items()

        if not item_ids:
            logger.warning("No Plaid items linked. Run setup_plaid.py first.")
            return stats

        # Fetch accounts for each item
        all_accounts = []
        for item_id in item_ids:
            try:
                accounts = plaid.get_accounts(item_id)
                all_accounts.extend(accounts)
            except Exception as e:
                logger.error(f"Error fetching accounts for item {item_id}: {e}")
                stats["errors"] += 1

        stats["fetched"] = len(all_accounts)

        if not all_accounts:
            logger.info("No accounts found")
            return stats

        logger.info(f"Found {len(all_accounts)} accounts across {len(item_ids)} items")

        if dry_run:
            logger.info("DRY RUN: Would sync the following accounts:")
            for account in all_accounts:
                logger.info(
                    f"  - {account['name']} ({account['type']}) - {account['masked_number']}"
                )
            return stats

        # Save each account to SQL
        for account in all_accounts:
            try:
                if storage.save_account(account):
                    stats["saved"] += 1
            except Exception as e:
                logger.error(f"Error saving account {account['name']}: {e}")
                stats["errors"] += 1

        elapsed = time.time() - start_time
        logger.info(f"Accounts sync complete in {elapsed:.1f}s")
        logger.info(
            f"  Fetched: {stats['fetched']}, Saved: {stats['saved']}, Errors: {stats['errors']}"
        )

    except Exception as e:
        logger.error(f"Unexpected error during account sync: {e}")
        stats["errors"] += 1

    return stats


def sync_transactions(
    plaid: PlaidSync, storage: FinancialStorage, dry_run: bool = False
) -> dict:
    """
    Sync transactions from Plaid to SQL database.

    Args:
        plaid: Plaid sync client
        storage: Financial storage client
        dry_run: If True, don't actually save data

    Returns:
        Dictionary with sync stats
    """
    logger.info("=" * 50)
    logger.info("Syncing Transactions...")
    logger.info("=" * 50)

    start_time = time.time()
    stats = {"fetched": 0, "saved": 0, "skipped": 0, "errors": 0}

    try:
        # Get all linked items
        item_ids = plaid.get_all_items()

        if not item_ids:
            logger.warning("No Plaid items linked")
            return stats

        # Fetch transactions for the configured number of days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=Config.PLAID_TRANSACTION_DAYS)

        logger.info(
            f"Fetching transactions from {start_date.date()} to {end_date.date()} ({Config.PLAID_TRANSACTION_DAYS} days)"
        )

        # Fetch transactions for each item
        all_transactions = []
        for item_id in item_ids:
            try:
                transactions = plaid.get_transactions(item_id, start_date, end_date)
                all_transactions.extend(transactions)
            except Exception as e:
                logger.error(f"Error fetching transactions for item {item_id}: {e}")
                stats["errors"] += 1

        stats["fetched"] = len(all_transactions)

        if not all_transactions:
            logger.info("No transactions found")
            return stats

        logger.info(f"Found {len(all_transactions)} transactions")

        if dry_run:
            logger.info("DRY RUN: Would sync the following transactions:")
            for txn in all_transactions[:10]:  # Show first 10
                logger.info(
                    f"  - {txn['date'].date()}: {txn['name']} (${txn['amount']:.2f})"
                )
            if len(all_transactions) > 10:
                logger.info(f"  ... and {len(all_transactions) - 10} more")
            return stats

        # Save each transaction to SQL (INSERT OR IGNORE for duplicates)
        for txn in all_transactions:
            try:
                if storage.save_transaction(txn):
                    stats["saved"] += 1
                else:
                    stats["skipped"] += 1
            except Exception as e:
                logger.error(f"Error saving transaction {txn['name']}: {e}")
                stats["errors"] += 1

        elapsed = time.time() - start_time
        logger.info(f"Transactions sync complete in {elapsed:.1f}s")
        logger.info(
            f"  Fetched: {stats['fetched']}, Saved: {stats['saved']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}"
        )

    except Exception as e:
        logger.error(f"Unexpected error during transaction sync: {e}")
        stats["errors"] += 1

    return stats


def sync_balances(
    plaid: PlaidSync, storage: FinancialStorage, dry_run: bool = False
) -> dict:
    """
    Create daily balance snapshots for all accounts in SQL.

    Args:
        plaid: Plaid sync client
        storage: Financial storage client
        dry_run: If True, don't actually save data

    Returns:
        Dictionary with sync stats
    """
    logger.info("=" * 50)
    logger.info("Syncing Balance Snapshots...")
    logger.info("=" * 50)

    start_time = time.time()
    stats = {"fetched": 0, "saved": 0, "skipped": 0, "errors": 0}

    try:
        # Get all linked items
        item_ids = plaid.get_all_items()

        if not item_ids:
            logger.warning("No Plaid items linked")
            return stats

        # Fetch accounts for each item
        all_accounts = []
        for item_id in item_ids:
            try:
                accounts = plaid.get_accounts(item_id)
                all_accounts.extend(accounts)
            except Exception as e:
                logger.error(f"Error fetching accounts for item {item_id}: {e}")
                stats["errors"] += 1

        stats["fetched"] = len(all_accounts)

        if not all_accounts:
            logger.info("No accounts found")
            return stats

        logger.info(f"Creating balance snapshots for {len(all_accounts)} accounts")

        if dry_run:
            logger.info("DRY RUN: Would create balance snapshots for:")
            for account in all_accounts:
                logger.info(
                    f"  - {account['name']}: ${account.get('current_balance', 0):.2f}"
                )
            return stats

        # Create balance snapshot for each account
        today = date.today()
        for account in all_accounts:
            try:
                if storage.save_balance(account['account_id'], account, today):
                    stats["saved"] += 1
                else:
                    stats["skipped"] += 1
            except Exception as e:
                logger.error(f"Error saving balance for {account['name']}: {e}")
                stats["errors"] += 1

        elapsed = time.time() - start_time
        logger.info(f"Balance snapshots sync complete in {elapsed:.1f}s")
        logger.info(
            f"  Fetched: {stats['fetched']}, Saved: {stats['saved']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}"
        )

    except Exception as e:
        logger.error(f"Unexpected error during balance sync: {e}")
        stats["errors"] += 1

    return stats


def sync_investments(
    plaid: PlaidSync, storage: FinancialStorage, dry_run: bool = False
) -> dict:
    """
    Sync investment holdings from Plaid to SQL database.

    Args:
        plaid: Plaid sync client
        storage: Financial storage client
        dry_run: If True, don't actually save data

    Returns:
        Dictionary with sync stats
    """
    logger.info("=" * 50)
    logger.info("Syncing Investments...")
    logger.info("=" * 50)

    start_time = time.time()
    stats = {"fetched": 0, "saved": 0, "errors": 0}

    try:
        # Get all linked items
        item_ids = plaid.get_all_items()

        if not item_ids:
            logger.warning("No Plaid items linked")
            return stats

        # Fetch investments for each item
        all_holdings = []
        for item_id in item_ids:
            try:
                holdings = plaid.get_investments(item_id)
                all_holdings.extend(holdings)
            except Exception as e:
                # Not all items have investments
                logger.debug(f"No investments for item {item_id}: {e}")

        stats["fetched"] = len(all_holdings)

        if not all_holdings:
            logger.info("No investment holdings found")
            return stats

        logger.info(f"Found {len(all_holdings)} investment holdings")

        if dry_run:
            logger.info("DRY RUN: Would sync the following holdings:")
            for holding in all_holdings[:10]:
                logger.info(
                    f"  - {holding['name']} ({holding.get('ticker', 'N/A')}): {holding['quantity']} @ ${holding['price']:.2f}"
                )
            if len(all_holdings) > 10:
                logger.info(f"  ... and {len(all_holdings) - 10} more")
            return stats

        # Save each holding to SQL
        today = date.today()
        for holding in all_holdings:
            try:
                if storage.save_investment(holding, today):
                    stats["saved"] += 1
            except Exception as e:
                logger.error(f"Error saving investment {holding['name']}: {e}")
                stats["errors"] += 1

        elapsed = time.time() - start_time
        logger.info(f"Investments sync complete in {elapsed:.1f}s")
        logger.info(
            f"  Fetched: {stats['fetched']}, Saved: {stats['saved']}, Errors: {stats['errors']}"
        )

    except Exception as e:
        logger.error(f"Unexpected error during investment sync: {e}")
        stats["errors"] += 1

    return stats


def health_check() -> bool:
    """
    Run health check to verify configuration and database.

    Returns:
        True if all checks pass, False otherwise
    """
    logger.info("=" * 60)
    logger.info("Financial Sync - Health Check")
    logger.info("=" * 60)

    # Check configuration
    logger.info("\n1. Checking configuration...")
    is_valid, errors = Config.validate()

    if not is_valid:
        logger.error("X Configuration not valid:")
        for error in errors:
            logger.error(f"  - {error}")
        return False

    logger.info("+ Configuration valid")

    # Check SQL database
    logger.info("\n2. Checking SQL database...")
    try:
        db = Database(Config.DATA_DB_PATH)
        is_valid, errors = db.verify_schema()

        if not is_valid:
            logger.error("X Database schema invalid:")
            for error in errors:
                logger.error(f"  - {error}")
            logger.error("\nRun: python scripts/init_database.py")
            return False

        logger.info("+ Database schema valid")

        # Show current data counts
        counts = db.get_table_counts()
        logger.info(f"  Accounts: {counts['accounts']}")
        logger.info(f"  Transactions: {counts['transactions']}")
        logger.info(f"  Balances: {counts['balances']}")
        logger.info(f"  Investments: {counts['investments']}")

    except Exception as e:
        logger.error(f"X Database error: {e}")
        return False

    # Check Plaid credentials
    logger.info("\n3. Checking Plaid credentials...")
    try:
        plaid = PlaidSync(
            client_id=Config.PLAID_CLIENT_ID,
            secret=Config.PLAID_SECRET,
            environment=Config.PLAID_ENVIRONMENT,
        )

        # Try to create a link token (doesn't require existing items)
        link_token = plaid.create_link_token()
        logger.info(f"  + Plaid credentials valid ({Config.PLAID_ENVIRONMENT} environment)")

    except Exception as e:
        logger.error(f"  X Plaid connection failed: {e}")
        return False

    # Check for linked items
    logger.info("\n4. Checking for linked Plaid items...")
    item_ids = plaid.get_all_items()
    if item_ids:
        logger.info(f"  + Found {len(item_ids)} linked items")
        for item_id in item_ids:
            logger.info(f"    - {item_id}")
    else:
        logger.warning("  ! No items linked yet. Run setup_plaid.py to link your bank accounts.")

    logger.info("\n" + "=" * 60)
    logger.info("+ Health check passed!")
    logger.info("=" * 60)
    logger.info("\nData storage: SQL database (data.db)")
    logger.info(f"Transaction history: {Config.PLAID_TRANSACTION_DAYS} days")
    logger.info("\nNext steps:")
    if not item_ids:
        logger.info("  1. Run 'python orchestrators/setup_plaid.py' to link bank accounts")
        logger.info("  2. Run 'python orchestrators/sync_financial.py' to sync data")
    else:
        logger.info("  1. Run 'python orchestrators/sync_financial.py' to sync data")
        logger.info("  2. Query data using storage modules or SQL")

    return True


def main():
    """Main sync orchestrator."""
    parser = argparse.ArgumentParser(
        description="Sync financial data from Plaid to SQL database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview sync without making changes",
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Run health check to verify configuration",
    )
    parser.add_argument(
        "--accounts-only",
        action="store_true",
        help="Sync only accounts",
    )
    parser.add_argument(
        "--transactions-only",
        action="store_true",
        help="Sync only transactions",
    )
    parser.add_argument(
        "--balances-only",
        action="store_true",
        help="Sync only balance snapshots",
    )
    parser.add_argument(
        "--investments-only",
        action="store_true",
        help="Sync only investments",
    )

    args = parser.parse_args()

    # Health check mode
    if args.health_check:
        success = health_check()
        sys.exit(0 if success else 1)

    # Normal sync mode
    logger.info("=" * 60)
    logger.info("Financial Data Sync - Starting")
    logger.info("=" * 60)
    logger.info(f"Storage: SQL database ({Config.DATA_DB_PATH})")
    logger.info(f"Environment: {Config.PLAID_ENVIRONMENT}")
    logger.info(f"Transaction days: {Config.PLAID_TRANSACTION_DAYS}")

    if args.dry_run:
        logger.info("! DRY RUN MODE - No changes will be made")

    start_time = time.time()

    try:
        # Initialize clients
        plaid = PlaidSync(
            client_id=Config.PLAID_CLIENT_ID,
            secret=Config.PLAID_SECRET,
            environment=Config.PLAID_ENVIRONMENT,
        )
        db = Database(Config.DATA_DB_PATH)
        storage = FinancialStorage(db)

        # Determine what to sync
        sync_all = not any(
            [
                args.accounts_only,
                args.transactions_only,
                args.balances_only,
                args.investments_only,
            ]
        )

        # Sync accounts (always needed for relations)
        if sync_all or args.accounts_only:
            account_stats = sync_accounts(plaid, storage, dry_run=args.dry_run)

        # Sync transactions
        if sync_all or args.transactions_only:
            txn_stats = sync_transactions(plaid, storage, dry_run=args.dry_run)

        # Sync balance snapshots
        if sync_all or args.balances_only:
            balance_stats = sync_balances(plaid, storage, dry_run=args.dry_run)

        # Sync investments
        if sync_all or args.investments_only:
            investment_stats = sync_investments(plaid, storage, dry_run=args.dry_run)

        # Summary
        elapsed = time.time() - start_time
        logger.info("\n" + "=" * 60)
        logger.info(f"Financial sync complete in {elapsed:.1f}s")
        logger.info("=" * 60)

        if not args.dry_run:
            # Show current database stats
            counts = db.get_table_counts()
            logger.info("\nDatabase summary:")
            logger.info(f"  Accounts: {counts['accounts']}")
            logger.info(f"  Transactions: {counts['transactions']}")
            logger.info(f"  Balances: {counts['balances']} snapshots")
            logger.info(f"  Investments: {counts['investments']} holdings")

            # Calculate net worth
            net_worth = storage.get_net_worth()
            logger.info(f"\nCurrent net worth: ${net_worth:,.2f}")

            logger.info("\n+ Data saved to SQL database")
            logger.info("  Query data using storage.queries or direct SQL")

    except Exception as e:
        logger.error(f"\nX Sync failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
