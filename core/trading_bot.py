"""
Trading Bot Main Orchestrator
Coordinates all components to execute automated trading strategies
"""
import time
import signal
import sys
from typing import List, Set
from datetime import datetime, timedelta
from threading import Thread, Event
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from utils.config import settings
from core.price_stream import price_stream_manager, PriceData
from core.signal_engine import signal_engine, SignalType, SignalStrength
from core.order_executor import order_executor, OrderSide, OrderType
from core.risk_manager import risk_manager
from utils.notifications import NotificationManager


class TradingBot:
    """
    Main Trading Bot that orchestrates all components:
    - Price streaming via MQTT
    - Signal generation from technical analysis
    - Order execution via REST API
    - Risk management with virtual stop-loss
    - DCA (Dollar Cost Averaging) bot
    """

    def __init__(self, symbols: List[str]):
        self.symbols = [s.upper() for s in symbols]
        self.is_running = False
        self.stop_event = Event()
        self.scheduler = BackgroundScheduler()
        self.notification_manager = NotificationManager()

        # Track processed signals to avoid duplicates
        self.processed_signals: Set[str] = set()

        # DCA bot settings
        self.dca_enabled = settings.dca_enabled
        self.dca_symbols = settings.dca_symbols_list
        self.dca_interval_hours = settings.dca_interval_hours
        self.dca_amount = settings.dca_amount_per_order

        logger.info(f"Trading Bot initialized for symbols: {self.symbols}")
        logger.info(f"Trading Mode: {settings.trading_mode.upper()}")
        logger.info(f"DCA Enabled: {self.dca_enabled}")

    def _on_price_update(self, price_data: PriceData):
        """
        Callback when price data is received from MQTT
        This is the main event loop of the bot
        """
        try:
            symbol = price_data.symbol

            # Update price history in signal engine
            signal_engine.update_price(
                symbol=symbol,
                price=price_data.price,
                volume=price_data.volume,
                high=price_data.high,
                low=price_data.low,
            )

            # Update risk manager with current price
            risk_manager.update_position_price(symbol, price_data.price)

            # Monitor positions for stop-loss and take-profit
            risk_manager.monitor_positions()

            # Generate trading signal
            signal = signal_engine.generate_signal(symbol, price_data.price)

            if signal and signal.signal_type != SignalType.HOLD:
                self._process_signal(signal, price_data)

        except Exception as e:
            logger.error(f"Error processing price update for {price_data.symbol}: {e}")

    def _process_signal(self, signal, price_data: PriceData):
        """
        Process a trading signal and execute orders if appropriate
        """
        # Create unique signal ID to avoid duplicate processing
        signal_id = f"{signal.symbol}_{signal.signal_type.value}_{int(time.time()/60)}"

        if signal_id in self.processed_signals:
            return

        logger.info(f"Signal: {signal}")

        # Only process strong signals
        if signal.strength == SignalStrength.WEAK:
            logger.info(f"Skipping weak signal for {signal.symbol}")
            return

        # Process BUY signal
        if signal.signal_type == SignalType.BUY:
            self._execute_buy(signal, price_data)

        # Process SELL signal
        elif signal.signal_type == SignalType.SELL:
            self._execute_sell(signal, price_data)

        # Process CUTLOSS signal
        elif signal.signal_type == SignalType.CUTLOSS:
            self._execute_cutloss(signal, price_data)

        # Mark signal as processed
        self.processed_signals.add(signal_id)

        # Clean up old signals (keep only last hour)
        current_time = int(time.time() / 60)
        self.processed_signals = {
            sid for sid in self.processed_signals if int(sid.split("_")[-1]) > current_time - 60
        }

    def _execute_buy(self, signal, price_data: PriceData):
        """
        Execute BUY order based on signal
        """
        symbol = signal.symbol
        entry_price = price_data.price

        # Calculate stop loss
        stop_loss_price = risk_manager.calculate_stop_loss_price(
            entry_price, OrderSide.BUY
        )

        # Calculate position size
        quantity = risk_manager.calculate_position_size(
            symbol, entry_price, stop_loss_price
        )

        if quantity == 0:
            logger.warning(f"Position size is 0 for {symbol}, skipping buy")
            return

        # Check if we can open position
        can_open, reason = risk_manager.can_open_position(
            symbol, quantity * entry_price
        )

        if not can_open:
            logger.warning(f"Cannot open position for {symbol}: {reason}")
            self.notification_manager.send_notification(
                f"❌ BUY signal for {symbol} @ {entry_price:.2f} - Cannot open: {reason}"
            )
            return

        # Place buy order
        logger.info(f"Executing BUY: {symbol} | Qty: {quantity} @ {entry_price:.2f}")

        order = order_executor.place_order(
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=quantity,
            price=entry_price,
            order_type=OrderType.LIMIT,
        )

        if order:
            # Open position in risk manager
            position = risk_manager.open_position(
                symbol=symbol,
                quantity=quantity,
                entry_price=entry_price,
                stop_loss_price=stop_loss_price,
            )

            # Send notification
            self.notification_manager.send_notification(
                f"✅ BUY {symbol}\n"
                f"Qty: {quantity} @ {entry_price:.2f}\n"
                f"Stop Loss: {stop_loss_price:.2f}\n"
                f"Reason: {signal.reason}"
            )
        else:
            logger.error(f"Failed to place buy order for {symbol}")

    def _execute_sell(self, signal, price_data: PriceData):
        """
        Execute SELL order based on signal
        """
        symbol = signal.symbol
        exit_price = price_data.price

        # Check if we have a position to sell
        if symbol not in risk_manager.positions:
            logger.info(f"No position to sell for {symbol}")
            return

        position = risk_manager.positions[symbol]

        # Place sell order
        logger.info(
            f"Executing SELL: {symbol} | Qty: {position.quantity} @ {exit_price:.2f}"
        )

        order = order_executor.place_order(
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=position.quantity,
            price=exit_price,
            order_type=OrderType.LIMIT,
        )

        if order:
            # Close position
            risk_manager.close_position(symbol, exit_price, f"Signal: {signal.reason}")

            # Send notification
            self.notification_manager.send_notification(
                f"📤 SELL {symbol}\n"
                f"Qty: {position.quantity} @ {exit_price:.2f}\n"
                f"P&L: {position.pnl:+,.0f} VND ({position.pnl_percent:+.2%})\n"
                f"Reason: {signal.reason}"
            )

    def _execute_cutloss(self, signal, price_data: PriceData):
        """
        Execute CUTLOSS order based on signal
        """
        symbol = signal.symbol
        exit_price = price_data.price

        # Check if we have a position to cut loss
        if symbol not in risk_manager.positions:
            logger.info(f"No position to cut loss for {symbol}")
            return

        position = risk_manager.positions[symbol]

        # Place market sell order for immediate execution
        logger.warning(
            f"Executing CUTLOSS: {symbol} | Qty: {position.quantity} @ {exit_price:.2f}"
        )

        order = order_executor.place_order(
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=position.quantity,
            price=exit_price,
            order_type=OrderType.MARKET,
        )

        if order:
            # Close position
            risk_manager.close_position(symbol, exit_price, f"CUTLOSS: {signal.reason}")

            # Send notification
            self.notification_manager.send_notification(
                f"⚠️ CUTLOSS {symbol}\n"
                f"Qty: {position.quantity} @ {exit_price:.2f}\n"
                f"P&L: {position.pnl:+,.0f} VND ({position.pnl_percent:+.2%})\n"
                f"Reason: {signal.reason}"
            )

    def _dca_job(self):
        """
        DCA (Dollar Cost Averaging) job
        Executes periodic buys for configured symbols
        """
        if not self.dca_enabled:
            return

        logger.info("Running DCA job...")

        for symbol in self.dca_symbols:
            try:
                # Get latest price
                price_data = price_stream_manager.get_latest_price(symbol)
                if not price_data:
                    logger.warning(f"No price data for DCA symbol {symbol}")
                    continue

                entry_price = price_data.price

                # Calculate quantity based on DCA amount
                quantity = int(self.dca_amount / entry_price)
                quantity = (quantity // 100) * 100  # Round to lot size

                if quantity == 0:
                    logger.warning(f"DCA quantity is 0 for {symbol}")
                    continue

                # Calculate stop loss
                stop_loss_price = risk_manager.calculate_stop_loss_price(
                    entry_price, OrderSide.BUY
                )

                # Check if we can open position
                can_open, reason = risk_manager.can_open_position(
                    symbol, quantity * entry_price
                )

                if not can_open:
                    logger.warning(f"DCA: Cannot open position for {symbol}: {reason}")
                    continue

                # Place buy order
                logger.info(
                    f"DCA BUY: {symbol} | Qty: {quantity} @ {entry_price:.2f}"
                )

                order = order_executor.place_order(
                    symbol=symbol,
                    side=OrderSide.BUY,
                    quantity=quantity,
                    price=entry_price,
                    order_type=OrderType.LIMIT,
                )

                if order:
                    # Open position in risk manager
                    risk_manager.open_position(
                        symbol=symbol,
                        quantity=quantity,
                        entry_price=entry_price,
                        stop_loss_price=stop_loss_price,
                    )

                    # Send notification
                    self.notification_manager.send_notification(
                        f"🔄 DCA BUY {symbol}\n"
                        f"Qty: {quantity} @ {entry_price:.2f}\n"
                        f"Amount: {quantity * entry_price:,.0f} VND"
                    )

                # Add delay between orders
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error in DCA job for {symbol}: {e}")

    def _portfolio_summary_job(self):
        """
        Periodic job to log and send portfolio summary
        """
        summary = risk_manager.get_portfolio_summary()

        logger.info(
            f"Portfolio Summary | "
            f"Total Value: {summary['total_value']:,.0f} | "
            f"P&L: {summary['total_pnl']:+,.0f} ({summary['total_return']:+.2%}) | "
            f"Positions: {summary['num_positions']} | "
            f"Max Drawdown: {summary['max_drawdown']:.2%}"
        )

    def start(self):
        """
        Start the trading bot
        """
        logger.info("=" * 60)
        logger.info("Starting Trading Bot...")
        logger.info("=" * 60)

        # Start price stream
        logger.info("Starting price stream manager...")
        if not price_stream_manager.start():
            logger.error("Failed to start price stream manager")
            return False

        # Register price callback
        price_stream_manager.add_callback(self._on_price_update)

        # Subscribe to symbols
        logger.info(f"Subscribing to {len(self.symbols)} symbols...")
        price_stream_manager.subscribe(self.symbols)

        # Subscribe to DCA symbols if enabled
        if self.dca_enabled:
            logger.info(f"Subscribing to {len(self.dca_symbols)} DCA symbols...")
            price_stream_manager.subscribe(self.dca_symbols)

        # Start scheduler for periodic jobs
        self.scheduler.add_job(
            self._portfolio_summary_job, "interval", minutes=15, id="portfolio_summary"
        )

        if self.dca_enabled:
            self.scheduler.add_job(
                self._dca_job,
                "interval",
                hours=self.dca_interval_hours,
                id="dca_job",
            )

        self.scheduler.start()

        self.is_running = True
        logger.info("Trading Bot started successfully!")

        # Send startup notification
        self.notification_manager.send_notification(
            f"🚀 Trading Bot Started\n"
            f"Mode: {settings.trading_mode.upper()}\n"
            f"Symbols: {', '.join(self.symbols[:5])}{'...' if len(self.symbols) > 5 else ''}\n"
            f"DCA: {'Enabled' if self.dca_enabled else 'Disabled'}"
        )

        return True

    def stop(self):
        """
        Stop the trading bot
        """
        logger.info("Stopping Trading Bot...")

        self.is_running = False
        self.stop_event.set()

        # Stop scheduler
        if self.scheduler.running:
            self.scheduler.shutdown()

        # Unsubscribe from symbols
        price_stream_manager.unsubscribe(self.symbols)
        if self.dca_enabled:
            price_stream_manager.unsubscribe(self.dca_symbols)

        # Stop price stream
        price_stream_manager.stop()

        # Send shutdown notification
        summary = risk_manager.get_portfolio_summary()
        self.notification_manager.send_notification(
            f"🛑 Trading Bot Stopped\n"
            f"Final P&L: {summary['total_pnl']:+,.0f} VND ({summary['total_return']:+.2%})\n"
            f"Max Drawdown: {summary['max_drawdown']:.2%}"
        )

        logger.info("Trading Bot stopped")

    def run(self):
        """
        Run the trading bot (blocking)
        """
        if not self.start():
            logger.error("Failed to start trading bot")
            return

        # Setup signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            logger.info("Received shutdown signal")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Keep running
        logger.info("Trading Bot is running. Press Ctrl+C to stop.")
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self.stop()
