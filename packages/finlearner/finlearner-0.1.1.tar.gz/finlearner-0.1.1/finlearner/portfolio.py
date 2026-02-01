"""
Portfolio Optimization Module.

Provides multiple portfolio optimization strategies:
- Markowitz Mean-Variance Optimization
- Black-Litterman Model
- Risk Parity
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from typing import Dict, List, Optional, Tuple, Union


class PortfolioOptimizer:
    """
    Optimizes asset allocation using Mean-Variance Optimization (Markowitz).
    """
    def __init__(self, tickers: list, start: str, end: str):
        import yfinance as yf
        data = yf.download(tickers, start=start, end=end)
        # Handle newer yfinance MultiIndex columns
        if isinstance(data.columns, pd.MultiIndex):
            self.data = data['Close']
        else:
            self.data = data['Close'] if 'Close' in data.columns else data['Adj Close']
        self.returns = self.data.pct_change()
        self.tickers = tickers
        
    def optimize(self, num_portfolios: int = 5000):
        """
        Simulates random portfolios to find the Efficient Frontier.
        """
        results = np.zeros((3, num_portfolios))
        weights_record = []
        
        mean_daily_returns = self.returns.mean()
        cov_matrix = self.returns.cov()
        
        for i in range(num_portfolios):
            weights = np.random.random(len(self.data.columns))
            weights /= np.sum(weights)
            weights_record.append(weights)
            
            # Portfolio return and volatility
            portfolio_return = np.sum(mean_daily_returns * weights) * 252
            portfolio_std_dev = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(252)
            
            results[0,i] = portfolio_std_dev
            results[1,i] = portfolio_return
            results[2,i] = results[1,i] / results[0,i] # Sharpe Ratio

        # Find max Sharpe ratio
        max_sharpe_idx = np.argmax(results[2])
        sdp, rp = results[0,max_sharpe_idx], results[1,max_sharpe_idx]
        max_sharpe_allocation = pd.DataFrame(weights_record[max_sharpe_idx], index=self.data.columns, columns=['allocation'])
        
        return results, max_sharpe_allocation, (sdp, rp)


class BlackLittermanOptimizer:
    """
    Black-Litterman Portfolio Optimization Model.
    
    Combines market equilibrium (CAPM) with investor views to produce
    a more stable and intuitive portfolio allocation.
    
    Key advantages over traditional Markowitz:
    - Incorporates investor views/beliefs
    - More stable allocations
    - Better handling of estimation error
    
    Example:
        >>> optimizer = BlackLittermanOptimizer(tickers=['AAPL', 'GOOG', 'MSFT'],
        ...                                     start='2023-01-01', end='2024-01-01')
        >>> views = {'AAPL': 0.10}  # Expect AAPL to return 10%
        >>> weights, metrics = optimizer.optimize(views=views)
    """
    
    def __init__(self, tickers: List[str], start: str, end: str,
                 risk_free_rate: float = 0.02,
                 market_cap_weights: Optional[Dict[str, float]] = None):
        """
        Initialize Black-Litterman optimizer.
        
        Args:
            tickers: List of ticker symbols
            start: Start date for historical data
            end: End date for historical data  
            risk_free_rate: Annual risk-free rate
            market_cap_weights: Market cap weights (if None, uses equal weights)
        """
        import yfinance as yf
        
        self.tickers = tickers
        self.risk_free_rate = risk_free_rate
        
        # Download data
        data = yf.download(tickers, start=start, end=end)
        # Handle newer yfinance MultiIndex columns
        if isinstance(data.columns, pd.MultiIndex):
            self.data = data['Close']
        else:
            self.data = data['Close'] if 'Close' in data.columns else data['Adj Close']
        self.returns = self.data.pct_change().dropna()
        
        # Calculate covariance matrix (annualized)
        self.cov_matrix = self.returns.cov() * 252
        
        # Market cap weights (default: equal weights)
        if market_cap_weights:
            self.market_weights = np.array([market_cap_weights.get(t, 1/len(tickers)) 
                                           for t in tickers])
        else:
            self.market_weights = np.ones(len(tickers)) / len(tickers)
        self.market_weights = self.market_weights / self.market_weights.sum()
        
        # Risk aversion parameter (derived from market)
        self.delta = self._calculate_risk_aversion()
        
        # Equilibrium excess returns (implied by market)
        self.pi = self._calculate_equilibrium_returns()
    
    def _calculate_risk_aversion(self) -> float:
        """Calculate implied market risk aversion."""
        # Using market Sharpe ratio approach
        market_return = (self.returns @ self.market_weights).mean() * 252
        market_var = self.market_weights @ self.cov_matrix @ self.market_weights
        
        # delta = (E[Rm] - Rf) / Var(Rm)
        delta = (market_return - self.risk_free_rate) / market_var
        return max(delta, 2.5)  # Floor at reasonable value
    
    def _calculate_equilibrium_returns(self) -> np.ndarray:
        """Calculate equilibrium excess returns using reverse optimization."""
        # pi = delta * Sigma * w_mkt
        pi = self.delta * (self.cov_matrix.values @ self.market_weights)
        return pi
    
    def optimize(self, 
                 views: Optional[Dict[str, float]] = None,
                 view_confidences: Optional[Dict[str, float]] = None,
                 tau: float = 0.05) -> Tuple[pd.DataFrame, Dict]:
        """
        Optimize portfolio using Black-Litterman model.
        
        Args:
            views: Dict mapping ticker to expected absolute return
                   e.g., {'AAPL': 0.15} means expect AAPL to return 15%
            view_confidences: Dict mapping ticker to confidence (0-1)
            tau: Scaling factor for prior uncertainty (typically 0.01-0.1)
            
        Returns:
            Tuple of (allocation DataFrame, metrics dict)
        """
        n = len(self.tickers)
        
        if views is None or len(views) == 0:
            # No views: use equilibrium returns
            posterior_returns = self.pi
        else:
            # Build P (pick matrix) and Q (view returns)
            P = np.zeros((len(views), n))
            Q = np.zeros(len(views))
            
            for i, (ticker, expected_return) in enumerate(views.items()):
                if ticker in self.tickers:
                    idx = self.tickers.index(ticker)
                    P[i, idx] = 1.0
                    Q[i] = expected_return - self.risk_free_rate  # Excess return
            
            # Omega: uncertainty in views (diagonal matrix)
            if view_confidences:
                # Higher confidence = lower uncertainty
                omega_diag = [(1 - view_confidences.get(t, 0.5)) * 0.1 
                             for t in views.keys()]
            else:
                # Use proportional variance
                omega_diag = np.diag(tau * P @ self.cov_matrix.values @ P.T)
            
            Omega = np.diag(omega_diag)
            Sigma = self.cov_matrix.values
            
            # Black-Litterman formula for posterior returns
            # E[R] = [(tau*Sigma)^-1 + P'*Omega^-1*P]^-1 * [(tau*Sigma)^-1*pi + P'*Omega^-1*Q]
            tau_sigma_inv = np.linalg.inv(tau * Sigma)
            omega_inv = np.linalg.inv(Omega)
            
            M = np.linalg.inv(tau_sigma_inv + P.T @ omega_inv @ P)
            posterior_returns = M @ (tau_sigma_inv @ self.pi + P.T @ omega_inv @ Q)
        
        # Optimize weights using posterior returns
        Sigma = self.cov_matrix.values
        
        # Mean-variance optimization with posterior returns
        weights = self._optimize_weights(posterior_returns, Sigma)
        
        # Calculate portfolio metrics
        portfolio_return = weights @ posterior_returns + self.risk_free_rate
        portfolio_vol = np.sqrt(weights @ Sigma @ weights)
        sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol
        
        allocation = pd.DataFrame({
            'Ticker': self.tickers,
            'Weight': weights,
            'Expected_Return': posterior_returns + self.risk_free_rate
        }).set_index('Ticker')
        
        metrics = {
            'expected_return': portfolio_return,
            'volatility': portfolio_vol,
            'sharpe_ratio': sharpe,
            'risk_aversion': self.delta
        }
        
        return allocation, metrics
    
    def _optimize_weights(self, expected_returns: np.ndarray, 
                          cov_matrix: np.ndarray) -> np.ndarray:
        """Optimize portfolio weights using quadratic programming."""
        n = len(expected_returns)
        
        def neg_sharpe(w):
            ret = w @ expected_returns
            vol = np.sqrt(w @ cov_matrix @ w)
            return -ret / vol if vol > 0 else 0
        
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}  # Weights sum to 1
        ]
        bounds = [(0, 1) for _ in range(n)]  # No short selling
        
        result = minimize(neg_sharpe, 
                         x0=np.ones(n) / n,
                         method='SLSQP',
                         bounds=bounds,
                         constraints=constraints)
        
        return result.x


class RiskParityOptimizer:
    """
    Risk Parity Portfolio Optimization.
    
    Allocates assets such that each asset contributes equally to portfolio risk.
    This approach focuses on risk allocation rather than capital allocation.
    
    Key advantages:
    - More diversified risk exposure
    - Less sensitive to expected return estimates
    - Historically stable performance across market regimes
    
    Example:
        >>> optimizer = RiskParityOptimizer(tickers=['AAPL', 'GOOG', 'MSFT', 'BND'],
        ...                                 start='2023-01-01', end='2024-01-01')
        >>> weights, risk_contrib = optimizer.optimize()
    """
    
    def __init__(self, tickers: List[str], start: str, end: str):
        """
        Initialize Risk Parity optimizer.
        
        Args:
            tickers: List of ticker symbols
            start: Start date
            end: End date
        """
        import yfinance as yf
        
        self.tickers = tickers
        data = yf.download(tickers, start=start, end=end)
        # Handle newer yfinance MultiIndex columns
        if isinstance(data.columns, pd.MultiIndex):
            self.data = data['Close']
        else:
            self.data = data['Close'] if 'Close' in data.columns else data['Adj Close']
        self.returns = self.data.pct_change().dropna()
        self.cov_matrix = self.returns.cov() * 252  # Annualized
    
    def _risk_contribution(self, weights: np.ndarray, 
                           cov_matrix: np.ndarray) -> np.ndarray:
        """Calculate marginal risk contribution of each asset."""
        portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
        marginal_contrib = cov_matrix @ weights
        risk_contrib = weights * marginal_contrib / portfolio_vol
        return risk_contrib
    
    def _risk_parity_objective(self, weights: np.ndarray, 
                               cov_matrix: np.ndarray) -> float:
        """
        Objective function: minimize deviation from equal risk contribution.
        """
        risk_contrib = self._risk_contribution(weights, cov_matrix)
        target_contrib = np.ones(len(weights)) / len(weights)
        
        # Minimize squared difference from target
        portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
        relative_contrib = risk_contrib / portfolio_vol
        
        return np.sum((relative_contrib - target_contrib) ** 2)
    
    def optimize(self, 
                 target_risk_budget: Optional[Dict[str, float]] = None
                 ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Optimize for risk parity allocation.
        
        Args:
            target_risk_budget: Optional custom risk budget per asset
                               (default: equal risk contribution)
        
        Returns:
            Tuple of (allocation DataFrame, risk_contribution DataFrame)
        """
        n = len(self.tickers)
        cov_matrix = self.cov_matrix.values
        
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}  # Weights sum to 1
        ]
        bounds = [(0.01, 1) for _ in range(n)]  # Min 1% allocation
        
        # Optimization
        result = minimize(
            self._risk_parity_objective,
            x0=np.ones(n) / n,
            args=(cov_matrix,),
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )
        
        optimal_weights = result.x
        optimal_weights = optimal_weights / optimal_weights.sum()  # Normalize
        
        # Calculate final risk contributions
        risk_contrib = self._risk_contribution(optimal_weights, cov_matrix)
        portfolio_vol = np.sqrt(optimal_weights @ cov_matrix @ optimal_weights)
        relative_contrib = risk_contrib / portfolio_vol
        
        # Build results
        allocation = pd.DataFrame({
            'Ticker': self.tickers,
            'Weight': optimal_weights,
            'Risk_Contribution': risk_contrib,
            'Relative_Risk_Contrib': relative_contrib
        }).set_index('Ticker')
        
        # Portfolio metrics
        expected_return = (self.returns @ optimal_weights).mean() * 252
        
        metrics = pd.DataFrame({
            'Metric': ['Expected Return', 'Volatility', 'Sharpe Ratio'],
            'Value': [expected_return, portfolio_vol, expected_return / portfolio_vol]
        }).set_index('Metric')
        
        return allocation, metrics
    
    def compare_with_equal_weight(self) -> pd.DataFrame:
        """
        Compare risk parity vs equal weight allocation.
        
        Returns:
            DataFrame comparing both strategies
        """
        n = len(self.tickers)
        cov_matrix = self.cov_matrix.values
        
        # Equal weight
        eq_weights = np.ones(n) / n
        eq_risk_contrib = self._risk_contribution(eq_weights, cov_matrix)
        eq_vol = np.sqrt(eq_weights @ cov_matrix @ eq_weights)
        
        # Risk parity
        rp_allocation, _ = self.optimize()
        rp_weights = rp_allocation['Weight'].values
        rp_risk_contrib = self._risk_contribution(rp_weights, cov_matrix)
        rp_vol = np.sqrt(rp_weights @ cov_matrix @ rp_weights)
        
        comparison = pd.DataFrame({
            'Ticker': self.tickers,
            'EW_Weight': eq_weights,
            'EW_Risk_Contrib': eq_risk_contrib / eq_vol,
            'RP_Weight': rp_weights,
            'RP_Risk_Contrib': rp_risk_contrib / rp_vol
        }).set_index('Ticker')
        
        return comparison