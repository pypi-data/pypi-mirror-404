"""
Risk Metrics Module for Financial Analysis.

Provides comprehensive risk measurement tools including:
- Value at Risk (VaR): Historical, Parametric, Monte Carlo
- Conditional VaR (Expected Shortfall)
- Maximum Drawdown analysis
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, Optional, Union, Literal


class RiskMetrics:
    """
    Comprehensive Risk Metrics Calculator for Financial Portfolios.
    
    Provides multiple methods for calculating Value at Risk (VaR),
    Conditional VaR (CVaR/Expected Shortfall), and Drawdown metrics.
    
    Example:
        >>> risk = RiskMetrics(returns)
        >>> var_95 = risk.historical_var(confidence=0.95)
        >>> cvar = risk.cvar(confidence=0.95)
        >>> max_dd, dd_series = risk.max_drawdown()
    """
    
    def __init__(self, returns: Union[pd.Series, np.ndarray]):
        """
        Initialize RiskMetrics with return series.
        
        Args:
            returns: Series of returns (daily, weekly, etc.)
        """
        if isinstance(returns, np.ndarray):
            returns = pd.Series(returns)
        self.returns = returns.dropna()
    
    @classmethod
    def from_prices(cls, prices: Union[pd.Series, np.ndarray]) -> 'RiskMetrics':
        """
        Create RiskMetrics from price series.
        
        Args:
            prices: Series of prices
            
        Returns:
            RiskMetrics instance
        """
        if isinstance(prices, np.ndarray):
            prices = pd.Series(prices)
        returns = prices.pct_change().dropna()
        return cls(returns)
    
    # ================== VALUE AT RISK (VaR) ==================
    
    def historical_var(self, confidence: float = 0.95, 
                       horizon: int = 1) -> float:
        """
        Calculate Historical VaR using empirical distribution.
        
        Args:
            confidence: Confidence level (e.g., 0.95 for 95% VaR)
            horizon: Time horizon in periods (default: 1 day)
            
        Returns:
            VaR value (positive number representing potential loss)
        """
        alpha = 1 - confidence
        var = np.percentile(self.returns, alpha * 100)
        
        # Scale by square root of time for multi-period
        var = var * np.sqrt(horizon)
        
        return -var  # Return positive loss value
    
    def parametric_var(self, confidence: float = 0.95, 
                       horizon: int = 1) -> float:
        """
        Calculate Parametric (Gaussian) VaR.
        
        Assumes returns are normally distributed.
        
        Args:
            confidence: Confidence level (e.g., 0.95 for 95% VaR)
            horizon: Time horizon in periods
            
        Returns:
            VaR value (positive number)
        """
        mu = self.returns.mean()
        sigma = self.returns.std()
        
        # Z-score for confidence level
        z = stats.norm.ppf(1 - confidence)
        
        var = -(mu * horizon + z * sigma * np.sqrt(horizon))
        
        return var
    
    def monte_carlo_var(self, confidence: float = 0.95,
                        horizon: int = 1,
                        simulations: int = 10000,
                        seed: Optional[int] = None) -> float:
        """
        Calculate VaR using Monte Carlo simulation.
        
        Simulates future returns based on historical distribution.
        
        Args:
            confidence: Confidence level
            horizon: Time horizon in periods
            simulations: Number of Monte Carlo simulations
            seed: Random seed for reproducibility
            
        Returns:
            VaR value (positive number)
        """
        if seed is not None:
            np.random.seed(seed)
        
        mu = self.returns.mean()
        sigma = self.returns.std()
        
        # Simulate returns
        simulated_returns = np.random.normal(mu, sigma, (simulations, horizon))
        
        # Calculate cumulative returns over horizon
        cumulative_returns = np.sum(simulated_returns, axis=1)
        
        # Get VaR at confidence level
        alpha = 1 - confidence
        var = np.percentile(cumulative_returns, alpha * 100)
        
        return -var
    
    def cornish_fisher_var(self, confidence: float = 0.95, 
                           horizon: int = 1) -> float:
        """
        Calculate VaR using Cornish-Fisher expansion.
        
        Adjusts for skewness and kurtosis in the return distribution.
        More accurate than parametric VaR for non-normal distributions.
        
        Args:
            confidence: Confidence level
            horizon: Time horizon in periods
            
        Returns:
            VaR value (positive number)
        """
        mu = self.returns.mean()
        sigma = self.returns.std()
        skew = stats.skew(self.returns)
        kurt = stats.kurtosis(self.returns)  # Excess kurtosis
        
        z = stats.norm.ppf(1 - confidence)
        
        # Cornish-Fisher expansion
        z_cf = (z + 
                (z**2 - 1) * skew / 6 +
                (z**3 - 3*z) * kurt / 24 -
                (2*z**3 - 5*z) * (skew**2) / 36)
        
        var = -(mu * horizon + z_cf * sigma * np.sqrt(horizon))
        
        return var
    
    # ================== CONDITIONAL VAR (CVaR) ==================
    
    def cvar(self, confidence: float = 0.95, 
             method: Literal['historical', 'parametric'] = 'historical',
             horizon: int = 1) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall).
        
        CVaR is the expected loss given that loss exceeds VaR.
        It captures tail risk better than VaR alone.
        
        Args:
            confidence: Confidence level
            method: 'historical' or 'parametric'
            horizon: Time horizon in periods
            
        Returns:
            CVaR value (positive number)
        """
        alpha = 1 - confidence
        
        if method == 'historical':
            var = np.percentile(self.returns, alpha * 100)
            cvar = self.returns[self.returns <= var].mean()
            cvar = cvar * np.sqrt(horizon)
            return -cvar
            
        elif method == 'parametric':
            mu = self.returns.mean()
            sigma = self.returns.std()
            z = stats.norm.ppf(alpha)
            
            # Expected shortfall formula for normal distribution
            es = mu - sigma * stats.norm.pdf(z) / alpha
            es = es * np.sqrt(horizon)
            return -es
        
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def expected_shortfall(self, confidence: float = 0.95, 
                           horizon: int = 1) -> float:
        """Alias for CVaR using historical method."""
        return self.cvar(confidence, method='historical', horizon=horizon)
    
    # ================== DRAWDOWN METRICS ==================
    
    def max_drawdown(self, prices: Optional[pd.Series] = None) -> Tuple[float, pd.Series]:
        """
        Calculate Maximum Drawdown.
        
        Maximum peak-to-trough decline during a specific period.
        
        Args:
            prices: Optional price series (if None, calculated from returns)
            
        Returns:
            Tuple of (max_drawdown, drawdown_series)
        """
        if prices is None:
            # Reconstruct prices from returns (assume starting value of 100)
            prices = (1 + self.returns).cumprod() * 100
        
        # Calculate running maximum
        running_max = prices.cummax()
        
        # Calculate drawdown
        drawdown = (prices - running_max) / running_max
        
        # Maximum drawdown
        max_dd = drawdown.min()
        
        return -max_dd, drawdown  # Return positive value for max_dd
    
    def drawdown_duration(self, prices: Optional[pd.Series] = None) -> pd.DataFrame:
        """
        Calculate drawdown duration statistics.
        
        Args:
            prices: Optional price series
            
        Returns:
            DataFrame with drawdown periods and durations
        """
        if prices is None:
            prices = (1 + self.returns).cumprod() * 100
        
        running_max = prices.cummax()
        drawdown = (prices - running_max) / running_max
        
        # Find drawdown periods
        is_drawdown = drawdown < 0
        drawdown_groups = (~is_drawdown).cumsum()
        
        periods = []
        for group_id in drawdown_groups[is_drawdown].unique():
            mask = (drawdown_groups == group_id) & is_drawdown
            if mask.any():
                start = mask.idxmax()
                end = mask[::-1].idxmax()
                duration = len(prices.loc[start:end])
                min_dd = drawdown.loc[start:end].min()
                periods.append({
                    'start': start,
                    'end': end,
                    'duration': duration,
                    'max_drawdown': -min_dd
                })
        
        return pd.DataFrame(periods)
    
    def calmar_ratio(self, annualization_factor: int = 252,
                     prices: Optional[pd.Series] = None) -> float:
        """
        Calculate Calmar Ratio.
        
        Annualized return divided by maximum drawdown.
        
        Args:
            annualization_factor: Trading days per year
            prices: Optional price series
            
        Returns:
            Calmar ratio
        """
        annual_return = self.returns.mean() * annualization_factor
        max_dd, _ = self.max_drawdown(prices)
        
        return annual_return / max_dd if max_dd != 0 else np.inf
    
    # ================== UTILITY METHODS ==================
    
    def summary(self, confidence: float = 0.95) -> pd.DataFrame:
        """
        Generate a comprehensive risk metrics summary.
        
        Args:
            confidence: Confidence level for VaR calculations
            
        Returns:
            DataFrame with all risk metrics
        """
        max_dd, _ = self.max_drawdown()
        
        metrics = {
            'Mean Return': self.returns.mean(),
            'Std Deviation': self.returns.std(),
            'Skewness': stats.skew(self.returns),
            'Kurtosis': stats.kurtosis(self.returns),
            f'Historical VaR ({confidence:.0%})': self.historical_var(confidence),
            f'Parametric VaR ({confidence:.0%})': self.parametric_var(confidence),
            f'Monte Carlo VaR ({confidence:.0%})': self.monte_carlo_var(confidence, seed=42),
            f'Cornish-Fisher VaR ({confidence:.0%})': self.cornish_fisher_var(confidence),
            f'CVaR ({confidence:.0%})': self.cvar(confidence),
            'Maximum Drawdown': max_dd,
            'Calmar Ratio': self.calmar_ratio()
        }
        
        return pd.DataFrame.from_dict(metrics, orient='index', columns=['Value'])


