"""
Unit tests for finlearner.data module.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from finlearner.data import DataLoader


class TestDataLoader:
    """Tests for the DataLoader class."""
    
    def test_download_data_single_ticker(self, sample_ohlcv_data, mock_yfinance_download):
        """Test downloading data for a single ticker."""
        mock_yfinance_download.return_value = sample_ohlcv_data
        
        result = DataLoader.download_data('AAPL', start='2023-01-01', end='2023-04-10')
        
        mock_yfinance_download.assert_called_once_with(
            'AAPL', start='2023-01-01', end='2023-04-10', progress=False
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 100
        assert 'Close' in result.columns
    
    def test_download_data_multiple_tickers(self, sample_ohlcv_data, mock_yfinance_download):
        """Test downloading data for multiple tickers."""
        mock_yfinance_download.return_value = sample_ohlcv_data
        
        tickers = ['AAPL', 'GOOG', 'MSFT']
        result = DataLoader.download_data(tickers, start='2023-01-01', end='2023-04-10')
        
        mock_yfinance_download.assert_called_once_with(
            tickers, start='2023-01-01', end='2023-04-10', progress=False
        )
        assert isinstance(result, pd.DataFrame)
    
    def test_download_data_empty_result_raises_error(self, mock_yfinance_download):
        """Test that empty data raises a ValueError."""
        mock_yfinance_download.return_value = pd.DataFrame()
        
        with pytest.raises(ValueError, match="No data found"):
            DataLoader.download_data('INVALID', start='2023-01-01', end='2023-04-10')
    
    def test_download_data_returns_ohlcv_columns(self, sample_ohlcv_data, mock_yfinance_download):
        """Test that returned data has expected OHLCV columns."""
        mock_yfinance_download.return_value = sample_ohlcv_data
        
        result = DataLoader.download_data('AAPL', start='2023-01-01', end='2023-04-10')
        
        expected_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in expected_columns:
            assert col in result.columns, f"Missing column: {col}"
    
    def test_download_data_index_is_datetime(self, sample_ohlcv_data, mock_yfinance_download):
        """Test that the index is a DatetimeIndex."""
        mock_yfinance_download.return_value = sample_ohlcv_data
        
        result = DataLoader.download_data('AAPL', start='2023-01-01', end='2023-04-10')
        
        assert isinstance(result.index, pd.DatetimeIndex)
