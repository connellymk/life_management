# Hybrid SQL + Notion Architecture Plan

## Overview

Moving to a hybrid architecture where:
- **SQL Database (PostgreSQL/SQLite)** = Primary storage for high-volume data
- **Notion** = Dashboard/UI for recent data and manual annotations

## Data Storage Strategy

### Keep in Notion (Low Volume, Manual Editing)
✅ **Calendar Events** - ~400 events, manually annotated, visual timeline
✅ **Workouts** - ~100 activities, want to add notes/tags manually
✅ **Tasks** - Manual task management
✅ **Classes** - Manual course tracking

### Move to SQL (High Volume, Analytics)
🔄 **Daily Metrics** - 91+ days, growing daily, need trend analysis
🔄 **Transactions** - High volume, need historical analysis (5+ years)
🔄 **Balances** - Daily snapshots, need net worth trends
🔄 **Accounts** - Reference data, rarely changes
🔄 **Investments** - Holdings history, performance tracking
🔄 **Bills** - Recurring payment tracking

### Optional Notion Summaries (SQL → Notion)
📊 Recent transactions (last 30 days) for quick viewing
📊 Monthly spending summaries by category
📊 Net worth trend (monthly snapshots)
📊 Investment performance dashboard

## Database Choice: PostgreSQL vs SQLite

### Recommendation: **Start with SQLite, migrate to PostgreSQL if needed**

**SQLite Pros:**
- ✅ No separate server required
- ✅ Single file database (easy backup)
- ✅ Fast for local queries
- ✅ Perfect for single-user application
- ✅ Already using it for state.db
- ✅ Can scale to millions of rows

**SQLite Cons:**
- ❌ No concurrent writes (not an issue for single-user sync)
- ❌ Limited built-in functions vs PostgreSQL

**Migration Path:**
- Start with SQLite (data.db)
- If you need advanced analytics → PostgreSQL
- SQLite can easily be converted to PostgreSQL later

## SQL Database Schema

### Financial Tables

```sql
-- Accounts table
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL,
    name TEXT NOT NULL,
    official_name TEXT,
    type TEXT NOT NULL,  -- depository, credit, investment, loan
    subtype TEXT,
    masked_number TEXT,
    institution_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table (unlimited history)
CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    date DATE NOT NULL,
    amount REAL NOT NULL,  -- negative for expenses, positive for income
    name TEXT NOT NULL,
    merchant_name TEXT,
    category_primary TEXT,
    category_detailed TEXT,
    pending BOOLEAN DEFAULT 0,
    payment_channel TEXT,
    iso_currency_code TEXT DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

CREATE INDEX idx_transactions_date ON transactions(date DESC);
CREATE INDEX idx_transactions_account ON transactions(account_id);
CREATE INDEX idx_transactions_category ON transactions(category_primary);

-- Balances table (daily snapshots)
CREATE TABLE balances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    date DATE NOT NULL,
    current_balance REAL,
    available_balance REAL,
    credit_limit REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    UNIQUE(account_id, date)
);

CREATE INDEX idx_balances_date ON balances(date DESC);

-- Investments table (holdings snapshots)
CREATE TABLE investments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    holding_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    security_id TEXT NOT NULL,
    name TEXT NOT NULL,
    ticker TEXT,
    type TEXT,  -- stock, etf, mutual_fund, bond, cash
    quantity REAL,
    price REAL,
    value REAL,
    cost_basis REAL,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    UNIQUE(holding_id, date)
);

CREATE INDEX idx_investments_date ON investments(date DESC);
CREATE INDEX idx_investments_ticker ON investments(ticker);

-- Bills table
CREATE TABLE bills (
    bill_id TEXT PRIMARY KEY,
    account_id TEXT,
    name TEXT NOT NULL,
    amount REAL,
    frequency TEXT,  -- weekly, monthly, quarterly, annually
    category TEXT,
    next_payment_date DATE,
    last_payment_date DATE,
    auto_pay BOOLEAN DEFAULT 0,
    status TEXT DEFAULT 'active',  -- active, paused, cancelled
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);
```

### Health Tables

