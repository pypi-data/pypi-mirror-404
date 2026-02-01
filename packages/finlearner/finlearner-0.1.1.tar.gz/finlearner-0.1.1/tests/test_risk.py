"""
Unit tests for finlearner.risk module.
"""
import pytest
import numpy as np
import pandas as pd
from finlearner.risk import (
    RiskMetrics,
    historical_var,
    parametric_var,
    monte_carlo_var,
    cvar,
    max_drawdown
)


class TestRiskMetrics:
    """Tests for the RiskMetrics class."""
    
    @pytest.fixture
    def sample_returns(self):
        """Create sample returns for testing."""
        np.random.seed(42)
        return pd.Series(np.random.normal(0.001, 0.02, 252))
    
    @pytest.fixture
    def sample_prices(self):
        """Create sample prices for testing."""
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 252)
        prices = 100 * np.cumprod(1 + returns)
        return pd.Series(prices)
    
    def test_init_with_series(self, sample_returns):
        """Test initialization with pandas Series."""
        risk = RiskMetrics(sample_returns)
        assert len(risk.returns) == 252
    
    def test_init_with_numpy(self, sample_returns):
        """Test initialization with numpy array."""
        risk = RiskMetrics(sample_returns.values)
        assert len(risk.returns) == 252
    
    def test_from_prices(self, sample_prices):
        """Test creation from price series."""
        risk = RiskMetrics.from_prices(sample_prices)
        # Returns have one less element than prices
        assert len(risk.returns) == 251
    
    # ========== VaR Tests ==========
    
    def test_historical_var_positive(self, sample_returns):
        """Test that historical VaR returns positive value."""
        risk = RiskMetrics(sample_returns)
        var = risk.historical_var(confidence=0.95)
        assert var > 0
    
    def test_historical_var_confidence_levels(self, sample_returns):
        """Test that higher confidence = higher VaR."""
        risk = RiskMetrics(sample_returns)
        var_95 = risk.historical_var(confidence=0.95)
        var_99 = risk.historical_var(confidence=0.99)
        assert var_99 > var_95
    
    def test_parametric_var_positive(self, sample_returns):
        """Test that parametric VaR returns positive value."""
        risk = RiskMetrics(sample_returns)
        var = risk.parametric_var(confidence=0.95)
        assert var > 0
    
    def test_monte_carlo_var_positive(self, sample_returns):
        """Test that Monte Carlo VaR returns positive value."""
        risk = RiskMetrics(sample_returns)
        var = risk.monte_carlo_var(confidence=0.95, simulations=1000, seed=42)
        assert var > 0
    
    def test_monte_carlo_var_reproducible(self, sample_returns):
        """Test that Monte Carlo VaR is reproducible with seed."""
        risk = RiskMetrics(sample_returns)
        var1 = risk.monte_carlo_var(confidence=0.95, simulations=1000, seed=42)
        var2 = risk.monte_carlo_var(confidence=0.95, simulations=1000, seed=42)
        assert var1 == pytest.approx(var2)
    
    def test_cornish_fisher_var(self, sample_returns):
        """Test Cornish-Fisher VaR adjusts for skew/kurtosis."""
        risk = RiskMetrics(sample_returns)
        cf_var = risk.cornish_fisher_var(confidence=0.95)
        param_var = risk.parametric_var(confidence=0.95)
        # Should differ due to skewness/kurtosis adjustment
        assert cf_var != param_var
    
    # ========== CVaR Tests ==========
    
    def test_cvar_greater_than_var(self, sample_returns):
        """Test that CVaR >= VaR (expected shortfall is larger)."""
        risk = RiskMetrics(sample_returns)
        var = risk.historical_var(confidence=0.95)
        cvar_val = risk.cvar(confidence=0.95)
        assert cvar_val >= var
    
    def test_cvar_historical_method(self, sample_returns):
        """Test CVaR with historical method."""
        risk = RiskMetrics(sample_returns)
        cvar_val = risk.cvar(confidence=0.95, method='historical')
        assert cvar_val > 0
    
    def test_cvar_parametric_method(self, sample_returns):
        """Test CVaR with parametric method."""
        risk = RiskMetrics(sample_returns)
        cvar_val = risk.cvar(confidence=0.95, method='parametric')
        assert cvar_val > 0
    
    def test_expected_shortfall_alias(self, sample_returns):
        """Test expected_shortfall is alias for cvar."""
        risk = RiskMetrics(sample_returns)
        cvar_val = risk.cvar(confidence=0.95)
        es_val = risk.expected_shortfall(confidence=0.95)
        assert cvar_val == pytest.approx(es_val)
    
    # ========== Drawdown Tests ==========
    
    def test_max_drawdown_positive(self, sample_prices):
        """Test that max drawdown is a positive percentage."""
        risk = RiskMetrics.from_prices(sample_prices)
        max_dd, dd_series = risk.max_drawdown(sample_prices)
        assert max_dd >= 0
        assert max_dd <= 1  # Should be a fraction
    
    def test_max_drawdown_series(self, sample_prices):
        """Test that drawdown series has correct length."""
        risk = RiskMetrics.from_prices(sample_prices)
        max_dd, dd_series = risk.max_drawdown(sample_prices)
        assert len(dd_series) == len(sample_prices)
    
    def test_calmar_ratio(self, sample_prices):
        """Test Calmar ratio calculation."""
        risk = RiskMetrics.from_prices(sample_prices)
        calmar = risk.calmar_ratio(prices=sample_prices)
        # Should be a finite number
        assert np.isfinite(calmar)
    
    # ========== Summary Tests ==========
    
    def test_summary_returns_dataframe(self, sample_returns):
        """Test that summary returns a DataFrame."""
        risk = RiskMetrics(sample_returns)
        summary = risk.summary(confidence=0.95)
        assert isinstance(summary, pd.DataFrame)
        assert 'Value' in summary.columns
    
    def test_summary_contains_all_metrics(self, sample_returns):
        """Test that summary contains expected metrics."""
        risk = RiskMetrics(sample_returns)
        summary = risk.summary(confidence=0.95)
        
        expected_metrics = [
            'Mean Return',
            'Std Deviation',
            'Skewness',
            'Kurtosis',
            'Maximum Drawdown',
            'Calmar Ratio'
        ]
        
        for metric in expected_metrics:
            assert metric in summary.index


