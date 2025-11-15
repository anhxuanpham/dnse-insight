#!/usr/bin/env python3
"""
Example: Using Market Screener
"""
from screener.core.scanner_engine import scanner_engine
from screener.filters.volume_surge import VolumeSurgeFilter
from screener.filters.breakout import BreakoutFilter
from screener.filters.price_momentum import PriceMomentumFilter, NewHighLowFilter
from screener.filters.technical_indicators import RSIExtremeFilter, MovingAverageCrossFilter

from core.price_stream import price_stream_manager
from loguru import logger


def main():
    """Run market screener example"""
    # Setup screener
    logger.info("Setting up market screener...")

    # Add filters
    scanner_engine.add_filter(VolumeSurgeFilter(threshold=2.0))
    scanner_engine.add_filter(BreakoutFilter())
    scanner_engine.add_filter(PriceMomentumFilter(threshold=0.03))
    scanner_engine.add_filter(NewHighLowFilter())
    scanner_engine.add_filter(RSIExtremeFilter())
    scanner_engine.add_filter(MovingAverageCrossFilter())

    # Set symbols to scan
    symbols = ["VCB", "VHM", "VIC", "FPT", "HPG"]
    scanner_engine.set_symbols(symbols)

    # Add callback
    def on_scan_hit(result):
        logger.success(f"🎯 SCAN HIT: [{result.priority.name}] {result.message}")

    scanner_engine.add_callback(on_scan_hit)

    # Start price stream
    price_stream_manager.start()
    price_stream_manager.subscribe(symbols)

    logger.info("Screener running... Press Ctrl+C to stop")

    # Run scan loop
    import time
    try:
        while True:
            results = scanner_engine.scan_all()
            if results:
                logger.info(f"Found {len(results)} opportunities")

            time.sleep(60)  # Scan every minute

    except KeyboardInterrupt:
        logger.info("Stopping screener...")
        price_stream_manager.stop()


if __name__ == "__main__":
    main()
