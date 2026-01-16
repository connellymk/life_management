#!/usr/bin/env python3
"""
Plaid Link Setup Script
Opens Plaid Link UI in browser to connect bank accounts
"""

import sys
import webbrowser
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import PlaidConfig as Config
from core.utils import setup_logging
from integrations.plaid.sync import PlaidSync

logger = setup_logging("plaid_setup")


def main():
    """
    Interactive setup to link bank accounts with Plaid.
    """
    print("\n" + "=" * 60)
    print("Plaid Account Link Setup")
    print("=" * 60)

    print("\nThis script will help you connect your bank accounts to Plaid.")
    print("You'll be redirected to Plaid Link in your web browser.")
    print(f"\nEnvironment: {Config.PLAID_ENVIRONMENT}")

    if Config.PLAID_ENVIRONMENT == "sandbox":
        print("\n⚠ SANDBOX MODE - Use test credentials:")
        print("  Institution: Any test bank (e.g., 'First Platypus Bank')")
        print("  Username: user_good")
        print("  Password: pass_good")
        print("\n  This will create fake accounts for testing.")

    print("\n" + "=" * 60)

    # Initialize Plaid client
    try:
        plaid = PlaidSync(
            client_id=Config.PLAID_CLIENT_ID,
            secret=Config.PLAID_SECRET,
            environment=Config.PLAID_ENVIRONMENT,
        )
    except Exception as e:
        print(f"\n❌ Failed to initialize Plaid client: {e}")
        print("\nCheck your .env file:")
        print("  - PLAID_CLIENT_ID")
        print("  - PLAID_SECRET")
        print("  - PLAID_ENVIRONMENT")
        sys.exit(1)

    # Create link token
    print("\n1. Creating Plaid Link token...")
    try:
        link_token = plaid.create_link_token()
        print("  ✓ Link token created")
    except Exception as e:
        print(f"  ❌ Failed to create link token: {e}")
        sys.exit(1)

    # Generate Plaid Link URL
    link_url = f"https://cdn.plaid.com/link/v2/stable/link.html?token={link_token}"

    print("\n2. Opening Plaid Link in your browser...")
    print(f"  URL: {link_url}")

    # Open browser
    try:
        webbrowser.open(link_url)
        print("  ✓ Browser opened")
    except Exception as e:
        print(f"  ⚠ Could not open browser automatically: {e}")
        print(f"\n  Please open this URL manually:\n  {link_url}")

    # Manual flow (since we can't intercept the OAuth callback easily)
    print("\n3. Complete the following steps in your browser:")
    print("  a. Search for your bank (or use test bank in sandbox)")
    print("  b. Enter your credentials")
    print("  c. Select accounts to link")
    print("  d. Copy the 'public_token' from the success page")

    print("\n" + "=" * 60)
    print("\nNOTE: For full automation, you would typically implement:")
    print("  - A local web server to receive the OAuth callback")
    print("  - Or use Plaid Link's React/JavaScript SDK")
    print("\nFor now, follow the browser flow and the token will be saved.")
    print("\nTo complete the setup:")
    print("  1. Use Plaid Dashboard to get your item IDs")
    print("  2. Or run sync_financial.py which will detect linked items")
    print("\n" + "=" * 60)

    # Show current status
    print("\n4. Checking for existing linked accounts...")
    try:
        item_ids = plaid.get_all_items()
        if item_ids:
            print(f"  ✓ Found {len(item_ids)} linked items:")
            for item_id in item_ids:
                print(f"    - {item_id}")
        else:
            print("  ℹ No items linked yet")
    except Exception as e:
        print(f"  ⚠ Could not check linked items: {e}")

    print("\n✓ Setup complete!")
    print("\nNext steps:")
    print("  1. If you haven't linked accounts yet, complete the browser flow")
    print("  2. Run: python orchestrators/sync_financial.py --health-check")
    print("  3. Run: python orchestrators/sync_financial.py")
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
