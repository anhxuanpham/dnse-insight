#!/usr/bin/env python3
"""
DNSE Trading Bot - Main Entry Point
Real-time automated trading bot for Vietnamese stock market
"""
import sys
import argparse
from pathlib import Path
from loguru import logger

from utils.config import settings
from core.trading_bot import TradingBot


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="DNSE Trading Bot - Automated trading for Vietnamese stock market",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run bot with VN30 stocks
  python main.py --symbols VCB VHM VIC FPT

  # Run bot with custom symbols and DCA
  python main.py --symbols VCB VHM --dca --dca-symbols VCB VIC

  # Run in live trading mode (default is paper)
  python main.py --symbols VCB --mode live

  # Run with all VN30 stocks
  python main.py --vn30
        """,
    )

    parser.add_argument(
        "--symbols",
        nargs="+",
        help="Stock symbols to trade (e.g., VCB VHM VIC)",
    )

    parser.add_argument(
        "--vn30",
        action="store_true",
        help="Trade all VN30 stocks",
    )

    parser.add_argument(
        "--mode",
        choices=["paper", "live"],
        default=settings.trading_mode,
        help="Trading mode: paper (simulation) or live (real money)",
    )

    parser.add_argument(
        "--dca",
        action="store_true",
        help="Enable DCA (Dollar Cost Averaging) bot",
    )

    parser.add_argument(
        "--dca-symbols",
        nargs="+",
        help="Symbols for DCA bot",
    )

    parser.add_argument(
        "--dca-interval",
        type=int,
        default=settings.dca_interval_hours,
        help="DCA interval in hours",
    )

    parser.add_argument(
        "--dca-amount",
        type=float,
        default=settings.dca_amount_per_order,
        help="DCA amount per order in VND",
    )

    return parser.parse_args()


def get_vn30_symbols():
    """Get list of VN30 stock symbols"""
    return [
        "VCB",
        "VHM",
        "VIC",
        "VNM",
        "FPT",
        "GAS",
        "MSN",
        "MWG",
        "VPB",
        "HPG",
        "TCB",
        "BID",
        "CTG",
        "SAB",
        "SSI",
        "VRE",
        "PLX",
        "POW",
        "MBB",
        "ACB",
        "GVR",
        "HDB",
        "TPB",
        "VJC",
        "PDR",
        "STB",
        "NVL",
        "BCM",
        "KDH",
        "VCG",
    ]


def main():
    """Main entry point"""
    args = parse_arguments()

    # Determine symbols to trade
    if args.vn30:
        symbols = get_vn30_symbols()
        logger.info("Trading VN30 stocks")
    elif args.symbols:
        symbols = args.symbols
    else:
        logger.error("No symbols specified. Use --symbols or --vn30")
        sys.exit(1)

    # Update settings based on arguments
    if args.mode:
        settings.trading_mode = args.mode

    if args.dca:
        settings.dca_enabled = True

    if args.dca_symbols:
        settings.dca_symbols = ",".join(args.dca_symbols)

    if args.dca_interval:
        settings.dca_interval_hours = args.dca_interval

    if args.dca_amount:
        settings.dca_amount_per_order = args.dca_amount

    # Print configuration
    logger.info("=" * 60)
    logger.info("DNSE Trading Bot Configuration")
    logger.info("=" * 60)
    logger.info(f"Trading Mode: {settings.trading_mode.upper()}")
    logger.info(f"Symbols: {', '.join(symbols)}")
    logger.info(f"DCA Enabled: {settings.dca_enabled}")
    if settings.dca_enabled:
        logger.info(f"DCA Symbols: {settings.dca_symbols}")
        logger.info(f"DCA Interval: {settings.dca_interval_hours} hours")
        logger.info(f"DCA Amount: {settings.dca_amount_per_order:,.0f} VND")
    logger.info("=" * 60)

    # Warning for live trading
    if settings.trading_mode == "live":
        logger.warning("⚠️  LIVE TRADING MODE - REAL MONEY AT RISK ⚠️")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Exiting...")
            sys.exit(0)

    # Create and run trading bot
    try:
        bot = TradingBot(symbols=symbols)
        bot.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
