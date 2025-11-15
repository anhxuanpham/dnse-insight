#!/usr/bin/env python3
"""
Example: Portfolio Rebalancing
"""
from portfolio.rebalancer import portfolio_rebalancer, AllocationTarget
from loguru import logger


def main():
    """Run portfolio rebalancing example"""
    logger.info("Portfolio Rebalancing Example")

    # Define target allocation
    targets = [
        AllocationTarget(symbol="VCB", target_percent=0.30),  # 30%
        AllocationTarget(symbol="VHM", target_percent=0.25),  # 25%
        AllocationTarget(symbol="VIC", target_percent=0.20),  # 20%
        AllocationTarget(symbol="FPT", target_percent=0.15),  # 15%
        AllocationTarget(symbol="CASH", target_percent=0.10),  # 10%
    ]

    portfolio_rebalancer.set_allocation_targets(targets)

    # Get current allocation
    current = portfolio_rebalancer.get_current_allocation()
    logger.info("Current Allocation:")
    for symbol, pct in current.items():
        logger.info(f"  {symbol}: {pct*100:.2f}%")

    # Calculate drift
    drift = portfolio_rebalancer.calculate_drift()
    logger.info("\nAllocation Drift:")
    for symbol, drift_pct in drift.items():
        logger.info(f"  {symbol}: {drift_pct*100:+.2f}%")

    # Check if rebalancing needed
    if portfolio_rebalancer.needs_rebalancing():
        logger.warning("\n⚠️  Rebalancing needed!")

        # Get rebalancing actions
        actions = portfolio_rebalancer.generate_rebalance_actions()
        logger.info(f"\nRecommended Actions ({len(actions)}):")
        for action in actions:
            logger.info(
                f"  {action.action} {action.quantity} {action.symbol} - {action.reason}"
            )

        # Get full report
        report = portfolio_rebalancer.get_rebalance_report()
        logger.info(f"\nFull Report: {report}")

        # Execute rebalancing (DRY RUN)
        logger.info("\n🔄 Executing rebalancing (DRY RUN)...")
        portfolio_rebalancer.execute_rebalance(dry_run=True)

    else:
        logger.success("✅ Portfolio is balanced!")


if __name__ == "__main__":
    main()
