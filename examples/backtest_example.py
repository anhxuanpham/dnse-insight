#!/usr/bin/env python3
"""
Example: Backtesting a Trading Strategy
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger

from backtest.engine.backtest_engine import BacktestEngine
from core.signal_engine import SignalEngine, SignalType


def generate_sample_data(days: int = 365) -> pd.DataFrame:
    """Generate sample price data for backtesting"""
    dates = pd.date_range(end=datetime.now(), periods=days)

    # Generate synthetic price data
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(days) * 2)
    volumes = np.random.randint(1000000, 5000000, days)

    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices * (1 + np.random.randn(days) * 0.01),
        'high': prices * (1 + np.abs(np.random.randn(days)) * 0.02),
        'low': prices * (1 - np.abs(np.random.randn(days)) * 0.02),
        'close': prices,
        'volume': volumes,
    })

    return df


def simple_strategy(signal_engine: SignalEngine, symbol: str, price: float):
    """Simple moving average crossover strategy"""
    return signal_engine.generate_signal(symbol, price)


def main():
    """Run backtest example"""
    logger.info("Backtesting Example")

    # Generate sample data
    logger.info("Generating sample data...")
    data = generate_sample_data(days=500)

    # Create backtest engine
    engine = BacktestEngine(initial_capital=100_000_000)  # 100M VND

    # Run backtest
    logger.info("Running backtest...")
    results = engine.run_backtest(
        data=data,
        strategy_func=simple_strategy,
        symbol="VCB",
    )

    # Display results
    logger.info("\n" + "=" * 60)
    logger.info("BACKTEST RESULTS")
    logger.info("=" * 60)

    logger.info(f"Total Trades: {results['total_trades']}")
    logger.info(f"Winning Trades: {results['winning_trades']}")
    logger.info(f"Losing Trades: {results['losing_trades']}")
    logger.info(f"Win Rate: {results['win_rate']*100:.2f}%")
    logger.info(f"Total P&L: {results['total_pnl']:,.0f} VND")
    logger.info(f"Total Return: {results['total_return']*100:.2f}%")
    logger.info(f"Avg Win: {results['avg_win']:,.0f} VND")
    logger.info(f"Avg Loss: {results['avg_loss']:,.0f} VND")
    logger.info(f"Profit Factor: {results['profit_factor']:.2f}")
    logger.info(f"Max Drawdown: {results['max_drawdown']*100:.2f}%")
    logger.info(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    logger.info(f"Final Capital: {results['final_capital']:,.0f} VND")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