# ================== STANDALONE FUNCTIONS ==================

def historical_var(returns: Union[pd.Series, np.ndarray], 
                   confidence: float = 0.95) -> float:
    """
    Calculate Historical VaR.
    
    Args:
        returns: Series of returns
        confidence: Confidence level
        
    Returns:
        VaR value
    """
    return RiskMetrics(returns).historical_var(confidence)


def parametric_var(returns: Union[pd.Series, np.ndarray], 
                   confidence: float = 0.95) -> float:
    """Calculate Parametric VaR."""
    return RiskMetrics(returns).parametric_var(confidence)


def monte_carlo_var(returns: Union[pd.Series, np.ndarray],
                    confidence: float = 0.95,
                    simulations: int = 10000) -> float:
    """Calculate Monte Carlo VaR."""
    return RiskMetrics(returns).monte_carlo_var(confidence, simulations=simulations)


def cvar(returns: Union[pd.Series, np.ndarray],
         confidence: float = 0.95) -> float:
    """Calculate CVaR (Expected Shortfall)."""
    return RiskMetrics(returns).cvar(confidence)


def max_drawdown(prices: Union[pd.Series, np.ndarray]) -> Tuple[float, pd.Series]:
    """
    Calculate Maximum Drawdown from prices.
    
    Args:
        prices: Price series
        
    Returns:
        Tuple of (max_drawdown, drawdown_series)
    """
    if isinstance(prices, np.ndarray):
        prices = pd.Series(prices)
    
    running_max = prices.cummax()
    drawdown = (prices - running_max) / running_max
    max_dd = drawdown.min()
    
    return -max_dd, drawdown
