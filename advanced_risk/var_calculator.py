"""
Advanced Risk Management - Value at Risk (VaR) Calculator
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from loguru import logger

from core.risk_manager import risk_manager
from core.signal_engine import signal_engine


class VaRCalculator:
    """
    Value at Risk Calculator

    Methods:
    - Historical VaR
    - Parametric VaR (Variance-Covariance)
    - Monte Carlo VaR
    """

    def __init__(self, confidence_level: float = 0.95):
        """
        Args:
            confidence_level: Confidence level for VaR (default 95%)
        """
        self.confidence_level = confidence_level

    def calculate_historical_var(
        self,
        returns: pd.Series,
        holding_period: int = 1,
    ) -> float:
        """
        Calculate Historical VaR

        Args:
            returns: Historical returns series
            holding_period: Holding period in days

        Returns:
            VaR value
        """
        if len(returns) < 30:
            logger.warning("Insufficient data for VaR calculation")
            return 0.0

        # Scale returns for holding period
        scaled_returns = returns * np.sqrt(holding_period)

        # Calculate VaR as percentile
        var = np.percentile(scaled_returns, (1 - self.confidence_level) * 100)

        return abs(var)

    def calculate_parametric_var(
        self,
        returns: pd.Series,
        holding_period: int = 1,
    ) -> float:
        """
        Calculate Parametric VaR (assumes normal distribution)

        Args:
            returns: Historical returns series
            holding_period: Holding period in days

        Returns:
            VaR value
        """
        if len(returns) < 30:
            return 0.0

        # Calculate mean and std
        mean = returns.mean()
        std = returns.std()

        # Z-score for confidence level
        from scipy.stats import norm
        z_score = norm.ppf(1 - self.confidence_level)

        # VaR formula
        var = -(mean + z_score * std) * np.sqrt(holding_period)

        return abs(var)

    def calculate_monte_carlo_var(
        self,
        returns: pd.Series,
        portfolio_value: float,
        holding_period: int = 1,
        simulations: int = 10000,
    ) -> float:
        """
        Calculate Monte Carlo VaR

        Args:
            returns: Historical returns series
            portfolio_value: Current portfolio value
            holding_period: Holding period in days
            simulations: Number of simulations

        Returns:
            VaR value in currency
        """
        if len(returns) < 30:
            return 0.0

        mean = returns.mean()
        std = returns.std()

        # Generate random returns
        simulated_returns = np.random.normal(
            mean * holding_period,
            std * np.sqrt(holding_period),
            simulations
        )

        # Calculate portfolio values
        simulated_values = portfolio_value * (1 + simulated_returns)

        # Calculate losses
        losses = portfolio_value - simulated_values

        # VaR is the percentile of losses
        var = np.percentile(losses, self.confidence_level * 100)

        return var

    def calculate_portfolio_var(
        self,
        method: str = "historical",
        holding_period: int = 1,
    ) -> Dict:
        """
        Calculate VaR for current portfolio

        Args:
            method: "historical", "parametric", or "monte_carlo"
            holding_period: Holding period in days

        Returns:
            Dictionary with VaR metrics
        """
        # Get portfolio data
        portfolio_summary = risk_manager.get_portfolio_summary()
        total_value = portfolio_summary["total_value"]

        # Calculate portfolio returns (simplified - using first position)
        returns_list = []
        for symbol in risk_manager.positions:
            history = signal_engine.price_histories.get(symbol)
            if history and len(history) >= 30:
                df = history.get_dataframe()
                returns = df["close"].pct_change().dropna()
                returns_list.append(returns)

        if not returns_list:
            return {"error": "Insufficient data for VaR calculation"}

        # Use first available returns (simplified)
        returns = returns_list[0]

        if method == "historical":
            var_pct = self.calculate_historical_var(returns, holding_period)
        elif method == "parametric":
            var_pct = self.calculate_parametric_var(returns, holding_period)
        elif method == "monte_carlo":
            var_value = self.calculate_monte_carlo_var(returns, total_value, holding_period)
            return {
                "method": method,
                "var_value": var_value,
                "var_percent": var_value / total_value if total_value > 0 else 0,
                "confidence_level": self.confidence_level,
                "holding_period": holding_period,
            }
        else:
            raise ValueError(f"Unknown method: {method}")

        return {
            "method": method,
            "var_percent": var_pct,
            "var_value": var_pct * total_value,
            "confidence_level": self.confidence_level,
            "holding_period": holding_period,
        }


class PortfolioHedging:
    """
    Portfolio Hedging Strategies
    """

    @staticmethod
    def calculate_hedge_ratio(
        portfolio_beta: float,
        portfolio_value: float,
        hedge_instrument_value: float,
    ) -> float:
        """
        Calculate optimal hedge ratio

        Args:
            portfolio_beta: Portfolio beta
            portfolio_value: Portfolio value
            hedge_instrument_value: Value of hedging instrument

        Returns:
            Hedge ratio (number of hedge instruments needed)
        """
        hedge_ratio = (portfolio_beta * portfolio_value) / hedge_instrument_value
        return hedge_ratio

    @staticmethod
    def suggest_hedge(portfolio_value: float, target_beta: float = 0) -> Dict:
        """
        Suggest hedging strategy

        Args:
            portfolio_value: Current portfolio value
            target_beta: Target beta after hedging (0 = market neutral)

        Returns:
            Hedging recommendations
        """
        # Simplified hedging suggestion
        # In practice, would use futures or options

        current_beta = 1.0  # Assume market beta

        hedge_amount = portfolio_value * (current_beta - target_beta)

        return {
            "current_beta": current_beta,
            "target_beta": target_beta,
            "hedge_amount": hedge_amount,
            "recommendation": (
                f"To achieve target beta of {target_beta}, "
                f"hedge {hedge_amount:,.0f} VND worth of market exposure"
            ),
        }


# Global instance
var_calculator = VaRCalculator()
portfolio_hedging = PortfolioHedging()
