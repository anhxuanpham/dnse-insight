"""
Volume Surge Filter
Detects abnormal volume spikes
"""
from typing import Optional
from datetime import datetime
from screener.core.scanner_engine import BaseFilter, ScanResult, ScanResultPriority
from core.price_stream import PriceData
from core.signal_engine import signal_engine


class VolumeSurgeFilter(BaseFilter):
    """Detect volume surges"""

    def __init__(self, threshold: float = 2.0, min_price_change: float = 0.01):
        super().__init__("Volume Surge", ScanResultPriority.HIGH)
        self.threshold = threshold  # 2x normal volume
        self.min_price_change = min_price_change  # 1% minimum price change

    def scan(self, symbol: str, price_data: PriceData) -> Optional[ScanResult]:
        """Scan for volume surge"""
        # Check if volume surge detected
        is_surge = signal_engine.detect_volume_surge(symbol, self.threshold)

        if not is_surge:
            return None

        # Check price change
        if abs(price_data.change_percent / 100) < self.min_price_change:
            return None

        # Calculate volume multiplier
        history = signal_engine.price_histories.get(symbol)
        if not history or len(history) < 20:
            return None

        df = history.get_dataframe()
        avg_volume = df["volume"].iloc[:-1].mean()
        current_volume = df["volume"].iloc[-1]
        multiplier = current_volume / avg_volume if avg_volume > 0 else 0

        message = (
            f"Volume surge detected: {multiplier:.1f}x average "
            f"with {price_data.change_percent:+.2f}% price change"
        )

        return ScanResult(
            symbol=symbol,
            filter_name=self.name,
            priority=self.priority,
            message=message,
            price=price_data.price,
            change_percent=price_data.change_percent,
            volume=price_data.volume,
            timestamp=datetime.now(),
            metadata={
                "volume_multiplier": multiplier,
                "avg_volume": avg_volume,
            },
        )
