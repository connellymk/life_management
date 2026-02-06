#!/usr/bin/env python3
"""
Grocery Cart Orchestrator
Searches for grocery items via the Kroger API and adds them to your
Smith's Food & Drug pickup cart.

Usage:
    # First-time setup: find your local Smith's store
    python orchestrators/grocery_cart.py --find-store 84101

    # Health check (verify API credentials + store)
    python orchestrators/grocery_cart.py --health-check

    # Authenticate with Kroger (opens browser for OAuth login)
    python orchestrators/grocery_cart.py --auth

    # Add items from a grocery list file (one item per line)
    python orchestrators/grocery_cart.py --file grocery_list.txt

    # Add items directly from command line
    python orchestrators/grocery_cart.py --items "avocados" "chicken thighs" "sweet potatoes"

    # Dry run (search products but don't add to cart)
    python orchestrators/grocery_cart.py --file grocery_list.txt --dry-run
"""

import sys
import time
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import KrogerConfig as Config
from core.utils import setup_logging
from integrations.kroger.client import KrogerClient

logger = setup_logging("grocery_cart")


def find_store(zip_code: str, chain: str = "SMITHS"):
    """Find nearby Kroger-family stores and display their location IDs."""
    logger.info(f"Searching for {chain} stores near {zip_code}...")

    client = KrogerClient()
    locations = client.find_locations(zip_code=zip_code, chain=chain)

    if not locations:
        logger.info(f"No {chain} stores found near {zip_code}")
        return

    print(f"\n{'='*60}")
    print(f"{chain} stores near {zip_code}:")
    print(f"{'='*60}")
    for loc in locations:
        addr = loc.get("address", {})
        addr_line = f"{addr.get('addressLine1', '')}, {addr.get('city', '')} {addr.get('state', '')} {addr.get('zipCode', '')}"
        print(f"\n  Location ID: {loc['location_id']}")
        print(f"  Name:        {loc['name']}")
        print(f"  Address:     {addr_line}")
        if loc.get("phone"):
            print(f"  Phone:       {loc['phone']}")

    print(f"\n{'='*60}")
    print("Add your preferred store's Location ID to .env:")
    print(f"  KROGER_LOCATION_ID={locations[0]['location_id']}")
    print(f"{'='*60}\n")


def authenticate():
    """Run the OAuth authentication flow."""
    client = KrogerClient()
    if client.authenticate_user():
        print("\n+ Kroger authentication successful!")
        print("  Your tokens have been saved to credentials/kroger_tokens.json")
        print("  You can now add items to your cart.\n")
    else:
        print("\nX Kroger authentication failed.")
        print("  Check your KROGER_CLIENT_ID and KROGER_CLIENT_SECRET in .env\n")
        sys.exit(1)