class TestStandaloneFunctions:
    """Tests for standalone risk functions."""
    
    @pytest.fixture
    def sample_returns(self):
        """Create sample returns."""
        np.random.seed(42)
        return pd.Series(np.random.normal(0.001, 0.02, 100))
    
    def test_historical_var_function(self, sample_returns):
        """Test standalone historical_var function."""
        var = historical_var(sample_returns, confidence=0.95)
        assert var > 0
    
    def test_parametric_var_function(self, sample_returns):
        """Test standalone parametric_var function."""
        var = parametric_var(sample_returns, confidence=0.95)
        assert var > 0
    
    def test_monte_carlo_var_function(self, sample_returns):
        """Test standalone monte_carlo_var function."""
        var = monte_carlo_var(sample_returns, confidence=0.95, simulations=1000)
        assert var > 0
    
    def test_cvar_function(self, sample_returns):
        """Test standalone cvar function."""
        cvar_val = cvar(sample_returns, confidence=0.95)
        assert cvar_val > 0
    
    def test_max_drawdown_function(self):
        """Test standalone max_drawdown function."""
        np.random.seed(42)
        prices = pd.Series(100 * np.cumprod(1 + np.random.normal(0.001, 0.02, 100)))
        max_dd, dd_series = max_drawdown(prices)
        assert max_dd >= 0
        assert len(dd_series) == len(prices)
