"""
Technical Indicator Filters
Filters based on RSI, MACD, etc.
"""
from typing import Optional
from datetime import datetime
from screener.core.scanner_engine import BaseFilter, ScanResult, ScanResultPriority
from core.price_stream import PriceData
from core.signal_engine import signal_engine


class RSIExtremeFilter(BaseFilter):
    """Detect extreme RSI conditions"""

    def __init__(self, oversold: float = 30, overbought: float = 70):
        super().__init__("RSI Extreme", ScanResultPriority.MEDIUM)
        self.oversold = oversold
        self.overbought = overbought

    def scan(self, symbol: str, price_data: PriceData) -> Optional[ScanResult]:
        """Scan for extreme RSI"""
        rsi = signal_engine.calculate_rsi(symbol, 14)

        if rsi is None:
            return None

        if rsi < self.oversold:
            message = f"RSI oversold: {rsi:.1f} < {self.oversold}"
            priority = ScanResultPriority.HIGH if rsi < 20 else ScanResultPriority.MEDIUM

            return ScanResult(
                symbol=symbol,
                filter_name=self.name,
                priority=priority,
                message=message,
                price=price_data.price,
                change_percent=price_data.change_percent,
                volume=price_data.volume,
                timestamp=datetime.now(),
                metadata={
                    "rsi": rsi,
                    "condition": "oversold",
                },
            )

        elif rsi > self.overbought:
            message = f"RSI overbought: {rsi:.1f} > {self.overbought}"
            priority = ScanResultPriority.HIGH if rsi > 80 else ScanResultPriority.MEDIUM

            return ScanResult(
                symbol=symbol,
                filter_name=self.name,
                priority=priority,
                message=message,
                price=price_data.price,
                change_percent=price_data.change_percent,
                volume=price_data.volume,
                timestamp=datetime.now(),
                metadata={
                    "rsi": rsi,
                    "condition": "overbought",
                },
            )

        return None


class MovingAverageCrossFilter(BaseFilter):
    """Detect moving average crossovers"""

    def __init__(self):
        super().__init__("MA Crossover", ScanResultPriority.HIGH)

    def scan(self, symbol: str, price_data: PriceData) -> Optional[ScanResult]:
        """Scan for MA crossovers"""
        sma_20 = signal_engine.calculate_sma(symbol, 20)
        sma_50 = signal_engine.calculate_sma(symbol, 50)

        if sma_20 is None or sma_50 is None:
            return None

        # Get previous SMA20
        history = signal_engine.price_histories.get(symbol)
        if not history or len(history) < 21:
            return None

        df = history.get_dataframe()
        prev_sma_20 = df["close"].iloc[-21:-1].mean()

        # Golden Cross
        if prev_sma_20 <= sma_50 and sma_20 > sma_50:
            message = f"Golden Cross! SMA20 ({sma_20:.2f}) crossed above SMA50 ({sma_50:.2f})"
            return ScanResult(
                symbol=symbol,
                filter_name=self.name,
                priority=ScanResultPriority.HIGH,
                message=message,
                price=price_data.price,
                change_percent=price_data.change_percent,
                volume=price_data.volume,
                timestamp=datetime.now(),
                metadata={
                    "type": "golden_cross",
                    "sma_20": sma_20,
                    "sma_50": sma_50,
                },
            )

        # Death Cross
        elif prev_sma_20 >= sma_50 and sma_20 < sma_50:
            message = f"Death Cross! SMA20 ({sma_20:.2f}) crossed below SMA50 ({sma_50:.2f})"
            return ScanResult(
                symbol=symbol,
                filter_name=self.name,
                priority=ScanResultPriority.HIGH,
                message=message,
                price=price_data.price,
                change_percent=price_data.change_percent,
                volume=price_data.volume,
                timestamp=datetime.now(),
                metadata={
                    "type": "death_cross",
                    "sma_20": sma_20,
                    "sma_50": sma_50,
                },
            )

        return None
