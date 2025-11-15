"""
Risk Manager Module
Manages trading risk, position sizing, and stop-loss logic
Implements "virtual stop loss" since Vietnam market doesn't have standard stop loss
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from loguru import logger
from utils.config import settings
from core.order_executor import Order, OrderSide, OrderType, order_executor


@dataclass
class Position:
    """Position model"""

    symbol: str
    quantity: int
    avg_entry_price: float
    current_price: float
    stop_loss_price: float
    take_profit_price: Optional[float] = None
    entry_time: datetime = None
    pnl: float = 0.0
    pnl_percent: float = 0.0

    def __post_init__(self):
        if self.entry_time is None:
            self.entry_time = datetime.now()
        self.update_pnl(self.current_price)

    def update_pnl(self, current_price: float):
        """Update P&L based on current price"""
        self.current_price = current_price
        self.pnl = (current_price - self.avg_entry_price) * self.quantity
        self.pnl_percent = (
            (current_price - self.avg_entry_price) / self.avg_entry_price
        )

    def should_stop_loss(self) -> bool:
        """Check if stop loss should be triggered"""
        return self.current_price <= self.stop_loss_price

    def should_take_profit(self) -> bool:
        """Check if take profit should be triggered"""
        if self.take_profit_price is None:
            return False
        return self.current_price >= self.take_profit_price

    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "avg_entry_price": self.avg_entry_price,
            "current_price": self.current_price,
            "stop_loss_price": self.stop_loss_price,
            "take_profit_price": self.take_profit_price,
            "pnl": self.pnl,
            "pnl_percent": self.pnl_percent,
            "entry_time": self.entry_time.isoformat(),
        }


class RiskManager:
    """
    Manages trading risk and implements risk control measures:
    1. Position sizing based on risk per trade
    2. Virtual stop-loss monitoring and execution
    3. Maximum drawdown protection
    4. Maximum position limits
    5. Trailing stop-loss
    """

    def __init__(self):
        self.positions: Dict[str, Position] = {}
        self.initial_capital = 1_000_000_000  # 1 billion VND default
        self.current_capital = self.initial_capital
        self.max_drawdown = 0.0
        self.peak_capital = self.initial_capital

        # Risk parameters from settings
        self.max_position_size = settings.max_position_size
        self.max_positions = settings.max_positions
        self.risk_per_trade = settings.risk_per_trade
        self.default_stop_loss_pct = settings.default_stop_loss_pct
        self.max_drawdown_pct = settings.max_drawdown_pct

    def calculate_position_size(
        self, symbol: str, entry_price: float, stop_loss_price: float
    ) -> int:
        """
        Calculate position size based on risk per trade
        Uses fixed fractional position sizing
        """
        # Calculate risk amount
        risk_amount = self.current_capital * self.risk_per_trade

        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss_price)

        if risk_per_share == 0:
            logger.warning(f"Risk per share is zero for {symbol}")
            return 0

        # Calculate number of shares
        shares = int(risk_amount / risk_per_share)

        # Apply position size limits
        max_shares_by_value = int(self.max_position_size / entry_price)
        shares = min(shares, max_shares_by_value)

        # Round down to lot size (100 shares in Vietnam)
        shares = (shares // 100) * 100

        logger.info(
            f"Position size for {symbol}: {shares} shares @ {entry_price:.2f} "
            f"(risk: {risk_amount:,.0f} VND, {self.risk_per_trade*100}%)"
        )

        return shares

    def calculate_stop_loss_price(self, entry_price: float, side: OrderSide) -> float:
        """
        Calculate stop-loss price based on entry price
        """
        if side == OrderSide.BUY:
            stop_loss = entry_price * (1 - self.default_stop_loss_pct)
        else:  # SELL (for short positions, not common in Vietnam)
            stop_loss = entry_price * (1 + self.default_stop_loss_pct)

        return stop_loss

    def can_open_position(self, symbol: str, position_value: float) -> Tuple[bool, str]:
        """
        Check if a new position can be opened based on risk rules
        Returns (can_open, reason)
        """
        # Check if already at max positions
        if len(self.positions) >= self.max_positions:
            return False, f"Maximum positions limit reached ({self.max_positions})"

        # Check if position already exists
        if symbol in self.positions:
            return False, f"Position already exists for {symbol}"

        # Check if position size exceeds limit
        if position_value > self.max_position_size:
            return (
                False,
                f"Position value {position_value:,.0f} exceeds limit {self.max_position_size:,.0f}",
            )

        # Check if we have enough capital
        if position_value > self.current_capital:
            return False, f"Insufficient capital: need {position_value:,.0f}, have {self.current_capital:,.0f}"

        # Check max drawdown
        if self.max_drawdown >= self.max_drawdown_pct:
            return False, f"Maximum drawdown {self.max_drawdown*100:.1f}% exceeded"

        return True, "OK"

    def open_position(
        self,
        symbol: str,
        quantity: int,
        entry_price: float,
        stop_loss_price: float = None,
        take_profit_price: float = None,
    ) -> Optional[Position]:
        """
        Open a new position with risk management
        """
        position_value = quantity * entry_price

        # Check if position can be opened
        can_open, reason = self.can_open_position(symbol, position_value)
        if not can_open:
            logger.warning(f"Cannot open position for {symbol}: {reason}")
            return None

        # Calculate stop loss if not provided
        if stop_loss_price is None:
            stop_loss_price = self.calculate_stop_loss_price(entry_price, OrderSide.BUY)

        # Create position
        position = Position(
            symbol=symbol,
            quantity=quantity,
            avg_entry_price=entry_price,
            current_price=entry_price,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
        )

        self.positions[symbol] = position
        self.current_capital -= position_value

        logger.bind(TRADE=True).info(
            f"OPEN POSITION: {symbol} | Qty: {quantity} | Entry: {entry_price:.2f} | "
            f"Stop Loss: {stop_loss_price:.2f} | Capital: {self.current_capital:,.0f}"
        )

        return position

    def close_position(self, symbol: str, exit_price: float, reason: str = "") -> bool:
        """
        Close a position and update capital
        """
        if symbol not in self.positions:
            logger.warning(f"No position found for {symbol}")
            return False

        position = self.positions[symbol]
        position.update_pnl(exit_price)

        # Update capital
        exit_value = position.quantity * exit_price
        self.current_capital += exit_value

        # Update peak and drawdown
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        else:
            drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
            self.max_drawdown = max(self.max_drawdown, drawdown)

        logger.bind(TRADE=True).info(
            f"CLOSE POSITION: {symbol} | Exit: {exit_price:.2f} | "
            f"P&L: {position.pnl:+,.0f} VND ({position.pnl_percent:+.2%}) | "
            f"Reason: {reason} | Capital: {self.current_capital:,.0f}"
        )

        # Remove position
        del self.positions[symbol]

        return True

    def update_position_price(self, symbol: str, current_price: float):
        """
        Update position with current price
        """
        if symbol in self.positions:
            self.positions[symbol].update_pnl(current_price)

    def check_stop_loss(self, symbol: str) -> bool:
        """
        Check if stop loss should be triggered for a position
        Returns True if stop loss triggered and position closed
        """
        if symbol not in self.positions:
            return False

        position = self.positions[symbol]

        if position.should_stop_loss():
            logger.warning(
                f"STOP LOSS TRIGGERED: {symbol} | "
                f"Price: {position.current_price:.2f} <= Stop: {position.stop_loss_price:.2f}"
            )

            # Execute stop loss order
            order = order_executor.place_order(
                symbol=symbol,
                side=OrderSide.SELL,
                quantity=position.quantity,
                price=position.current_price,
                order_type=OrderType.MARKET,
            )

            if order:
                self.close_position(symbol, position.current_price, "Stop Loss")
                return True

        return False

    def check_take_profit(self, symbol: str) -> bool:
        """
        Check if take profit should be triggered for a position
        Returns True if take profit triggered and position closed
        """
        if symbol not in self.positions:
            return False

        position = self.positions[symbol]

        if position.should_take_profit():
            logger.info(
                f"TAKE PROFIT TRIGGERED: {symbol} | "
                f"Price: {position.current_price:.2f} >= Target: {position.take_profit_price:.2f}"
            )

            # Execute take profit order
            order = order_executor.place_order(
                symbol=symbol,
                side=OrderSide.SELL,
                quantity=position.quantity,
                price=position.current_price,
                order_type=OrderType.LIMIT,
            )

            if order:
                self.close_position(symbol, position.current_price, "Take Profit")
                return True

        return False

    def update_trailing_stop(self, symbol: str, trailing_pct: float = 0.05):
        """
        Update trailing stop-loss based on current price
        Trailing stop moves up as price increases, but never moves down
        """
        if symbol not in self.positions:
            return

        position = self.positions[symbol]

        # Calculate new trailing stop
        new_stop = position.current_price * (1 - trailing_pct)

        # Only update if new stop is higher than current stop
        if new_stop > position.stop_loss_price:
            old_stop = position.stop_loss_price
            position.stop_loss_price = new_stop
            logger.info(
                f"TRAILING STOP UPDATE: {symbol} | "
                f"Old: {old_stop:.2f} -> New: {new_stop:.2f} | "
                f"Current Price: {position.current_price:.2f}"
            )

    def monitor_positions(self):
        """
        Monitor all positions for stop loss and take profit triggers
        Should be called regularly (e.g., every time price updates)
        """
        symbols_to_check = list(self.positions.keys())

        for symbol in symbols_to_check:
            # Check stop loss first (higher priority)
            if self.check_stop_loss(symbol):
                continue

            # Then check take profit
            if self.check_take_profit(symbol):
                continue

            # Update trailing stop if position is profitable
            position = self.positions.get(symbol)
            if position and position.pnl_percent > 0.05:  # 5% profit
                self.update_trailing_stop(symbol, trailing_pct=0.03)

    def get_portfolio_summary(self) -> Dict:
        """
        Get portfolio summary statistics
        """
        total_pnl = sum(pos.pnl for pos in self.positions.values())
        total_position_value = sum(
            pos.quantity * pos.current_price for pos in self.positions.values()
        )

        return {
            "initial_capital": self.initial_capital,
            "current_capital": self.current_capital,
            "total_position_value": total_position_value,
            "total_value": self.current_capital + total_position_value,
            "total_pnl": total_pnl,
            "total_return": (
                (self.current_capital + total_position_value - self.initial_capital)
                / self.initial_capital
            ),
            "max_drawdown": self.max_drawdown,
            "num_positions": len(self.positions),
            "positions": [pos.to_dict() for pos in self.positions.values()],
        }


# Global instance
risk_manager = RiskManager()
