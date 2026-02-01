"""
Gradient Boosting Models for Financial Prediction.

This module provides XGBoost and LightGBM wrappers optimized for 
tabular financial data with proper feature engineering.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from typing import Tuple, Optional, Literal


class GradientBoostPredictor:
    """
    Gradient Boosting Predictor using XGBoost or LightGBM.
    
    Optimized for tabular financial data with automatic feature engineering.
    Supports both XGBoost and LightGBM backends.
    
    Example:
        >>> predictor = GradientBoostPredictor(backend='xgboost')
        >>> predictor.fit(df, epochs=100)
        >>> predictions = predictor.predict(df)
    """
    
    def __init__(self, 
                 lookback_days: int = 60, 
                 backend: Literal['xgboost', 'lightgbm'] = 'xgboost',
                 n_estimators: int = 100,
                 max_depth: int = 6,
                 learning_rate: float = 0.1):
        """
        Initialize the Gradient Boosting Predictor.
        
        Args:
            lookback_days: Number of past days to use as features
            backend: 'xgboost' or 'lightgbm'
            n_estimators: Number of boosting rounds
            max_depth: Maximum tree depth
            learning_rate: Learning rate for boosting
        """
        self.lookback_days = lookback_days
        self.backend = backend
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.feature_names = []

    def _create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create engineered features from OHLCV data.
        
        Includes:
        - Lagged returns
        - Moving averages (SMA, EMA)
        - Volatility measures
        - Price momentum
        - Volume features
        """
        features = pd.DataFrame(index=df.index)
        
        # Price features
        features['Close'] = df['Close']
        features['Returns'] = df['Close'].pct_change()
        features['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1))
        
        # Lagged features
        for lag in [1, 2, 3, 5, 10, 20]:
            features[f'Return_Lag_{lag}'] = features['Returns'].shift(lag)
            features[f'Close_Lag_{lag}'] = df['Close'].shift(lag)
        
        # Moving averages
        for window in [5, 10, 20, 50]:
            features[f'SMA_{window}'] = df['Close'].rolling(window=window).mean()
            features[f'EMA_{window}'] = df['Close'].ewm(span=window, adjust=False).mean()
            features[f'SMA_Ratio_{window}'] = df['Close'] / features[f'SMA_{window}']
        
        # Volatility
        features['Volatility_10'] = features['Returns'].rolling(window=10).std()
        features['Volatility_20'] = features['Returns'].rolling(window=20).std()
        
        # Momentum
        features['Momentum_5'] = df['Close'] - df['Close'].shift(5)
        features['Momentum_10'] = df['Close'] - df['Close'].shift(10)
        features['Momentum_20'] = df['Close'] - df['Close'].shift(20)
        
        # High-Low range
        if 'High' in df.columns and 'Low' in df.columns:
            features['High_Low_Ratio'] = df['High'] / df['Low']
            features['Daily_Range'] = (df['High'] - df['Low']) / df['Close']
        
        # Volume features
        if 'Volume' in df.columns:
            features['Volume_Change'] = df['Volume'].pct_change()
            features['Volume_MA_10'] = df['Volume'].rolling(window=10).mean()
            features['Volume_Ratio'] = df['Volume'] / features['Volume_MA_10']
        
        # RSI-like feature
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features['RSI_14'] = 100 - (100 / (1 + rs))
        
        # Drop NaN rows
        features = features.dropna()
        
        return features

    def _prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and target for training."""
        features = self._create_features(df)
        
        # Target: next day's return direction or price
        target = features['Close'].shift(-1)
        
        # Remove last row (no target) and first rows (NaN features)
        features = features.iloc[:-1]
        target = target.iloc[:-1].dropna()
        
        # Align indices
        common_idx = features.index.intersection(target.index)
        features = features.loc[common_idx]
        target = target.loc[common_idx]
        
        # Store feature names
        self.feature_names = [col for col in features.columns if col != 'Close']
        X = features[self.feature_names].values
        y = target.values
        
        return X, y

    def fit(self, df: pd.DataFrame, epochs: int = None, verbose: bool = True):
        """
        Train the gradient boosting model.
        
        Args:
            df: DataFrame with OHLCV data
            epochs: Number of boosting rounds (overrides n_estimators)
            verbose: Whether to print training progress
        """
        X, y = self._prepare_data(df)
        
        n_estimators = epochs if epochs else self.n_estimators
        
        if self.backend == 'xgboost':
            try:
                import xgboost as xgb
                self.model = xgb.XGBRegressor(
                    n_estimators=n_estimators,
                    max_depth=self.max_depth,
                    learning_rate=self.learning_rate,
                    objective='reg:squarederror',
                    verbosity=1 if verbose else 0
                )
                self.model.fit(X, y)
            except ImportError:
                raise ImportError("XGBoost not installed. Run: pip install xgboost")
                
        elif self.backend == 'lightgbm':
            try:
                import lightgbm as lgb
                self.model = lgb.LGBMRegressor(
                    n_estimators=n_estimators,
                    max_depth=self.max_depth,
                    learning_rate=self.learning_rate,
                    verbose=1 if verbose else -1
                )
                self.model.fit(X, y)
            except ImportError:
                raise ImportError("LightGBM not installed. Run: pip install lightgbm")
        
        if verbose:
            print(f"✅ {self.backend.upper()} model trained with {len(self.feature_names)} features")

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Generate predictions using the trained model.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Array of predicted prices
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        features = self._create_features(df)
        X = features[self.feature_names].values
        
        predictions = self.model.predict(X)
        return predictions.reshape(-1, 1)

    def feature_importance(self) -> pd.DataFrame:
        """
        Get feature importance scores.
        
        Returns:
            DataFrame with feature names and importance scores
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        importance = self.model.feature_importances_
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        return importance_df
