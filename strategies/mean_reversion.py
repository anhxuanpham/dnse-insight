"""
Mean Reversion Trading Strategy
Buys when price significantly below moving average, sells when above
"""
from typing import Optional
from core.signal_engine import SignalType, TradingSignal, SignalStrength
from core.price_stream import PriceData
import numpy as np


class MeanReversionStrategy:
    """
    Mean Reversion Strategy

    Logic:
    - Calculate Bollinger Bands or Z-score
    - Buy when price < lower band (oversold)
    - Sell when price > upper band (overbought)
    - Exit when price returns to mean
    """

    def __init__(self, period: int = 20, std_dev: float = 2.0, z_score_threshold: float = 2.0):
        self.period = period
        self.std_dev = std_dev
        self.z_score_threshold = z_score_threshold

    def generate_signal(self, symbol: str, price_history: list, current_price: float) -> Optional[TradingSignal]:
        """Generate mean reversion signal"""
        if len(price_history) < self.period:
            return None

        prices = np.array(price_history[-self.period:])
        mean = prices.mean()
        std = prices.std()

        # Calculate Z-score
        z_score = (current_price - mean) / std if std > 0 else 0

        # Bollinger Bands
        upper_band = mean + (std * self.std_dev)
        lower_band = mean - (std * self.std_dev)

        # Generate signals
        if current_price < lower_band and z_score < -self.z_score_threshold:
            return TradingSignal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                strength=SignalStrength.STRONG if z_score < -2.5 else SignalStrength.MODERATE,
                price=current_price,
                reason=f"Mean Reversion: Price {current_price:.2f} below lower band {lower_band:.2f} (Z-score: {z_score:.2f})",
                indicators={
                    "mean": mean,
                    "upper_band": upper_band,
                    "lower_band": lower_band,
                    "z_score": z_score,
                }
            )

        elif current_price > upper_band and z_score > self.z_score_threshold:
            return TradingSignal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                strength=SignalStrength.STRONG if z_score > 2.5 else SignalStrength.MODERATE,
                price=current_price,
                reason=f"Mean Reversion: Price {current_price:.2f} above upper band {upper_band:.2f} (Z-score: {z_score:.2f})",
                indicators={
                    "mean": mean,
                    "upper_band": upper_band,
                    "lower_band": lower_band,
                    "z_score": z_score,
                }
            )

        # Exit signal when price returns to mean
        elif abs(z_score) < 0.5 and abs(current_price - mean) < std * 0.5:
            return TradingSignal(
                symbol=symbol,
                signal_type=SignalType.HOLD,
                strength=SignalStrength.WEAK,
                price=current_price,
                reason=f"Price returned to mean {mean:.2f}",
                indicators={"mean": mean, "z_score": z_score}
            )

        return None
