"""
Signal Engine Module
Analyzes price data and generates trading signals based on technical indicators
"""
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
from collections import deque
import pandas as pd
import numpy as np
from loguru import logger
from utils.config import settings


class SignalType(Enum):
    """Trading signal types"""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CUTLOSS = "CUTLOSS"


class SignalStrength(Enum):
    """Signal strength levels"""

    WEAK = 1
    MODERATE = 2
    STRONG = 3


class TradingSignal:
    """Trading signal model"""

    def __init__(
        self,
        symbol: str,
        signal_type: SignalType,
        strength: SignalStrength,
        price: float,
        reason: str,
        indicators: Dict = None,
    ):
        self.symbol = symbol
        self.signal_type = signal_type
        self.strength = strength
        self.price = price
        self.reason = reason
        self.indicators = indicators or {}
        self.timestamp = datetime.now()

    def __repr__(self):
        return f"Signal({self.symbol}, {self.signal_type.value}, {self.strength.value}, {self.price}, {self.reason})"

    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "signal_type": self.signal_type.value,
            "strength": self.strength.value,
            "price": self.price,
            "reason": self.reason,
            "indicators": self.indicators,
            "timestamp": self.timestamp.isoformat(),
        }


class PriceHistory:
    """Maintains price history for a symbol"""

    def __init__(self, symbol: str, max_size: int = 500):
        self.symbol = symbol
        self.max_size = max_size
        self.prices = deque(maxlen=max_size)
        self.volumes = deque(maxlen=max_size)
        self.timestamps = deque(maxlen=max_size)
        self.highs = deque(maxlen=max_size)
        self.lows = deque(maxlen=max_size)

    def add(self, price: float, volume: int, high: float, low: float, timestamp: datetime = None):
        """Add a new price point"""
        self.prices.append(price)
        self.volumes.append(volume)
        self.highs.append(high)
        self.lows.append(low)
        self.timestamps.append(timestamp or datetime.now())

    def get_dataframe(self, periods: int = None) -> pd.DataFrame:
        """Get price history as pandas DataFrame"""
        if not self.prices:
            return pd.DataFrame()

        data = {
            "timestamp": list(self.timestamps),
            "close": list(self.prices),
            "volume": list(self.volumes),
            "high": list(self.highs),
            "low": list(self.lows),
        }

        df = pd.DataFrame(data)
        if periods:
            df = df.tail(periods)

        return df

    def __len__(self):
        return len(self.prices)


