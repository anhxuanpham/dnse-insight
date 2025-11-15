"""
Market Scanner Engine
Real-time scanning of Vietnamese stock market for trading opportunities
"""
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from loguru import logger

from core.price_stream import price_stream_manager, PriceData
from core.signal_engine import signal_engine


class ScanResultPriority(Enum):
    """Scan result priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ScanResult:
    """Scan result model"""
    symbol: str
    filter_name: str
    priority: ScanResultPriority
    message: str
    price: float
    change_percent: float
    volume: int
    timestamp: datetime
    metadata: Dict = None

    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "filter_name": self.filter_name,
            "priority": self.priority.name,
            "message": self.message,
            "price": self.price,
            "change_percent": self.change_percent,
            "volume": self.volume,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {},
        }


class BaseFilter:
    """Base class for all market filters"""

    def __init__(self, name: str, priority: ScanResultPriority = ScanResultPriority.MEDIUM):
        self.name = name
        self.priority = priority

    def scan(self, symbol: str, price_data: PriceData) -> Optional[ScanResult]:
        """
        Scan a symbol and return result if conditions met
        Must be implemented by subclasses
        """
        raise NotImplementedError


class ScannerEngine:
    """
    Market Scanner Engine
    Continuously scans market for trading opportunities using various filters
    """

    def __init__(self):
        self.filters: List[BaseFilter] = []
        self.scan_results: List[ScanResult] = []
        self.symbols_to_scan: List[str] = []
        self.callbacks: List[Callable[[ScanResult], None]] = []

        # Statistics
        self.total_scans = 0
        self.total_hits = 0

    def add_filter(self, filter_instance: BaseFilter):
        """Add a filter to the scanner"""
        self.filters.append(filter_instance)
        logger.info(f"Added filter: {filter_instance.name}")

    def remove_filter(self, filter_name: str):
        """Remove a filter by name"""
        self.filters = [f for f in self.filters if f.name != filter_name]
        logger.info(f"Removed filter: {filter_name}")

    def set_symbols(self, symbols: List[str]):
        """Set symbols to scan"""
        self.symbols_to_scan = [s.upper() for s in symbols]
        logger.info(f"Scanner watching {len(self.symbols_to_scan)} symbols")

    def add_callback(self, callback: Callable[[ScanResult], None]):
        """Add callback for scan results"""
        self.callbacks.append(callback)

    def scan_symbol(self, symbol: str) -> List[ScanResult]:
        """Scan a single symbol with all filters"""
        price_data = price_stream_manager.get_latest_price(symbol)
        if not price_data:
            return []

        results = []
        self.total_scans += 1

        for filter_instance in self.filters:
            try:
                result = filter_instance.scan(symbol, price_data)
                if result:
                    results.append(result)
                    self.total_hits += 1
                    self.scan_results.append(result)

                    # Call callbacks
                    for callback in self.callbacks:
                        try:
                            callback(result)
                        except Exception as e:
                            logger.error(f"Error in scan callback: {e}")

            except Exception as e:
                logger.error(f"Error in filter {filter_instance.name} for {symbol}: {e}")

        return results

    def scan_all(self) -> List[ScanResult]:
        """Scan all watched symbols"""
        all_results = []
        for symbol in self.symbols_to_scan:
            results = self.scan_symbol(symbol)
            all_results.extend(results)

        return all_results

    def get_recent_results(self, minutes: int = 60, priority: Optional[ScanResultPriority] = None) -> List[ScanResult]:
        """Get recent scan results"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        results = [r for r in self.scan_results if r.timestamp >= cutoff_time]

        if priority:
            results = [r for r in results if r.priority == priority]

        return sorted(results, key=lambda x: x.timestamp, reverse=True)

    def get_statistics(self) -> Dict:
        """Get scanner statistics"""
        return {
            "total_scans": self.total_scans,
            "total_hits": self.total_hits,
            "hit_rate": self.total_hits / self.total_scans if self.total_scans > 0 else 0,
            "filters_count": len(self.filters),
            "symbols_count": len(self.symbols_to_scan),
            "recent_results_count": len(self.get_recent_results(60)),
        }

    def clear_results(self):
        """Clear old scan results"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.scan_results = [r for r in self.scan_results if r.timestamp >= cutoff_time]


# Global instance
scanner_engine = ScannerEngine()
