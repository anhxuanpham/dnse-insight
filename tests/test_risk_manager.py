"""
Unit tests for Risk Manager
"""
import pytest
from core.risk_manager import RiskManager, Position
from core.order_executor import OrderSide


class TestRiskManager:
    """Test RiskManager class"""

    @pytest.fixture
    def risk_manager(self):
        """Create risk manager instance"""
        manager = RiskManager()
        manager.initial_capital = 100_000_000  # 100M VND
        manager.current_capital = 100_000_000
        manager.peak_capital = 100_000_000
        return manager

    def test_calculate_position_size(self, risk_manager):
        """Test position size calculation"""
        entry_price = 100.0
        stop_loss_price = 97.0  # 3% stop loss

        size = risk_manager.calculate_position_size("VCB", entry_price, stop_loss_price)

        assert size > 0
        assert size % 100 == 0  # Should be rounded to lot size

    def test_calculate_stop_loss_price(self, risk_manager):
        """Test stop loss price calculation"""
        entry_price = 100.0

        stop_loss = risk_manager.calculate_stop_loss_price(entry_price, OrderSide.BUY)

        assert stop_loss < entry_price
        assert stop_loss == pytest.approx(97.0, rel=0.01)  # 3% default

    def test_can_open_position(self, risk_manager):
        """Test position opening validation"""
        can_open, reason = risk_manager.can_open_position("VCB", 10_000_000)

        assert can_open is True
        assert reason == "OK"

    def test_cannot_open_position_max_limit(self, risk_manager):
        """Test max position limit"""
        # Open max positions
        for i in range(10):
            risk_manager.open_position(
                symbol=f"VCB{i}", quantity=100, entry_price=100.0, stop_loss_price=97.0
            )

        can_open, reason = risk_manager.can_open_position("VCB11", 10_000_000)

        assert can_open is False
        assert "Maximum positions limit" in reason

    def test_cannot_open_duplicate_position(self, risk_manager):
        """Test duplicate position prevention"""
        risk_manager.open_position(
            symbol="VCB", quantity=100, entry_price=100.0, stop_loss_price=97.0
        )

        can_open, reason = risk_manager.can_open_position("VCB", 10_000_000)

        assert can_open is False
        assert "already exists" in reason

    def test_open_position(self, risk_manager):
        """Test opening a position"""
        initial_capital = risk_manager.current_capital

        position = risk_manager.open_position(
            symbol="VCB", quantity=1000, entry_price=100.0, stop_loss_price=97.0
        )

        assert position is not None
        assert position.symbol == "VCB"
        assert position.quantity == 1000
        assert "VCB" in risk_manager.positions
        assert risk_manager.current_capital < initial_capital

    def test_close_position(self, risk_manager):
        """Test closing a position"""
        # Open position
        risk_manager.open_position(
            symbol="VCB", quantity=1000, entry_price=100.0, stop_loss_price=97.0
        )

        # Close position at profit
        success = risk_manager.close_position("VCB", 105.0, "Take Profit")

        assert success is True
        assert "VCB" not in risk_manager.positions
        assert risk_manager.current_capital > risk_manager.initial_capital

    def test_update_position_price(self, risk_manager):
        """Test updating position price"""
        risk_manager.open_position(
            symbol="VCB", quantity=1000, entry_price=100.0, stop_loss_price=97.0
        )

        risk_manager.update_position_price("VCB", 105.0)

        position = risk_manager.positions["VCB"]
        assert position.current_price == 105.0
        assert position.pnl > 0
        assert position.pnl_percent > 0

    def test_trailing_stop(self, risk_manager):
        """Test trailing stop loss"""
        risk_manager.open_position(
            symbol="VCB", quantity=1000, entry_price=100.0, stop_loss_price=97.0
        )

        # Update price to trigger trailing stop
        risk_manager.update_position_price("VCB", 110.0)
        initial_stop = risk_manager.positions["VCB"].stop_loss_price

        risk_manager.update_trailing_stop("VCB", trailing_pct=0.05)

        new_stop = risk_manager.positions["VCB"].stop_loss_price
        assert new_stop > initial_stop

    def test_portfolio_summary(self, risk_manager):
        """Test portfolio summary generation"""
        # Open some positions
        risk_manager.open_position(
            symbol="VCB", quantity=1000, entry_price=100.0, stop_loss_price=97.0
        )
        risk_manager.open_position(
            symbol="VHM", quantity=500, entry_price=200.0, stop_loss_price=194.0
        )

        summary = risk_manager.get_portfolio_summary()

        assert "initial_capital" in summary
        assert "current_capital" in summary
        assert "total_value" in summary
        assert "num_positions" in summary
        assert summary["num_positions"] == 2


class TestPosition:
    """Test Position class"""

    def test_position_creation(self):
        """Test position creation"""
        position = Position(
            symbol="VCB",
            quantity=1000,
            avg_entry_price=100.0,
            current_price=100.0,
            stop_loss_price=97.0,
        )

        assert position.symbol == "VCB"
        assert position.quantity == 1000
        assert position.pnl == 0.0

    def test_update_pnl(self):
        """Test P&L update"""
        position = Position(
            symbol="VCB",
            quantity=1000,
            avg_entry_price=100.0,
            current_price=100.0,
            stop_loss_price=97.0,
        )

        position.update_pnl(105.0)

        assert position.current_price == 105.0
        assert position.pnl == 5000.0  # (105 - 100) * 1000
        assert position.pnl_percent == pytest.approx(0.05)

    def test_should_stop_loss(self):
        """Test stop loss trigger"""
        position = Position(
            symbol="VCB",
            quantity=1000,
            avg_entry_price=100.0,
            current_price=96.0,
            stop_loss_price=97.0,
        )

        assert position.should_stop_loss() is True

    def test_should_take_profit(self):
        """Test take profit trigger"""
        position = Position(
            symbol="VCB",
            quantity=1000,
            avg_entry_price=100.0,
            current_price=110.0,
            stop_loss_price=97.0,
            take_profit_price=108.0,
        )

        assert position.should_take_profit() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
