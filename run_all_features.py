#!/usr/bin/env python3
"""
Run All Features - Comprehensive Trading System Runner
Starts all components of the DNSE Insight trading system
"""
import sys
import asyncio
import signal
from threading import Thread
from loguru import logger

from utils.config import settings
from core.trading_bot import TradingBot
from core.price_stream import price_stream_manager
from screener.core.scanner_engine import scanner_engine
from screener.filters.volume_surge import VolumeSurgeFilter
from screener.filters.breakout import BreakoutFilter
from screener.filters.price_momentum import PriceMomentumFilter, NewHighLowFilter
from screener.filters.technical_indicators import RSIExtremeFilter, MovingAverageCrossFilter
from portfolio.rebalancer import portfolio_rebalancer, AllocationTarget
from alerts.alert_system import alert_system, AlertChannel, PortfolioAlert
from backtest.data.tick_recorder import tick_recorder


class DNSEInsightSystem:
    """
    Comprehensive DNSE Insight Trading System

    Integrates all features:
    1. Trading Bot with Auto-trading
    2. Market Screener with Filters
    3. Portfolio Rebalancing
    4. Multi-channel Alerts
    5. Tick Data Recording for Backtesting
    6. Dashboard API (run separately)
    """

    def __init__(self, symbols: list):
        self.symbols = symbols
        self.trading_bot = None
        self.is_running = False

    def setup_screener(self):
        """Setup market screener with filters"""
        logger.info("Setting up market screener...")

        # Add filters
        scanner_engine.add_filter(VolumeSurgeFilter(threshold=2.0))
        scanner_engine.add_filter(BreakoutFilter())
        scanner_engine.add_filter(PriceMomentumFilter(threshold=0.03))
        scanner_engine.add_filter(NewHighLowFilter())
        scanner_engine.add_filter(RSIExtremeFilter())
        scanner_engine.add_filter(MovingAverageCrossFilter())

        # Set symbols to scan
        scanner_engine.set_symbols(self.symbols)

        # Add callback for scan results
        def on_scan_result(result):
            logger.info(f"SCAN HIT: {result.message}")
            # Send alert
            from alerts.alert_system import Alert, AlertPriority
            alert = Alert(
                title=f"Market Scanner: {result.symbol}",
                message=result.message,
                priority=AlertPriority[result.priority.name],
                channels=[AlertChannel.TELEGRAM],
            )
            alert_system.send_alert(alert)

        scanner_engine.add_callback(on_scan_result)

        logger.info(f"Screener configured with {len(scanner_engine.filters)} filters")

    def setup_rebalancer(self):
        """Setup portfolio rebalancer"""
        logger.info("Setting up portfolio rebalancer...")

        # Example allocation targets
        targets = [
            AllocationTarget(symbol="VCB", target_percent=0.25),
            AllocationTarget(symbol="VHM", target_percent=0.20),
            AllocationTarget(symbol="VIC", target_percent=0.15),
            AllocationTarget(symbol="FPT", target_percent=0.15),
            AllocationTarget(symbol="CASH", target_percent=0.25),
        ]

        portfolio_rebalancer.set_allocation_targets(targets)
        logger.info("Portfolio rebalancer configured")

    def setup_alerts(self):
        """Setup alert system"""
        logger.info("Setting up alert system...")

        # Add portfolio alerts
        alert_system.add_rule(
            PortfolioAlert(
                threshold_pct=0.05,  # 5% gain
                condition="gain",
                channels=[AlertChannel.TELEGRAM],
            )
        )

        alert_system.add_rule(
            PortfolioAlert(
                threshold_pct=0.03,  # 3% loss
                condition="loss",
                channels=[AlertChannel.TELEGRAM, AlertChannel.EMAIL],
            )
        )

        logger.info("Alert system configured")

    def setup_tick_recorder(self):
        """Setup tick data recorder"""
        logger.info("Setting up tick data recorder...")

        # Add callback to price stream to record ticks
        def record_tick(price_data):
            tick_recorder.record_tick(price_data)

        price_stream_manager.add_callback(record_tick)

        logger.info("Tick data recorder configured")

    async def run_screener_loop(self):
        """Run screener in background"""
        while self.is_running:
            try:
                # Scan all symbols
                results = scanner_engine.scan_all()
                if results:
                    logger.info(f"Scanner found {len(results)} opportunities")

                # Wait before next scan
                await asyncio.sleep(60)  # Scan every minute

            except Exception as e:
                logger.error(f"Error in screener loop: {e}")
                await asyncio.sleep(5)

    async def run_rebalancer_loop(self):
        """Run rebalancer in background"""
        while self.is_running:
            try:
                # Check if rebalancing needed
                if portfolio_rebalancer.needs_rebalancing():
                    logger.warning("Portfolio needs rebalancing!")

                    # Get report
                    report = portfolio_rebalancer.get_rebalance_report()
                    logger.info(f"Rebalancing report: {report}")

                    # Execute rebalancing (dry run by default)
                    # Change to dry_run=False to execute for real
                    portfolio_rebalancer.execute_rebalance(dry_run=True)

                # Check every hour
                await asyncio.sleep(3600)

            except Exception as e:
                logger.error(f"Error in rebalancer loop: {e}")
                await asyncio.sleep(60)

    def start(self):
        """Start all system components"""
        logger.info("=" * 80)
        logger.info("Starting DNSE Insight Comprehensive Trading System")
        logger.info("=" * 80)

        # Setup components
        self.setup_screener()
        self.setup_rebalancer()
        self.setup_alerts()
        self.setup_tick_recorder()

        # Start trading bot
        self.trading_bot = TradingBot(symbols=self.symbols)
        if not self.trading_bot.start():
            logger.error("Failed to start trading bot")
            return False

        self.is_running = True

        # Start background tasks
        logger.info("Starting background tasks...")

        # Run screener loop
        screener_thread = Thread(target=lambda: asyncio.run(self.run_screener_loop()))
        screener_thread.daemon = True
        screener_thread.start()

        # Run rebalancer loop
        rebalancer_thread = Thread(target=lambda: asyncio.run(self.run_rebalancer_loop()))
        rebalancer_thread.daemon = True
        rebalancer_thread.start()

        logger.info("All components started successfully!")
        logger.info("=" * 80)

        return True

    def stop(self):
        """Stop all components"""
        logger.info("Stopping DNSE Insight System...")

        self.is_running = False

        if self.trading_bot:
            self.trading_bot.stop()

        logger.info("System stopped")


def main():
    """Main entry point"""
    # Define symbols to trade/monitor
    symbols = [
        "VCB", "VHM", "VIC", "FPT", "HPG",
        "VNM", "GAS", "MSN", "MWG", "VPB",
    ]

    # Create and start system
    system = DNSEInsightSystem(symbols)

    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        system.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start system
    if system.start():
        logger.info("DNSE Insight System is running. Press Ctrl+C to stop.")

        # Keep running
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            system.stop()
    else:
        logger.error("Failed to start system")
        sys.exit(1)


if __name__ == "__main__":
    main()