```sql
-- Daily Metrics table (replaces Notion)
CREATE TABLE daily_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    steps INTEGER,
    distance_miles REAL,
    floors_climbed REAL,
    calories_active INTEGER,
    calories_total INTEGER,
    sleep_duration_hours REAL,
    sleep_score INTEGER,
    resting_heart_rate INTEGER,
    min_heart_rate INTEGER,
    max_heart_rate INTEGER,
    avg_stress INTEGER,
    body_battery_max INTEGER,
    moderate_intensity_minutes INTEGER,
    vigorous_intensity_minutes INTEGER,
    vo2_max REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_daily_metrics_date ON daily_metrics(date DESC);

-- Body Metrics table (if Garmin data becomes available)
CREATE TABLE body_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    weight_lbs REAL,
    bmi REAL,
    body_fat_pct REAL,
    muscle_mass_lbs REAL,
    bone_mass_lbs REAL,
    body_water_pct REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     DATA SOURCES                            │
├──────────────┬──────────────┬──────────────┬───────────────┤
│ Google Cal   │ Garmin       │ Plaid        │ Manual        │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                    SYNC ORCHESTRATORS                       │
├──────────────┬──────────────┬──────────────┬───────────────┤
│ sync_cal.py  │ sync_health  │ sync_fin.py  │ Manual        │
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                  STORAGE LAYER                              │
├──────────────────────────────┬──────────────────────────────┤
│         NOTION               │       SQL DATABASE           │
│  ┌────────────────────┐      │  ┌────────────────────┐     │
│  │ Calendar Events    │      │  │ Transactions       │     │
│  │ Workouts           │      │  │ Accounts           │     │
│  │ Tasks              │      │  │ Balances           │     │
│  │ Classes            │      │  │ Investments        │     │
│  │                    │      │  │ Bills              │     │
│  │ (Optional)         │      │  │ Daily Metrics      │     │
│  │ - Recent Txns      │◄─────┼──│ Body Metrics       │     │
│  │ - Summaries        │      │  └────────────────────┘     │
│  └────────────────────┘      │                              │
└──────────────────────────────┴──────────────────────────────┘
       │                              │
       └──────────────┬───────────────┘
                      ▼
              ┌───────────────┐
              │    CLAUDE     │
              │               │
              │ - Notion API  │
              │ - SQL Queries │
              └───────────────┘
```

## Implementation Phases

### Phase 1: Database Setup ✅ **DO THIS FIRST**
1. Create `core/database.py` module
   - SQLite connection management
   - Table creation/migration
   - CRUD operations for all tables

2. Create schema migration script
   - Initialize database with tables
   - Add indexes
   - Validate schema

3. Add database path to config
   - `DATA_DB_PATH` in .env
   - Default: `data.db`

### Phase 2: Financial Sync → SQL
1. Update `integrations/plaid/sync.py`
   - No changes needed (already returns normalized data)

2. Create `storage/financial.py`
   - Save accounts to SQL
   - Save transactions to SQL
   - Save balances to SQL
   - Save investments to SQL
   - Query methods for Claude

3. Update `orchestrators/sync_financial.py`
   - Save to SQL as primary storage
   - **Remove** Notion sync for transactions/balances
   - Keep Notion sync for accounts (reference)

### Phase 3: Health Sync → SQL for Daily Metrics
1. Create `storage/health.py`
   - Save daily metrics to SQL
   - Query methods for trends

2. Update `orchestrators/sync_health.py`
   - Save daily metrics to SQL
   - **Remove** Notion sync for daily metrics
   - Keep Notion sync for workouts

### Phase 4: Query Layer for Claude
1. Create `storage/queries.py`
   - Pre-built queries for common analyses:
     - Monthly spending by category
     - Net worth trend
     - Transaction search
     - Category budgets
     - Investment performance
     - Health correlations

2. Create `tools/sql_helper.py` (optional)
   - Allow Claude to run custom SQL queries
   - Add safety guards (read-only, no DROP/DELETE)

### Phase 5: Optional Notion Summaries
1. Create `notion/summaries.py`
   - Sync recent transactions (last 30 days) to Notion
   - Sync monthly spending summaries
   - Sync net worth snapshots
   - Keep full history in SQL

## Migration Strategy

### For Existing Data

