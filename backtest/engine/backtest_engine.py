"""
Backtesting Engine
Test trading strategies using historical data
"""
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

from core.signal_engine import SignalEngine, SignalType
from core.risk_manager import RiskManager


@dataclass
class BacktestTrade:
    """Backtest trade record"""
    symbol: str
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime]
    exit_price: Optional[float]
    quantity: int
    pnl: float = 0.0
    pnl_percent: float = 0.0
    holding_period: Optional[timedelta] = None


class BacktestEngine:
    """
    Backtesting Engine for Strategy Testing

    Features:
    - Replay historical tick data
    - Test trading strategies
    - Calculate performance metrics
    - Walk-forward analysis
    """

    def __init__(self, initial_capital: float = 100_000_000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.trades: List[BacktestTrade] = []
        self.equity_curve = []

    def run_backtest(
        self,
        data: pd.DataFrame,
        strategy_func: Callable,
        symbol: str = "TEST",
    ) -> Dict:
        """
        Run backtest on historical data

        Args:
            data: DataFrame with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            strategy_func: Function that generates signals
            symbol: Symbol being tested

        Returns:
            Backtest results dictionary
        """
        logger.info(f"Running backtest on {symbol} with {len(data)} data points")

        signal_engine = SignalEngine()
        risk_manager = RiskManager()
        risk_manager.initial_capital = self.initial_capital
        risk_manager.current_capital = self.initial_capital

        current_position = None

        for idx, row in data.iterrows():
            timestamp = row['timestamp']
            close = row['close']
            high = row['high']
            low = row['low']
            volume = row['volume']

            # Update signal engine
            signal_engine.update_price(symbol, close, volume, high, low)

            # Update position price
            if current_position:
                current_position.current_price = close

            # Generate signal
            signal = signal_engine.generate_signal(symbol, close)

            if not signal:
                continue

            # Execute based on signal
            if signal.signal_type == SignalType.BUY and not current_position:
                # Calculate position size
                stop_loss = close * 0.97
                quantity = risk_manager.calculate_position_size(symbol, close, stop_loss)

                if quantity > 0:
                    current_position = BacktestTrade(
                        symbol=symbol,
                        entry_time=timestamp,
                        entry_price=close,
                        exit_time=None,
                        exit_price=None,
                        quantity=quantity,
                    )

                    # Update capital
                    self.capital -= quantity * close

            elif signal.signal_type in [SignalType.SELL, SignalType.CUTLOSS] and current_position:
                # Close position
                current_position.exit_time = timestamp
                current_position.exit_price = close
                current_position.pnl = (close - current_position.entry_price) * current_position.quantity
                current_position.pnl_percent = (close - current_position.entry_price) / current_position.entry_price
                current_position.holding_period = timestamp - current_position.entry_time

                # Update capital
                self.capital += current_position.quantity * close

                self.trades.append(current_position)
                current_position = None

            # Record equity
            equity = self.capital
            if current_position:
                equity += current_position.quantity * close

            self.equity_curve.append({
                'timestamp': timestamp,
                'equity': equity,
            })

        # Calculate metrics
        results = self.calculate_metrics()
        return results

    def calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if not self.trades:
            return {"error": "No trades executed"}

        # Basic metrics
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl < 0]

        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0

        total_pnl = sum(t.pnl for t in self.trades)
        total_return = (self.capital - self.initial_capital) / self.initial_capital

        avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0

        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0

        # Max drawdown
        equity_series = pd.DataFrame(self.equity_curve)['equity']
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax
        max_drawdown = drawdown.min()

        # Sharpe ratio (simplified)
        returns = equity_series.pct_change().dropna()
        sharpe_ratio = (returns.mean() / returns.std()) * (252 ** 0.5) if returns.std() > 0 else 0

        return {
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "total_return": total_return,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "final_capital": self.capital,
        }
