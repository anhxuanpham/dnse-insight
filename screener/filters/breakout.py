"""
Breakout Detection Filter
Detects when price breaks resistance or support levels
"""
from typing import Optional
from datetime import datetime
from screener.core.scanner_engine import BaseFilter, ScanResult, ScanResultPriority
from core.price_stream import PriceData
from core.signal_engine import signal_engine


class BreakoutFilter(BaseFilter):
    """Detect breakouts above resistance or below support"""

    def __init__(self, sensitivity: float = 0.002):
        super().__init__("Breakout Detection", ScanResultPriority.CRITICAL)
        self.sensitivity = sensitivity  # 0.2% threshold

    def scan(self, symbol: str, price_data: PriceData) -> Optional[ScanResult]:
        """Scan for breakouts"""
        # Get support and resistance
        support, resistance = signal_engine.detect_support_resistance(symbol, 50)

        if support == 0 or resistance == 0:
            return None

        current_price = price_data.price

        # Check for resistance breakout
        if current_price >= resistance * (1 - self.sensitivity):
            if current_price > resistance:
                message = f"BREAKOUT above resistance! Price {current_price:.2f} > Resistance {resistance:.2f}"
                priority = ScanResultPriority.CRITICAL
            else:
                message = f"Approaching resistance: {current_price:.2f} near {resistance:.2f}"
                priority = ScanResultPriority.HIGH

            return ScanResult(
                symbol=symbol,
                filter_name=self.name,
                priority=priority,
                message=message,
                price=current_price,
                change_percent=price_data.change_percent,
                volume=price_data.volume,
                timestamp=datetime.now(),
                metadata={
                    "resistance": resistance,
                    "support": support,
                    "type": "resistance_breakout",
                },
            )

        # Check for support breakdown
        elif current_price <= support * (1 + self.sensitivity):
            if current_price < support:
                message = f"BREAKDOWN below support! Price {current_price:.2f} < Support {support:.2f}"
                priority = ScanResultPriority.CRITICAL
            else:
                message = f"Approaching support: {current_price:.2f} near {support:.2f}"
                priority = ScanResultPriority.HIGH

            return ScanResult(
                symbol=symbol,
                filter_name=self.name,
                priority=priority,
                message=message,
                price=current_price,
                change_percent=price_data.change_percent,
                volume=price_data.volume,
                timestamp=datetime.now(),
                metadata={
                    "resistance": resistance,
                    "support": support,
                    "type": "support_breakdown",
                },
            )

        return None
