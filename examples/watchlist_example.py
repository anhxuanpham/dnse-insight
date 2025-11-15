#!/usr/bin/env python3
"""
Example: Watchlist Management
Demonstrates how to manage watchlists programmatically
"""
from core.watchlist_manager import watchlist_manager
from loguru import logger


def main():
    """Watchlist management examples"""
    logger.info("=" * 60)
    logger.info("WATCHLIST MANAGEMENT EXAMPLES")
    logger.info("=" * 60)

    # 1. View all watchlists
    logger.info("\n1. All Watchlists:")
    watchlists = watchlist_manager.get_all_watchlists()
    for wl in watchlists:
        logger.info(f"  - {wl.name}: {len(wl.symbols)} symbols (ID: {wl.id})")

    # 2. Get default watchlist
    logger.info("\n2. Default Watchlist:")
    default_wl = watchlist_manager.get_default_watchlist()
    if default_wl:
        logger.info(f"  Name: {default_wl.name}")
        logger.info(f"  Symbols: {', '.join(default_wl.symbols[:10])}...")

    # 3. Create custom watchlist
    logger.info("\n3. Creating Custom Watchlist:")
    custom_wl = watchlist_manager.create_watchlist(
        name="My Portfolio",
        description="Stocks I'm currently trading",
        symbols=["VCB", "VHM", "FPT", "HPG"],
        color="#10b981"  # Green
    )
    logger.info(f"  Created: {custom_wl.name} with {len(custom_wl.symbols)} symbols")

    # 4. Add symbols
    logger.info("\n4. Adding Symbols:")
    watchlist_manager.add_symbol(custom_wl.id, "MWG")
    watchlist_manager.add_symbol(custom_wl.id, "VNM")
    updated_wl = watchlist_manager.get_watchlist(custom_wl.id)
    logger.info(f"  Symbols now: {', '.join(updated_wl.symbols)}")

    # 5. Remove symbol
    logger.info("\n5. Removing Symbol:")
    watchlist_manager.remove_symbol(custom_wl.id, "HPG")
    updated_wl = watchlist_manager.get_watchlist(custom_wl.id)
    logger.info(f"  Symbols now: {', '.join(updated_wl.symbols)}")

    # 6. Search symbols
    logger.info("\n6. Search Symbols (containing 'V'):")
    found = watchlist_manager.search_symbols("V")
    logger.info(f"  Found: {', '.join(found[:10])}")

    # 7. Export to CSV
    logger.info("\n7. Export to CSV:")
    csv_file = "data/my_portfolio.csv"
    watchlist_manager.export_to_csv(custom_wl.id, csv_file)
    logger.info(f"  Exported to: {csv_file}")

    # 8. Export to JSON
    logger.info("\n8. Export to JSON:")
    json_file = "data/my_portfolio.json"
    watchlist_manager.export_to_json(custom_wl.id, json_file)
    logger.info(f"  Exported to: {json_file}")

    # 9. Get all unique symbols
    logger.info("\n9. All Unique Symbols Across Watchlists:")
    all_symbols = watchlist_manager.get_all_unique_symbols()
    logger.info(f"  Total: {len(all_symbols)} unique symbols")
    logger.info(f"  Examples: {', '.join(all_symbols[:15])}")

    # 10. Update watchlist
    logger.info("\n10. Updating Watchlist:")
    watchlist_manager.update_watchlist(
        custom_wl.id,
        name="My Active Trades",
        description="Updated description",
        color="#f59e0b"  # Orange
    )
    updated_wl = watchlist_manager.get_watchlist(custom_wl.id)
    logger.info(f"  Updated name: {updated_wl.name}")
    logger.info(f"  Updated color: {updated_wl.color}")

    logger.info("\n" + "=" * 60)
    logger.info("WATCHLIST MANAGEMENT COMPLETE")
    logger.info("=" * 60)

    # Cleanup (optional)
    # watchlist_manager.delete_watchlist(custom_wl.id)


if __name__ == "__main__":
    main()
