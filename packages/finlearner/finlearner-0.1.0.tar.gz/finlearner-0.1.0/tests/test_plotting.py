"""
Unit tests for finlearner.plotting module.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import plotly.graph_objects as go
from finlearner.plotting import Plotter


class TestPlotter:
    """Tests for the Plotter class."""
    
    @patch.object(go.Figure, 'show')
    def test_candlestick_creates_figure(self, mock_show, sample_ohlcv_data):
        """Test that candlestick() creates and shows a figure."""
        Plotter.candlestick(sample_ohlcv_data, title="Test Chart")
        
        # show() should be called once
        assert mock_show.called
    
    @patch('finlearner.plotting.make_subplots')
    def test_candlestick_creates_subplots(self, mock_make_subplots, sample_ohlcv_data):
        """Test that candlestick() creates proper subplot structure."""
        mock_fig = MagicMock()
        mock_make_subplots.return_value = mock_fig
        
        Plotter.candlestick(sample_ohlcv_data, title="Test Chart")
        
        # make_subplots should be called with correct params
        mock_make_subplots.assert_called_once()
        call_kwargs = mock_make_subplots.call_args
        
        # Should have 2 rows (OHLC + Volume)
        assert call_kwargs[1]['rows'] == 2
        assert call_kwargs[1]['cols'] == 1
    
    @patch('finlearner.plotting.make_subplots')
    def test_candlestick_adds_traces(self, mock_make_subplots, sample_ohlcv_data):
        """Test that candlestick() adds both candlestick and volume traces."""
        mock_fig = MagicMock()
        mock_make_subplots.return_value = mock_fig
        
        Plotter.candlestick(sample_ohlcv_data, title="Test Chart")
        
        # add_trace should be called twice (candlestick + volume bar)
        assert mock_fig.add_trace.call_count == 2
    
    @patch('finlearner.plotting.make_subplots')
    def test_candlestick_updates_layout(self, mock_make_subplots, sample_ohlcv_data):
        """Test that candlestick() sets the layout properly."""
        mock_fig = MagicMock()
        mock_make_subplots.return_value = mock_fig
        
        title = "My Custom Title"
        Plotter.candlestick(sample_ohlcv_data, title=title)
        
        # update_layout should be called with title
        mock_fig.update_layout.assert_called_once()
        call_kwargs = mock_fig.update_layout.call_args[1]
        assert call_kwargs['title'] == title
    
    @patch('finlearner.plotting.make_subplots')
    def test_candlestick_with_default_title(self, mock_make_subplots, sample_ohlcv_data):
        """Test that candlestick() uses default title when not provided."""
        mock_fig = MagicMock()
        mock_make_subplots.return_value = mock_fig
        
        Plotter.candlestick(sample_ohlcv_data)
        
        call_kwargs = mock_fig.update_layout.call_args[1]
        assert call_kwargs['title'] == "Stock Price"
    
    def test_candlestick_requires_ohlcv_columns(self):
        """Test that candlestick() requires OHLCV columns."""
        incomplete_data = pd.DataFrame({
            'Close': [100, 101, 102],
            'Volume': [1000, 1100, 1200]
        })
        
        with pytest.raises(KeyError):
            with patch.object(go.Figure, 'show'):
                Plotter.candlestick(incomplete_data)