class SignalEngine:
    """
    Generates trading signals based on technical analysis
    Supports multiple strategies:
    - Breakout strategy (resistance/support levels)
    - Moving average crossover
    - RSI overbought/oversold
    - Volume surge detection
    - Volatility-based cutloss
    """

    def __init__(self):
        self.price_histories: Dict[str, PriceHistory] = {}
        self.support_resistance_cache: Dict[str, Tuple[float, float]] = {}

    def update_price(self, symbol: str, price: float, volume: int, high: float, low: float):
        """Update price history for a symbol"""
        if symbol not in self.price_histories:
            self.price_histories[symbol] = PriceHistory(symbol)

        self.price_histories[symbol].add(price, volume, high, low)

    def calculate_sma(self, symbol: str, period: int) -> Optional[float]:
        """Calculate Simple Moving Average"""
        if symbol not in self.price_histories:
            return None

        df = self.price_histories[symbol].get_dataframe()
        if len(df) < period:
            return None

        return df["close"].tail(period).mean()

    def calculate_ema(self, symbol: str, period: int) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        if symbol not in self.price_histories:
            return None

        df = self.price_histories[symbol].get_dataframe()
        if len(df) < period:
            return None

        return df["close"].ewm(span=period, adjust=False).mean().iloc[-1]

    def calculate_rsi(self, symbol: str, period: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index"""
        if symbol not in self.price_histories:
            return None

        df = self.price_histories[symbol].get_dataframe()
        if len(df) < period + 1:
            return None

        # Calculate price changes
        delta = df["close"].diff()

        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)

        # Calculate average gains and losses
        avg_gains = gains.rolling(window=period).mean()
        avg_losses = losses.rolling(window=period).mean()

        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1]

    def calculate_bollinger_bands(
        self, symbol: str, period: int = 20, std_dev: float = 2.0
    ) -> Optional[Tuple[float, float, float]]:
        """Calculate Bollinger Bands (upper, middle, lower)"""
        if symbol not in self.price_histories:
            return None

        df = self.price_histories[symbol].get_dataframe()
        if len(df) < period:
            return None

        sma = df["close"].rolling(window=period).mean().iloc[-1]
        std = df["close"].rolling(window=period).std().iloc[-1]

        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)

        return upper, sma, lower

    def detect_support_resistance(self, symbol: str, lookback: int = 50) -> Tuple[float, float]:
        """
        Detect support and resistance levels using local min/max
        Returns (support, resistance)
        """
        if symbol not in self.price_histories:
            return 0.0, 0.0

        df = self.price_histories[symbol].get_dataframe(lookback)
        if len(df) < 10:
            return 0.0, 0.0

        # Use recent high/low as resistance/support
        resistance = df["high"].max()
        support = df["low"].min()

        # Cache the levels
        self.support_resistance_cache[symbol] = (support, resistance)

        return support, resistance

    def detect_volume_surge(self, symbol: str, threshold: float = 2.0) -> bool:
        """
        Detect if current volume is significantly higher than average
        """
        if symbol not in self.price_histories:
            return False

        df = self.price_histories[symbol].get_dataframe()
        if len(df) < 20:
            return False

        avg_volume = df["volume"].iloc[:-1].mean()
        current_volume = df["volume"].iloc[-1]

        return current_volume > (avg_volume * threshold)

    def calculate_volatility(self, symbol: str, period: int = 20) -> Optional[float]:
        """Calculate price volatility (standard deviation of returns)"""
        if symbol not in self.price_histories:
            return None

        df = self.price_histories[symbol].get_dataframe()
        if len(df) < period:
            return None

        returns = df["close"].pct_change()
        volatility = returns.rolling(window=period).std().iloc[-1]

        return volatility

    def generate_signal(self, symbol: str, current_price: float) -> Optional[TradingSignal]:
        """
        Generate trading signal based on multiple indicators
        """
        if symbol not in self.price_histories:
            return None

        history = self.price_histories[symbol]
        if len(history) < 30:  # Need minimum history
            return None

        indicators = {}
        signals = []
        reasons = []

        # Calculate indicators
        sma_20 = self.calculate_sma(symbol, 20)
        sma_50 = self.calculate_sma(symbol, 50)
        ema_12 = self.calculate_ema(symbol, 12)
        ema_26 = self.calculate_ema(symbol, 26)
        rsi = self.calculate_rsi(symbol, 14)
        volatility = self.calculate_volatility(symbol, 20)
        volume_surge = self.detect_volume_surge(symbol, 2.0)
        support, resistance = self.detect_support_resistance(symbol, 50)

        indicators = {
            "sma_20": sma_20,
            "sma_50": sma_50,
            "ema_12": ema_12,
            "ema_26": ema_26,
            "rsi": rsi,
            "volatility": volatility,
            "support": support,
            "resistance": resistance,
            "volume_surge": volume_surge,
        }

        # Strategy 1: Breakout Strategy
        if settings.enable_breakout_strategy and resistance > 0:
            if current_price >= resistance * 0.998:  # Price breaking resistance
                signals.append(SignalType.BUY)
                reasons.append(f"Breakout above resistance {resistance:.2f}")

        # Strategy 2: Support/Resistance Strategy
        if settings.enable_support_resistance_strategy and support > 0:
            if current_price <= support * 1.002:  # Price at support
                signals.append(SignalType.BUY)
                reasons.append(f"Price at support {support:.2f}")
            elif current_price <= support * 0.98:  # Price breaking support
                signals.append(SignalType.SELL)
                reasons.append(f"Price breaking support {support:.2f}")

        # Strategy 3: Moving Average Crossover
        if sma_20 and sma_50:
            df = self.price_histories[symbol].get_dataframe()
            if len(df) >= 2:
                prev_sma_20 = df["close"].iloc[-21:-1].mean()
                if prev_sma_20 <= sma_50 and sma_20 > sma_50:
                    signals.append(SignalType.BUY)
                    reasons.append("Golden Cross (SMA20 > SMA50)")
                elif prev_sma_20 >= sma_50 and sma_20 < sma_50:
                    signals.append(SignalType.SELL)
                    reasons.append("Death Cross (SMA20 < SMA50)")

        # Strategy 4: RSI Strategy
        if rsi:
            if rsi < 30:
                signals.append(SignalType.BUY)
                reasons.append(f"RSI oversold ({rsi:.1f})")
            elif rsi > 70:
                signals.append(SignalType.SELL)
                reasons.append(f"RSI overbought ({rsi:.1f})")

        # Strategy 5: Volume Surge with Price Increase
        if volume_surge:
            df = self.price_histories[symbol].get_dataframe()
            price_change = (df["close"].iloc[-1] - df["close"].iloc[-2]) / df["close"].iloc[-2]
            if price_change > 0.02:  # 2% increase
                signals.append(SignalType.BUY)
                reasons.append(f"Volume surge with {price_change*100:.1f}% price increase")

        # Strategy 6: Volatility-based Cutloss
        if settings.enable_volatility_cutloss and volatility:
            if volatility > settings.volatility_threshold:
                signals.append(SignalType.CUTLOSS)
                reasons.append(f"High volatility ({volatility*100:.2f}%)")

        # Determine final signal
        if not signals:
            return TradingSignal(
                symbol=symbol,
                signal_type=SignalType.HOLD,
                strength=SignalStrength.WEAK,
                price=current_price,
                reason="No strong signals detected",
                indicators=indicators,
            )

        # Count signal types
        buy_count = signals.count(SignalType.BUY)
        sell_count = signals.count(SignalType.SELL)
        cutloss_count = signals.count(SignalType.CUTLOSS)

        # Cutloss takes priority
        if cutloss_count > 0:
            return TradingSignal(
                symbol=symbol,
                signal_type=SignalType.CUTLOSS,
                strength=SignalStrength.STRONG,
                price=current_price,
                reason=" | ".join([r for r in reasons if "volatility" in r.lower()]),
                indicators=indicators,
            )

        # Determine signal based on majority
        if buy_count > sell_count:
            strength = (
                SignalStrength.STRONG
                if buy_count >= 3
                else SignalStrength.MODERATE
                if buy_count >= 2
                else SignalStrength.WEAK
            )
            return TradingSignal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                strength=strength,
                price=current_price,
                reason=" | ".join([r for r in reasons if any(x in r for x in ["Breakout", "support", "Cross", "oversold", "surge"])]),
                indicators=indicators,
            )
        elif sell_count > buy_count:
            strength = (
                SignalStrength.STRONG
                if sell_count >= 3
                else SignalStrength.MODERATE
                if sell_count >= 2
                else SignalStrength.WEAK
            )
            return TradingSignal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                strength=strength,
                price=current_price,
                reason=" | ".join([r for r in reasons if any(x in r for x in ["breaking", "Cross", "overbought"])]),
                indicators=indicators,
            )
        else:
            return TradingSignal(
                symbol=symbol,
                signal_type=SignalType.HOLD,
                strength=SignalStrength.WEAK,
                price=current_price,
                reason="Mixed signals",
                indicators=indicators,
            )


# Global instance
signal_engine = SignalEngine()
