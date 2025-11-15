"""
Price Momentum Filter
Detects strong price momentum
"""
from typing import Optional
from datetime import datetime
from screener.core.scanner_engine import BaseFilter, ScanResult, ScanResultPriority
from core.price_stream import PriceData


class PriceMomentumFilter(BaseFilter):
    """Detect strong price momentum"""

    def __init__(self, threshold: float = 0.03):
        super().__init__("Price Momentum", ScanResultPriority.HIGH)
        self.threshold = threshold  # 3% price change

    def scan(self, symbol: str, price_data: PriceData) -> Optional[ScanResult]:
        """Scan for price momentum"""
        change_pct = price_data.change_percent / 100

        if abs(change_pct) < self.threshold:
            return None

        if change_pct > 0:
            message = f"Strong upward momentum: +{change_pct*100:.2f}%"
            priority = ScanResultPriority.HIGH if change_pct > 0.05 else ScanResultPriority.MEDIUM
        else:
            message = f"Strong downward momentum: {change_pct*100:.2f}%"
            priority = ScanResultPriority.HIGH if change_pct < -0.05 else ScanResultPriority.MEDIUM

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
                "momentum": change_pct,
                "direction": "up" if change_pct > 0 else "down",
            },
        )


class NewHighLowFilter(BaseFilter):
    """Detect 52-week highs/lows"""

    def __init__(self, period: int = 252):  # ~252 trading days in a year
        super().__init__("52-Week High/Low", ScanResultPriority.HIGH)
        self.period = period

    def scan(self, symbol: str, price_data: PriceData) -> Optional[ScanResult]:
        """Scan for new highs/lows"""
        from core.signal_engine import signal_engine

        history = signal_engine.price_histories.get(symbol)
        if not history or len(history) < min(50, self.period):
            return None

        df = history.get_dataframe()
        current_price = price_data.price

        # Get high/low over period
        period_high = df["high"].max()
        period_low = df["low"].min()

        # Check for new high
        if current_price >= period_high * 0.99:  # Within 1% of high
            message = f"Near {self.period}-day high! Price: {current_price:.2f}, High: {period_high:.2f}"
            return ScanResult(
                symbol=symbol,
                filter_name=self.name,
                priority=ScanResultPriority.HIGH,
                message=message,
                price=current_price,
                change_percent=price_data.change_percent,
                volume=price_data.volume,
                timestamp=datetime.now(),
                metadata={
                    "type": "new_high",
                    "period_high": period_high,
                    "period_low": period_low,
                },
            )

        # Check for new low
        elif current_price <= period_low * 1.01:  # Within 1% of low
            message = f"Near {self.period}-day low! Price: {current_price:.2f}, Low: {period_low:.2f}"
            return ScanResult(
                symbol=symbol,
                filter_name=self.name,
                priority=ScanResultPriority.HIGH,
                message=message,
                price=current_price,
                change_percent=price_data.change_percent,
                volume=price_data.volume,
                timestamp=datetime.now(),
                metadata={
                    "type": "new_low",
                    "period_high": period_high,
                    "period_low": period_low,
                },
            )

        return None
