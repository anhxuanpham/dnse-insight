"""
Unit tests for Signal Engine
"""
import pytest
from datetime import datetime
from core.signal_engine import (
    SignalEngine,
    SignalType,
    SignalStrength,
    PriceHistory,
)


class TestPriceHistory:
    """Test PriceHistory class"""

    def test_add_price(self):
        """Test adding price data"""
        history = PriceHistory("VCB", max_size=100)

        history.add(
            price=100.0, volume=1000, high=101.0, low=99.0, timestamp=datetime.now()
        )

        assert len(history) == 1
        assert history.prices[0] == 100.0
        assert history.volumes[0] == 1000

    def test_max_size(self):
        """Test max size limit"""
        history = PriceHistory("VCB", max_size=3)

        for i in range(5):
            history.add(
                price=100.0 + i,
                volume=1000,
                high=101.0,
                low=99.0,
                timestamp=datetime.now(),
            )

        assert len(history) == 3
        assert history.prices[0] == 102.0  # Oldest entry after rotation

    def test_get_dataframe(self):
        """Test getting DataFrame"""
        history = PriceHistory("VCB", max_size=100)

        for i in range(10):
            history.add(
                price=100.0 + i,
                volume=1000,
                high=101.0,
                low=99.0,
                timestamp=datetime.now(),
            )

        df = history.get_dataframe()
        assert len(df) == 10
        assert "close" in df.columns
        assert "volume" in df.columns


class TestSignalEngine:
    """Test SignalEngine class"""

    @pytest.fixture
    def engine(self):
        """Create signal engine instance"""
        return SignalEngine()

    @pytest.fixture
    def engine_with_history(self):
        """Create signal engine with price history"""
        engine = SignalEngine()

        # Add 100 price points
        for i in range(100):
            price = 100.0 + (i % 10) - 5  # Oscillating price
            volume = 1000 + i * 10
            engine.update_price("VCB", price, volume, price + 1, price - 1)

        return engine

    def test_update_price(self, engine):
        """Test updating price"""
        engine.update_price("VCB", 100.0, 1000, 101.0, 99.0)

        assert "VCB" in engine.price_histories
        assert len(engine.price_histories["VCB"]) == 1

    def test_calculate_sma(self, engine_with_history):
        """Test SMA calculation"""
        sma_20 = engine_with_history.calculate_sma("VCB", 20)

        assert sma_20 is not None
        assert isinstance(sma_20, float)
        assert sma_20 > 0

    def test_calculate_ema(self, engine_with_history):
        """Test EMA calculation"""
        ema_12 = engine_with_history.calculate_ema("VCB", 12)

        assert ema_12 is not None
        assert isinstance(ema_12, float)

    def test_calculate_rsi(self, engine_with_history):
        """Test RSI calculation"""
        rsi = engine_with_history.calculate_rsi("VCB", 14)

        assert rsi is not None
        assert 0 <= rsi <= 100

    def test_detect_support_resistance(self, engine_with_history):
        """Test support/resistance detection"""
        support, resistance = engine_with_history.detect_support_resistance("VCB", 50)

        assert support > 0
        assert resistance > 0
        assert resistance >= support

    def test_detect_volume_surge(self, engine_with_history):
        """Test volume surge detection"""
        # Add a volume surge
        engine_with_history.update_price("VCB", 100.0, 10000, 101.0, 99.0)

        result = engine_with_history.detect_volume_surge("VCB", threshold=2.0)
        assert isinstance(result, bool)

    def test_generate_signal_insufficient_history(self, engine):
        """Test signal generation with insufficient history"""
        engine.update_price("VCB", 100.0, 1000, 101.0, 99.0)

        signal = engine.generate_signal("VCB", 100.0)
        assert signal is None  # Not enough history

    def test_generate_signal_with_history(self, engine_with_history):
        """Test signal generation with sufficient history"""
        signal = engine_with_history.generate_signal("VCB", 100.0)

        assert signal is not None
        assert signal.symbol == "VCB"
        assert isinstance(signal.signal_type, SignalType)
        assert isinstance(signal.strength, SignalStrength)
        assert signal.price == 100.0

    def test_signal_indicators(self, engine_with_history):
        """Test that signal contains indicators"""
        signal = engine_with_history.generate_signal("VCB", 100.0)

        if signal:
            assert "sma_20" in signal.indicators
            assert "rsi" in signal.indicators
            assert "support" in signal.indicators
            assert "resistance" in signal.indicators


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
