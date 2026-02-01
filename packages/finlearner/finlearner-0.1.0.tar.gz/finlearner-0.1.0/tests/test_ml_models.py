"""
Unit tests for finlearner.ml_models module.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from finlearner.ml_models import GradientBoostPredictor

# Check if xgboost and lightgbm are installed
try:
    import xgboost
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    import lightgbm
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False


class TestGradientBoostPredictor:
    """Tests for the GradientBoostPredictor class."""
    
    def test_init_default_params(self):
        """Test default initialization."""
        predictor = GradientBoostPredictor()
        assert predictor.lookback_days == 60
        assert predictor.backend == 'xgboost'
        assert predictor.n_estimators == 100
        assert predictor.max_depth == 6
        assert predictor.learning_rate == 0.1
        assert predictor.model is None
    
    def test_init_custom_params(self):
        """Test custom initialization."""
        predictor = GradientBoostPredictor(
            lookback_days=30,
            backend='lightgbm',
            n_estimators=200,
            max_depth=8,
            learning_rate=0.05
        )
        assert predictor.lookback_days == 30
        assert predictor.backend == 'lightgbm'
        assert predictor.n_estimators == 200
        assert predictor.max_depth == 8
        assert predictor.learning_rate == 0.05
    
    def test_create_features(self, sample_ohlcv_data):
        """Test feature engineering creates correct columns."""
        predictor = GradientBoostPredictor()
        features = predictor._create_features(sample_ohlcv_data)
        
        # Check that basic features exist
        assert 'Close' in features.columns
        assert 'Returns' in features.columns
        
        # Check lagged features
        assert 'Return_Lag_1' in features.columns
        assert 'Close_Lag_5' in features.columns
        
        # Check moving averages
        assert 'SMA_20' in features.columns
        assert 'EMA_10' in features.columns
        
        # Check volatility
        assert 'Volatility_10' in features.columns
        
        # Check momentum
        assert 'Momentum_5' in features.columns
        
        # Check RSI
        assert 'RSI_14' in features.columns
    
    def test_create_features_with_volume(self, sample_ohlcv_data):
        """Test that volume features are created when Volume column exists."""
        predictor = GradientBoostPredictor()
        features = predictor._create_features(sample_ohlcv_data)
        
        assert 'Volume_Change' in features.columns
        assert 'Volume_MA_10' in features.columns
        assert 'Volume_Ratio' in features.columns
    
    def test_create_features_with_high_low(self, sample_ohlcv_data):
        """Test that High-Low features are created."""
        predictor = GradientBoostPredictor()
        features = predictor._create_features(sample_ohlcv_data)
        
        assert 'High_Low_Ratio' in features.columns
        assert 'Daily_Range' in features.columns
    
    def test_prepare_data(self, sample_ohlcv_data):
        """Test data preparation returns arrays."""
        predictor = GradientBoostPredictor()
        X, y = predictor._prepare_data(sample_ohlcv_data)
        
        assert isinstance(X, np.ndarray)
        assert isinstance(y, np.ndarray)
        assert len(X) == len(y)
    
    @pytest.mark.skipif(not HAS_XGBOOST, reason="xgboost not installed")
    @patch('xgboost.XGBRegressor')
    def test_fit_xgboost(self, mock_xgb, sample_ohlcv_data):
        """Test fitting with XGBoost backend."""
        mock_model = MagicMock()
        mock_xgb.return_value = mock_model
        
        predictor = GradientBoostPredictor(backend='xgboost')
        predictor.fit(sample_ohlcv_data, epochs=10, verbose=False)
        
        assert mock_xgb.called
        assert mock_model.fit.called
    
    @pytest.mark.skipif(not HAS_LIGHTGBM, reason="lightgbm not installed")
    @patch('lightgbm.LGBMRegressor')
    def test_fit_lightgbm(self, mock_lgb, sample_ohlcv_data):
        """Test fitting with LightGBM backend."""
        mock_model = MagicMock()
        mock_lgb.return_value = mock_model
        
        predictor = GradientBoostPredictor(backend='lightgbm')
        predictor.fit(sample_ohlcv_data, epochs=10, verbose=False)
        
        assert mock_lgb.called
        assert mock_model.fit.called
    
    def test_predict_requires_fitted_model(self, sample_ohlcv_data):
        """Test that predict raises error without fitted model."""
        predictor = GradientBoostPredictor()
        
        with pytest.raises(ValueError, match="Model not trained"):
            predictor.predict(sample_ohlcv_data)
    
    @pytest.mark.skipif(not HAS_XGBOOST, reason="xgboost not installed")
    @patch('xgboost.XGBRegressor')
    def test_predict_returns_array(self, mock_xgb, sample_ohlcv_data):
        """Test that predict returns numpy array."""
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([100.0] * 50)
        mock_xgb.return_value = mock_model
        
        predictor = GradientBoostPredictor()
        predictor.fit(sample_ohlcv_data, epochs=10, verbose=False)
        predictions = predictor.predict(sample_ohlcv_data)
        
        assert isinstance(predictions, np.ndarray)
    
    def test_feature_importance_requires_model(self):
        """Test that feature_importance raises error without model."""
        predictor = GradientBoostPredictor()
        
        with pytest.raises(ValueError, match="Model not trained"):
            predictor.feature_importance()
    
    @pytest.mark.skipif(not HAS_XGBOOST, reason="xgboost not installed")
    @patch('xgboost.XGBRegressor')
    def test_feature_importance_returns_dataframe(self, mock_xgb, sample_ohlcv_data):
        """Test that feature_importance returns DataFrame."""
        mock_model = MagicMock()
        # Use 5 features to match the manually set feature_names
        mock_model.feature_importances_ = np.array([0.3, 0.25, 0.2, 0.15, 0.1])
        mock_xgb.return_value = mock_model
        
        predictor = GradientBoostPredictor()
        predictor.fit(sample_ohlcv_data, epochs=10, verbose=False)
        
        # Manually set feature_names to match importances array 
        predictor.feature_names = ['feat_1', 'feat_2', 'feat_3', 'feat_4', 'feat_5']
        
        importance = predictor.feature_importance()
        
        assert isinstance(importance, pd.DataFrame)
        assert 'feature' in importance.columns
        assert 'importance' in importance.columns
        assert len(importance) == 5
