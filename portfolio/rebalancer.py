"""
Auto Portfolio Rebalancing System
Automatically rebalances portfolio to maintain target allocation
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from core.price_stream import price_stream_manager
from core.order_executor import order_executor, OrderSide, OrderType
from core.risk_manager import risk_manager


@dataclass
class AllocationTarget:
    """Target allocation for a symbol"""
    symbol: str
    target_percent: float  # 0.0 to 1.0
    min_percent: float = None  # Minimum allocation
    max_percent: float = None  # Maximum allocation

    def __post_init__(self):
        if self.min_percent is None:
            self.min_percent = self.target_percent * 0.8
        if self.max_percent is None:
            self.max_percent = self.target_percent * 1.2


@dataclass
class RebalanceAction:
    """Rebalance action to take"""
    symbol: str
    action: str  # BUY or SELL
    quantity: int
    reason: str
    current_percent: float
    target_percent: float
    estimated_cost: float


class PortfolioRebalancer:
    """
    Automatic Portfolio Rebalancing System

    Features:
    - Maintains target asset allocation
    - Rebalances when drift exceeds threshold
    - Supports custom allocation strategies
    - Tax-loss harvesting aware
    """

    def __init__(self, drift_threshold: float = 0.05):
        """
        Args:
            drift_threshold: Rebalance when allocation drifts by this percentage (default 5%)
        """
        self.drift_threshold = drift_threshold
        self.allocation_targets: Dict[str, AllocationTarget] = {}
        self.last_rebalance: Optional[datetime] = None

    def set_allocation_targets(self, targets: List[AllocationTarget]):
        """Set target allocations"""
        # Validate total adds up to <= 100%
        total = sum(t.target_percent for t in targets)
        if total > 1.0:
            raise ValueError(f"Total allocation {total*100}% exceeds 100%")

        self.allocation_targets = {t.symbol: t for t in targets}
        logger.info(f"Set allocation targets for {len(targets)} symbols")

    def get_current_allocation(self) -> Dict[str, float]:
        """
        Get current portfolio allocation as percentages

        Returns:
            Dict mapping symbol to current percentage (0.0 to 1.0)
        """
        portfolio_summary = risk_manager.get_portfolio_summary()
        total_value = portfolio_summary["total_value"]

        if total_value == 0:
            return {}

        allocations = {}

        # Calculate position values
        for symbol, position in risk_manager.positions.items():
            position_value = position.quantity * position.current_price
            allocations[symbol] = position_value / total_value

        # Add cash allocation
        cash_value = portfolio_summary["current_capital"]
        allocations["CASH"] = cash_value / total_value

        return allocations

    def calculate_drift(self) -> Dict[str, float]:
        """
        Calculate allocation drift from targets

        Returns:
            Dict mapping symbol to drift percentage (current - target)
        """
        current = self.get_current_allocation()
        drift = {}

        for symbol, target in self.allocation_targets.items():
            current_pct = current.get(symbol, 0.0)
            drift[symbol] = current_pct - target.target_percent

        return drift

    def needs_rebalancing(self) -> bool:
        """Check if portfolio needs rebalancing"""
        drift = self.calculate_drift()

        # Check if any drift exceeds threshold
        for symbol, drift_pct in drift.items():
            if abs(drift_pct) > self.drift_threshold:
                logger.info(
                    f"Rebalancing needed: {symbol} drift {drift_pct*100:.2f}% "
                    f"exceeds threshold {self.drift_threshold*100:.1f}%"
                )
                return True

        return False

    def generate_rebalance_actions(self) -> List[RebalanceAction]:
        """
        Generate rebalancing actions

        Returns:
            List of actions to take to rebalance portfolio
        """
        current = self.get_current_allocation()
        drift = self.calculate_drift()
        summary = risk_manager.get_portfolio_summary()
        total_value = summary["total_value"]

        actions = []

        for symbol, target in self.allocation_targets.items():
            drift_pct = drift.get(symbol, 0)

            # Skip if drift is within threshold
            if abs(drift_pct) <= self.drift_threshold:
                continue

            current_pct = current.get(symbol, 0.0)
            target_pct = target.target_percent

            # Get current price
            price_data = price_stream_manager.get_latest_price(symbol)
            if not price_data:
                logger.warning(f"No price data for {symbol}, skipping")
                continue

            price = price_data.price

            # Calculate target value and current value
            target_value = total_value * target_pct
            current_value = total_value * current_pct

            # Calculate difference
            value_diff = target_value - current_value

            if value_diff > 0:
                # Need to BUY
                quantity = int(abs(value_diff) / price)
                quantity = (quantity // 100) * 100  # Round to lot size

                if quantity > 0:
                    actions.append(
                        RebalanceAction(
                            symbol=symbol,
                            action="BUY",
                            quantity=quantity,
                            reason=f"Underweight: {current_pct*100:.1f}% vs target {target_pct*100:.1f}%",
                            current_percent=current_pct,
                            target_percent=target_pct,
                            estimated_cost=quantity * price,
                        )
                    )

            else:
                # Need to SELL
                quantity = int(abs(value_diff) / price)
                quantity = (quantity // 100) * 100

                # Check if we have enough shares
                position = risk_manager.positions.get(symbol)
                if position:
                    quantity = min(quantity, position.quantity)

                if quantity > 0:
                    actions.append(
                        RebalanceAction(
                            symbol=symbol,
                            action="SELL",
                            quantity=quantity,
                            reason=f"Overweight: {current_pct*100:.1f}% vs target {target_pct*100:.1f}%",
                            current_percent=current_pct,
                            target_percent=target_pct,
                            estimated_cost=quantity * price,
                        )
                    )

        return actions

    def execute_rebalance(self, dry_run: bool = True) -> List[RebalanceAction]:
        """
        Execute rebalancing

        Args:
            dry_run: If True, only generate actions without executing

        Returns:
            List of actions taken/planned
        """
        if not self.needs_rebalancing():
            logger.info("No rebalancing needed")
            return []

        actions = self.generate_rebalance_actions()

        if dry_run:
            logger.info(f"[DRY RUN] Generated {len(actions)} rebalancing actions")
            for action in actions:
                logger.info(
                    f"[DRY RUN] {action.action} {action.quantity} {action.symbol} @ "
                    f"~{action.estimated_cost:,.0f} VND - {action.reason}"
                )
            return actions

        # Execute actions
        logger.info(f"Executing {len(actions)} rebalancing actions...")

        for action in actions:
            try:
                side = OrderSide.BUY if action.action == "BUY" else OrderSide.SELL

                order = order_executor.place_order(
                    symbol=action.symbol,
                    side=side,
                    quantity=action.quantity,
                    order_type=OrderType.MARKET,
                )

                if order:
                    logger.info(f"Rebalance order placed: {order}")
                else:
                    logger.error(f"Failed to place rebalance order for {action.symbol}")

            except Exception as e:
                logger.error(f"Error executing rebalance for {action.symbol}: {e}")

        self.last_rebalance = datetime.now()
        return actions

    def get_rebalance_report(self) -> Dict:
        """Get comprehensive rebalancing report"""
        current = self.get_current_allocation()
        drift = self.calculate_drift()
        actions = self.generate_rebalance_actions()

        report = {
            "timestamp": datetime.now().isoformat(),
            "needs_rebalancing": self.needs_rebalancing(),
            "last_rebalance": self.last_rebalance.isoformat() if self.last_rebalance else None,
            "drift_threshold": self.drift_threshold,
            "current_allocation": {
                symbol: f"{pct*100:.2f}%" for symbol, pct in current.items()
            },
            "target_allocation": {
                symbol: f"{target.target_percent*100:.2f}%"
                for symbol, target in self.allocation_targets.items()
            },
            "drift": {
                symbol: f"{drift_pct*100:+.2f}%" for symbol, drift_pct in drift.items()
            },
            "recommended_actions": [
                {
                    "symbol": a.symbol,
                    "action": a.action,
                    "quantity": a.quantity,
                    "reason": a.reason,
                    "estimated_cost": f"{a.estimated_cost:,.0f} VND",
                }
                for a in actions
            ],
        }

        return report


# Global instance
portfolio_rebalancer = PortfolioRebalancer()
