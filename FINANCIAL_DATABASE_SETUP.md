# Financial Database Setup Guide

⚠️ **OUTDATED - This document is kept for reference only**

## Current Architecture

As of Phase 2 (January 2026), **financial data is stored in SQL database**, not Notion.

### What Changed

**Old approach (this document):**
- Financial data synced to 5 Notion databases
- Limited to 30 days of transactions
- Slower queries due to Notion API

**New approach (current):**
- Financial data syncs to local SQL database (`data.db`)
- Unlimited transaction history
- 30-500x faster queries
- Enhanced privacy (data never leaves your machine)
- No Notion setup required for financial data

## Current Setup Instructions

### 1. Initialize SQL Database

```bash
python scripts/init_database.py
```

This creates `data.db` with all required tables:
- `accounts` - Bank accounts, credit cards, investments
- `transactions` - All transactions (unlimited history)
- `balances` - Daily balance snapshots
- `investments` - Investment holdings
- `bills` - Recurring payments

### 2. Configure Plaid Credentials

Add to your `.env` file:

```env
# Plaid API Credentials
PLAID_CLIENT_ID=your_client_id_here
PLAID_SECRET=your_secret_key_here
PLAID_ENVIRONMENT=sandbox  # Use 'sandbox' for testing, 'production' for real data

# Sync Settings
PLAID_TRANSACTION_DAYS=730  # Fetch up to 2 years of history (Plaid limit)
```

### 3. Link Bank Accounts

```bash
python orchestrators/setup_plaid.py
```

This opens Plaid Link in your browser to connect accounts.

### 4. Run Financial Sync

```bash
# Verify setup
python orchestrators/sync_financial.py --health-check

# Run sync to SQL database
python orchestrators/sync_financial.py

# Preview without making changes
python orchestrators/sync_financial.py --dry-run
```

## Security

**Enhanced security with SQL storage:**
- ✅ All financial data stored locally (never in cloud/Notion)
- ✅ Plaid access tokens encrypted with Fernet (AES-128)
- ✅ Full account numbers NEVER stored (only last 4 digits)
- ✅ Database file protected with owner-only permissions
- ✅ SQL injection prevention via parameterized queries

See [FINANCIAL_SECURITY_PLAN.md](FINANCIAL_SECURITY_PLAN.md) for complete security details.

## Querying Financial Data

### Using Pre-Built Analytics

```python
from core.database import Database
from storage.queries import AnalyticsQueries

db = Database("data.db")
analytics = AnalyticsQueries(db)

# Monthly spending by category
spending = analytics.monthly_spending_by_category(num_months=6)

# Net worth trend
net_worth = analytics.net_worth_trend(num_days=90)

# Large transactions
large = analytics.large_transactions(threshold=100, num_days=30)
```

### Direct SQL Queries

```python
from core.database import Database

db = Database("data.db")

# Custom analysis
results = db.execute_query("""
    SELECT
        category_primary,
        COUNT(*) as txn_count,
        SUM(amount) as total,
        AVG(amount) as avg_amount
    FROM transactions
    WHERE date >= date('now', '-30 days')
      AND amount < 0
    GROUP BY category_primary
    ORDER BY total ASC
""")
```

## Documentation

For complete architecture details, see:
- [HYBRID_ARCHITECTURE_COMPLETE.md](HYBRID_ARCHITECTURE_COMPLETE.md) - Full SQL + Notion architecture
- [PHASE2_COMPLETE.md](PHASE2_COMPLETE.md) - Financial sync migration details
- [FINANCIAL_SECURITY_PLAN.md](FINANCIAL_SECURITY_PLAN.md) - Security architecture

---

## Legacy Notion Setup (Not Used)

The remainder of this document describes the old Notion-based approach and is kept for reference only.

<details>
<summary>Click to expand legacy Notion setup instructions</summary>

### Overview (Legacy)

The old approach required creating 5 Notion databases:
1. **Accounts** - Bank accounts, credit cards, investment accounts
2. **Transactions** - Daily transactions (30 days rolling)
3. **Balances** - Daily account balances snapshot
4. **Investments** - Investment holdings and performance
5. **Bills** - Recurring payments and bills

This approach is no longer used. Financial data now syncs directly to SQL database for:
- Unlimited history (not just 30 days)
- 30-500x faster queries
- Better privacy (local storage only)
- No Notion database setup required

</details>

---

**For current setup instructions, see:**
- [README.md](README.md) - Main documentation with SQL setup
- [HYBRID_ARCHITECTURE_COMPLETE.md](HYBRID_ARCHITECTURE_COMPLETE.md) - Complete architecture overview
