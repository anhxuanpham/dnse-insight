"""
Pairs Trading Strategy
Trades two correlated stocks when spread diverges from mean
"""
from typing import Optional, Tuple
import numpy as np
from scipy import stats
from loguru import logger


class PairsTradingStrategy:
    """
    Pairs Trading (Statistical Arbitrage)

    Trades two highly correlated stocks:
    - Calculate spread = stock1 - hedge_ratio * stock2
    - Z-score of spread
    - Long spread when Z < -2 (buy stock1, sell stock2)
    - Short spread when Z > 2 (sell stock1, buy stock2)
    - Exit when spread returns to mean
    """

    def __init__(self, lookback: int = 60, entry_z: float = 2.0, exit_z: float = 0.5):
        self.lookback = lookback
        self.entry_z = entry_z
        self.exit_z = exit_z

    def calculate_hedge_ratio(self, prices1: np.ndarray, prices2: np.ndarray) -> float:
        """Calculate optimal hedge ratio using OLS regression"""
        slope, intercept, r_value, p_value, std_err = stats.linregress(prices2, prices1)
        return slope

    def calculate_spread(self, prices1: np.ndarray, prices2: np.ndarray, hedge_ratio: float) -> np.ndarray:
        """Calculate spread between two stocks"""
        return prices1 - hedge_ratio * prices2

    def generate_signal(
        self,
        symbol1: str,
        symbol2: str,
        prices1: np.ndarray,
        prices2: np.ndarray
    ) -> Optional[dict]:
        """
        Generate pairs trading signal

        Returns:
            dict with 'action', 'symbol1_action', 'symbol2_action', 'spread_zscore'
        """
        if len(prices1) < self.lookback or len(prices2) < self.lookback:
            return None

        # Use last N prices
        p1 = prices1[-self.lookback:]
        p2 = prices2[-self.lookback:]

        # Calculate hedge ratio
        hedge_ratio = self.calculate_hedge_ratio(p1, p2)

        # Calculate spread
        spread = self.calculate_spread(p1, p2, hedge_ratio)

        # Calculate Z-score of spread
        spread_mean = spread.mean()
        spread_std = spread.std()
        current_spread = spread[-1]
        z_score = (current_spread - spread_mean) / spread_std if spread_std > 0 else 0

        logger.info(
            f"Pairs {symbol1}/{symbol2}: Spread={current_spread:.2f}, "
            f"Z-score={z_score:.2f}, Hedge={hedge_ratio:.4f}"
        )

        # Generate signals
        if z_score < -self.entry_z:
            # Spread too low - Long spread
            return {
                "action": "LONG_SPREAD",
                "symbol1_action": "BUY",  # Buy stock1
                "symbol2_action": "SELL",  # Sell stock2
                "hedge_ratio": hedge_ratio,
                "spread_zscore": z_score,
                "reason": f"Spread Z-score {z_score:.2f} < -{self.entry_z}",
            }

        elif z_score > self.entry_z:
            # Spread too high - Short spread
            return {
                "action": "SHORT_SPREAD",
                "symbol1_action": "SELL",  # Sell stock1
                "symbol2_action": "BUY",   # Buy stock2
                "hedge_ratio": hedge_ratio,
                "spread_zscore": z_score,
                "reason": f"Spread Z-score {z_score:.2f} > {self.entry_z}",
            }

        elif abs(z_score) < self.exit_z:
            # Spread returned to mean - Exit
            return {
                "action": "EXIT",
                "symbol1_action": "CLOSE",
                "symbol2_action": "CLOSE",
                "hedge_ratio": hedge_ratio,
                "spread_zscore": z_score,
                "reason": f"Spread returned to mean (Z={z_score:.2f})",
            }

        return None


# Example pairs for Vietnamese market
VIETNAM_PAIRS = [
    ("VCB", "TCB"),   # Banking sector
    ("VHM", "VIC"),   # Vingroup stocks
    ("HPG", "HSG"),   # Steel sector
    ("MSN", "MWG"),   # Retail
    ("GAS", "PLX"),   # Energy
]