def health_check() -> bool:
    """Verify Kroger configuration and connectivity."""
    logger.info("=" * 60)
    logger.info("Grocery Cart - Health Check")
    logger.info("=" * 60)

    # Check configuration
    logger.info("\n1. Checking Kroger configuration...")
    is_valid, errors = Config.validate()

    if not is_valid:
        logger.error("X Configuration not valid:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    logger.info("+ Configuration valid")

    # Check API connectivity (client credentials)
    logger.info("\n2. Checking Kroger API connectivity...")
    try:
        client = KrogerClient()
        client._ensure_client_token()
        logger.info("+ Client credentials token obtained")
    except Exception as e:
        logger.error(f"X API connection failed: {e}")
        return False

    # Check store location
    logger.info("\n3. Checking store location...")
    if Config.KROGER_LOCATION_ID:
        try:
            products = client.search_products("milk", limit=1)
            if products:
                logger.info(f"+ Store {Config.KROGER_LOCATION_ID} is accessible")
            else:
                logger.warning("  Store accessible but no products returned for test query")
        except Exception as e:
            logger.error(f"X Store search failed: {e}")
            return False
    else:
        logger.warning("  KROGER_LOCATION_ID not set — run --find-store <zip> to configure")

    # Check user auth
    logger.info("\n4. Checking user authentication...")
    tokens_path = Path(__file__).parent.parent / "credentials" / "kroger_tokens.json"
    if tokens_path.exists():
        logger.info("+ User tokens found (run --auth to refresh if expired)")
    else:
        logger.warning("  No user tokens found — run --auth to authenticate before adding to cart")

    logger.info("\n" + "=" * 60)
    logger.info("+ Health check complete")
    logger.info("=" * 60)
    return True


def add_items_to_cart(
    items: list[str],
    dry_run: bool = False,
    interactive: bool = True,
):
    """
    Search for each grocery item and add the best match to cart.

    Args:
        items: List of grocery item search terms.
        dry_run: If True, search and display results but don't add to cart.
        interactive: If True, prompt user to confirm each item.
    """
    client = KrogerClient()

    if not dry_run:
        if not client.authenticate_user():
            logger.error("Cannot add to cart without user authentication. Run --auth first.")
            sys.exit(1)

    logger.info("=" * 60)
    logger.info(f"Processing {len(items)} grocery items")
    if dry_run:
        logger.info("! DRY RUN — no items will be added to cart")
    logger.info("=" * 60)

    start_time = time.time()
    stats = {"searched": 0, "found": 0, "added": 0, "not_found": 0, "skipped": 0}
    cart_items = []  # Accumulate for batch add

    for i, term in enumerate(items, 1):
        term = term.strip()
        if not term or term.startswith("#"):
            continue

        # Parse quantity if present (format: "2x chicken thighs" or "chicken thighs x2")
        quantity = 1
        search_term = term
        if term[0].isdigit() and "x " in term.lower():
            parts = term.split("x ", 1)
            try:
                quantity = int(parts[0].strip())
                search_term = parts[1].strip()
            except ValueError:
                pass
        elif " x" in term.lower() and term.rstrip()[-1].isdigit():
            parts = term.rsplit("x", 1)
            try:
                quantity = int(parts[1].strip())
                search_term = parts[0].strip()
            except ValueError:
                pass

        stats["searched"] += 1
        logger.info(f"\n[{i}/{len(items)}] Searching: {search_term} (qty: {quantity})")

        product = client.search_and_select_product(search_term)

        if not product:
            logger.warning(f"  X No results for '{search_term}'")
            stats["not_found"] += 1
            continue

        stats["found"] += 1
        desc = product.get("description", "Unknown")
        brand = product.get("brand", "")
        size = product.get("size", "")
        price = product.get("price_display", "N/A")
        stock = "In stock" if product.get("in_stock") else "Check availability"

        display = f"  {brand} {desc}"
        if size:
            display += f" ({size})"
        display += f" — {price} [{stock}]"
        print(display)

        if interactive and not dry_run:
            response = input(f"  Add to cart? (qty {quantity}) [Y/n/s(kip)/q(uit)]: ").strip().lower()
            if response in ("n", "no"):
                stats["skipped"] += 1
                continue
            elif response in ("s", "skip"):
                stats["skipped"] += 1
                continue
            elif response in ("q", "quit"):
                break

        if not dry_run:
            cart_items.append({"upc": product["upc"], "quantity": quantity})
            stats["added"] += 1

    # Batch add to cart
    if cart_items and not dry_run:
        logger.info(f"\nAdding {len(cart_items)} items to cart...")
        try:
            success = client.add_to_cart(cart_items)
            if not success:
                logger.error("Failed to add items to cart")
                stats["added"] = 0
        except Exception as e:
            logger.error(f"Error adding items to cart: {e}")
            stats["added"] = 0

    # Summary
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"Grocery cart summary ({elapsed:.1f}s):")
    print(f"  Searched: {stats['searched']}")
    print(f"  Found:    {stats['found']}")
    if not dry_run:
        print(f"  Added:    {stats['added']}")
    print(f"  Skipped:  {stats['skipped']}")
    print(f"  Not found: {stats['not_found']}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Add grocery items to your Smith's/Kroger pickup cart"
    )
    parser.add_argument(
        "--find-store",
        type=str,
        metavar="ZIP",
        help="Find nearby Smith's stores by ZIP code",
    )
    parser.add_argument(
        "--chain",
        type=str,
        default="SMITHS",
        help="Store chain to search (default: SMITHS)",
    )
    parser.add_argument(
        "--auth",
        action="store_true",
        help="Run OAuth authentication flow",
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Verify configuration and connectivity",
    )
    parser.add_argument(
        "--file",
        type=str,
        metavar="PATH",
        help="Path to grocery list file (one item per line)",
    )
    parser.add_argument(
        "--items",
        nargs="+",
        metavar="ITEM",
        help="Grocery items to add (space-separated, quote multi-word items)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Search for products without adding to cart",
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip interactive confirmation for each item",
    )

    args = parser.parse_args()

    if args.find_store:
        find_store(args.find_store, chain=args.chain)
        return

    if args.auth:
        authenticate()
        return

    if args.health_check:
        success = health_check()
        sys.exit(0 if success else 1)

    # Build item list from file and/or CLI args
    items = []
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            logger.error(f"File not found: {args.file}")
            sys.exit(1)
        items.extend(file_path.read_text().strip().splitlines())

    if args.items:
        items.extend(args.items)

    if not items:
        parser.print_help()
        print("\nProvide items via --file or --items")
        sys.exit(1)

    add_items_to_cart(
        items,
        dry_run=args.dry_run,
        interactive=not args.no_confirm,
    )


if __name__ == "__main__":
    main()