**If you already have financial data in Notion:**
1. Export from Notion (CSV)
2. Import into SQL database
3. Verify data integrity
4. Clear Notion databases
5. Re-sync from SQL → Notion summaries

**For new installation:**
- Just start with SQL, no migration needed

## Benefits of This Architecture

### For You
✅ **Unlimited history** - Keep 10+ years of transactions
✅ **Fast analytics** - SQL queries in milliseconds
✅ **No API limits** - Query locally as much as you want
✅ **Better privacy** - Sensitive data never leaves your machine
✅ **Easy backup** - Single SQLite file to back up
✅ **Future-proof** - Can migrate to PostgreSQL later

### For Claude
✅ **Direct SQL access** - No Notion API rate limits
✅ **Complex queries** - JOINs, aggregations, window functions
✅ **Historical analysis** - Analyze years of data instantly
✅ **Real-time** - No sync delay for queries

### For Notion
✅ **Stays fast** - No large datasets to slow it down
✅ **Manual annotations** - Still great for workouts, events
✅ **Beautiful dashboards** - Show summaries and trends
✅ **Collaboration** - Can share summaries without exposing raw data

## Example Queries Claude Can Run

```sql
-- Monthly spending by category
SELECT
    strftime('%Y-%m', date) as month,
    category_primary,
    SUM(amount) as total,
    COUNT(*) as transaction_count
FROM transactions
WHERE amount < 0  -- expenses only
GROUP BY month, category_primary
ORDER BY month DESC, total DESC;

-- Net worth over time
SELECT
    date,
    SUM(current_balance) as net_worth
FROM balances
GROUP BY date
ORDER BY date DESC;

-- Find large transactions
SELECT date, name, amount, category_primary
FROM transactions
WHERE ABS(amount) > 100
ORDER BY date DESC
LIMIT 20;

-- Investment performance
SELECT
    ticker,
    name,
    quantity,
    price,
    value,
    cost_basis,
    (value - cost_basis) as gain_loss,
    ((value - cost_basis) / cost_basis * 100) as gain_loss_pct
FROM investments
WHERE date = (SELECT MAX(date) FROM investments)
ORDER BY value DESC;

-- Health correlations (sleep vs steps)
SELECT
    date,
    sleep_duration_hours,
    steps,
    avg_stress
FROM daily_metrics
WHERE date > date('now', '-90 days')
ORDER BY date DESC;
```

## Security Considerations

### SQL Database Security
- ✅ Database file permissions: 600 (owner only)
- ✅ Located in project directory (not web-accessible)
- ✅ No network access (SQLite is file-based)
- ✅ Regular backups with encryption
- ✅ Sensitive data (full account numbers) never stored

### Notion Security (unchanged)
- ✅ Only masked account numbers
- ✅ Only recent summaries (if Phase 5 implemented)
- ✅ Can share specific views without exposing raw data

## Configuration Changes

Add to `.env`:
```env
# Database Configuration
DATA_DB_PATH=data.db

# Notion Sync Options
SYNC_TRANSACTIONS_TO_NOTION=false  # Set to true for Phase 5
NOTION_TRANSACTION_DAYS=30  # How many days to sync if enabled
SYNC_DAILY_METRICS_TO_NOTION=false  # Set to true to keep both
```

## Rollback Plan

If you want to go back to Notion-only:
1. Keep SQL database (don't delete)
2. Re-enable Notion sync in orchestrators
3. Sync from SQL → Notion
4. Claude can still use Notion API

## Performance Estimates

### SQL Performance
- Transaction insert: <1ms
- Query 1 year transactions: <10ms
- Complex aggregations: <100ms
- Full-text search: <50ms

### Storage Size
- 10 years transactions (~12,000): ~5 MB
- 10 years daily metrics: ~100 KB
- 10 years balances: ~1 MB
- Total: ~10-20 MB (tiny!)

## Next Steps

1. ✅ Review this plan
2. ⏳ Implement Phase 1 (database setup)
3. ⏳ Implement Phase 2 (financial sync to SQL)
4. ⏳ Implement Phase 3 (health sync to SQL)
5. ⏳ Implement Phase 4 (query layer)
6. ⏹️ Optional: Implement Phase 5 (Notion summaries)

---

**Ready to proceed?** Let's start with Phase 1: Database Setup!
