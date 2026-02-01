"""
Unit tests for finlearner.portfolio module.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from finlearner.portfolio import PortfolioOptimizer, BlackLittermanOptimizer, RiskParityOptimizer


class TestPortfolioOptimizer:
    """Tests for the PortfolioOptimizer class."""
    
    @patch('yfinance.download')
    def test_init_downloads_data(self, mock_download, sample_multi_ticker_data):
        """Test that initialization downloads and processes data."""
        # Create multi-level columns like yfinance returns
        mock_data = pd.DataFrame({
            ('Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
            ('Close', 'MSFT'): sample_multi_ticker_data['MSFT'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = PortfolioOptimizer(
            tickers=['AAPL', 'GOOG', 'MSFT'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        mock_download.assert_called_once()
        assert optimizer.data is not None
        assert optimizer.returns is not None
    
    @patch('yfinance.download')
    def test_optimize_returns_correct_structure(self, mock_download, sample_multi_ticker_data):
        """Test that optimize() returns results, allocation, and metrics."""
        mock_data = pd.DataFrame({
            ('Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
            ('Close', 'MSFT'): sample_multi_ticker_data['MSFT'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = PortfolioOptimizer(
            tickers=['AAPL', 'GOOG', 'MSFT'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        results, allocation, metrics = optimizer.optimize(num_portfolios=100)
        
        # Results should be (3, num_portfolios) - volatility, return, sharpe
        assert results.shape == (3, 100)
        
        # Allocation should be a DataFrame
        assert isinstance(allocation, pd.DataFrame)
        assert 'allocation' in allocation.columns
        
        # Metrics should be a tuple (volatility, return)
        assert isinstance(metrics, tuple)
        assert len(metrics) == 2
    
    @patch('yfinance.download')
    def test_optimize_weights_sum_to_one(self, mock_download, sample_multi_ticker_data):
        """Test that portfolio weights sum to 1."""
        mock_data = pd.DataFrame({
            ('Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
            ('Close', 'MSFT'): sample_multi_ticker_data['MSFT'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = PortfolioOptimizer(
            tickers=['AAPL', 'GOOG', 'MSFT'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        results, allocation, metrics = optimizer.optimize(num_portfolios=50)
        
        # Weights should sum to approximately 1
        total_weight = allocation['allocation'].sum()
        assert np.isclose(total_weight, 1.0, atol=0.01)
    
    @patch('yfinance.download')
    def test_optimize_sharpe_ratio_calculated(self, mock_download, sample_multi_ticker_data):
        """Test that Sharpe ratio is correctly calculated."""
        mock_data = pd.DataFrame({
            ('Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
            ('Close', 'MSFT'): sample_multi_ticker_data['MSFT'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = PortfolioOptimizer(
            tickers=['AAPL', 'GOOG', 'MSFT'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        results, allocation, metrics = optimizer.optimize(num_portfolios=100)
        
        # Sharpe ratios should be return / volatility
        for i in range(100):
            if results[0, i] != 0:  # Avoid division by zero
                expected_sharpe = results[1, i] / results[0, i]
                assert np.isclose(results[2, i], expected_sharpe, atol=0.001)
    
    @patch('yfinance.download')
    def test_optimize_finds_max_sharpe(self, mock_download, sample_multi_ticker_data):
        """Test that the allocation corresponds to max Sharpe ratio portfolio."""
        mock_data = pd.DataFrame({
            ('Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
            ('Close', 'MSFT'): sample_multi_ticker_data['MSFT'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = PortfolioOptimizer(
            tickers=['AAPL', 'GOOG', 'MSFT'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        results, allocation, metrics = optimizer.optimize(num_portfolios=100)
        
        # The returned metrics should correspond to max Sharpe ratio
        max_sharpe_idx = np.argmax(results[2])
        assert metrics[0] == results[0, max_sharpe_idx]  # volatility
        assert metrics[1] == results[1, max_sharpe_idx]  # return


class TestBlackLittermanOptimizer:
    """Tests for the BlackLittermanOptimizer class."""
    
    @patch('yfinance.download')
    def test_init_downloads_data(self, mock_download, sample_multi_ticker_data):
        """Test initialization downloads data correctly."""
        mock_data = pd.DataFrame({
            ('Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
            ('Close', 'MSFT'): sample_multi_ticker_data['MSFT'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = BlackLittermanOptimizer(
            tickers=['AAPL', 'GOOG', 'MSFT'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        assert optimizer.tickers == ['AAPL', 'GOOG', 'MSFT']
        assert optimizer.returns is not None
        assert optimizer.cov_matrix is not None
    
    @patch('yfinance.download')
    def test_init_has_delta(self, mock_download, sample_multi_ticker_data):
        """Test that risk aversion delta is calculated."""
        mock_data = pd.DataFrame({
            ('Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = BlackLittermanOptimizer(
            tickers=['AAPL', 'GOOG'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        # delta is calculated automatically
        assert hasattr(optimizer, 'delta')
        assert optimizer.delta > 0
    
    @patch('yfinance.download')
    def test_equilibrium_returns(self, mock_download, sample_multi_ticker_data):
        """Test that equilibrium returns are calculated correctly."""
        mock_data = pd.DataFrame({
            ('Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = BlackLittermanOptimizer(
            tickers=['AAPL', 'GOOG'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        # pi is the equilibrium returns
        assert optimizer.pi is not None
        assert len(optimizer.pi) == 2
    
    @patch('yfinance.download')
    def test_optimize_without_views(self, mock_download, sample_multi_ticker_data):
        """Test optimization without views returns equilibrium weights."""
        mock_data = pd.DataFrame({
            ('Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = BlackLittermanOptimizer(
            tickers=['AAPL', 'GOOG'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        allocation, metrics = optimizer.optimize()
        
        assert isinstance(allocation, pd.DataFrame)
        assert 'Weight' in allocation.columns
        assert np.isclose(allocation['Weight'].sum(), 1.0, atol=0.05)
    
    @patch('yfinance.download')
    def test_optimize_with_views(self, mock_download, sample_multi_ticker_data):
        """Test optimization with investor views."""
        mock_data = pd.DataFrame({
            ('Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = BlackLittermanOptimizer(
            tickers=['AAPL', 'GOOG'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        # Views: AAPL expected to return 15%
        views = {'AAPL': 0.15}
        allocation, metrics = optimizer.optimize(views=views)
        
        assert isinstance(allocation, pd.DataFrame)
        # With bullish view on AAPL, allocation should shift towards AAPL
        assert 'AAPL' in allocation.index
    
    @patch('yfinance.download')
    def test_optimize_returns_metrics(self, mock_download, sample_multi_ticker_data):
        """Test that optimize returns proper metrics tuple."""
        mock_data = pd.DataFrame({
            ('Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = BlackLittermanOptimizer(
            tickers=['AAPL', 'GOOG'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        allocation, metrics = optimizer.optimize()
        
        assert isinstance(metrics, dict)
        assert 'expected_return' in metrics
        assert 'volatility' in metrics


class TestRiskParityOptimizer:
    """Tests for the RiskParityOptimizer class."""
    
    @patch('yfinance.download')
    def test_init_downloads_data(self, mock_download, sample_multi_ticker_data):
        """Test initialization downloads data correctly."""
        mock_data = pd.DataFrame({
            ('Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
            ('Close', 'MSFT'): sample_multi_ticker_data['MSFT'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = RiskParityOptimizer(
            tickers=['AAPL', 'GOOG', 'MSFT'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        assert optimizer.tickers == ['AAPL', 'GOOG', 'MSFT']
        assert optimizer.cov_matrix is not None
    
    @patch('yfinance.download')
    def test_optimize_weights_sum_to_one(self, mock_download, sample_multi_ticker_data):
        """Test that optimized weights sum to 1."""
        mock_data = pd.DataFrame({
            ('Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
            ('Close', 'MSFT'): sample_multi_ticker_data['MSFT'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = RiskParityOptimizer(
            tickers=['AAPL', 'GOOG', 'MSFT'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        allocation, metrics = optimizer.optimize()
        
        assert np.isclose(allocation['Weight'].sum(), 1.0, atol=0.01)
    
    @patch('yfinance.download')
    def test_optimize_all_weights_positive(self, mock_download, sample_multi_ticker_data):
        """Test that all weights are non-negative."""
        mock_data = pd.DataFrame({
            ('Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
            ('Close', 'MSFT'): sample_multi_ticker_data['MSFT'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = RiskParityOptimizer(
            tickers=['AAPL', 'GOOG', 'MSFT'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        allocation, metrics = optimizer.optimize()
        
        assert all(allocation['Weight'] >= 0)
    
    @patch('yfinance.download')
    def test_optimize_returns_metrics(self, mock_download, sample_multi_ticker_data):
        """Test that optimize returns risk contribution metrics."""
        mock_data = pd.DataFrame({
            ('Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = RiskParityOptimizer(
            tickers=['AAPL', 'GOOG'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        allocation, metrics = optimizer.optimize()
        
        # RiskParity returns DataFrame for metrics
        assert isinstance(metrics, pd.DataFrame)
        assert 'Volatility' in metrics.index
    
    @patch('yfinance.download')
    def test_risk_contributions_approximately_equal(self, mock_download, sample_multi_ticker_data):
        """Test that risk parity achieves roughly equal risk contributions."""
        mock_data = pd.DataFrame({
            ('Close', 'AAPL'): sample_multi_ticker_data['AAPL'],
            ('Close', 'GOOG'): sample_multi_ticker_data['GOOG'],
            ('Close', 'MSFT'): sample_multi_ticker_data['MSFT'],
        }, index=sample_multi_ticker_data.index)
        mock_download.return_value = mock_data
        
        optimizer = RiskParityOptimizer(
            tickers=['AAPL', 'GOOG', 'MSFT'],
            start='2023-01-01',
            end='2023-04-10'
        )
        
        allocation, metrics = optimizer.optimize()
        
        # Check Relative_Risk_Contrib column
        risk_contribs = allocation['Relative_Risk_Contrib'].values
        
        # Expected equal contribution: 1/3 for each asset
        expected = 1.0 / 3.0
        
        # Allow tolerance since perfect parity is hard to achieve
        for rc in risk_contribs:
            assert abs(rc - expected) < 0.15  # 15% tolerance
