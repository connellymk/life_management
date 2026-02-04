#!/usr/bin/env python3
"""
Initialize SQL database with schema.
Safe to run multiple times.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import Database
from core.utils import setup_logging

logger = setup_logging("init_database")


def main():
    """Initialize database with all tables and indexes."""
    print("\n" + "=" * 60)
    print("Database Initialization")
    print("=" * 60)

    # Initialize database
    db = Database("data.db")

    # Create schema
    print("\n1. Creating tables and indexes...")
    db.initialize_schema()

    # Verify schema
    print("\n2. Verifying schema...")
    is_valid, errors = db.verify_schema()

    if not is_valid:
        print("X Schema verification failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    print("+ Schema verified")

    # Get table counts
    print("\n3. Current data counts:")
    counts = db.get_table_counts()
    for table, count in counts.items():
        print(f"  {table:20s}: {count:>6d} rows")

    # Get database size
    size_bytes = db.get_database_size()
    size_mb = size_bytes / (1024 * 1024)
    print(f"\n4. Database size: {size_mb:.2f} MB ({size_bytes:,} bytes)")

    print("\n" + "=" * 60)
    print("+ Database initialized successfully!")
    print("=" * 60)
    print("\nDatabase location: data.db")
    print("\nNext steps:")
    print("  1. Run health sync to populate metrics")
    print("  2. Query data using SQL or storage modules")
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
