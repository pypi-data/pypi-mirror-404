"""
FinLearner - State-of-the-art Financial Analysis & Deep Learning Library

Provides:
- Deep learning models (LSTM, GRU, Transformer, CNN-LSTM, Ensemble)
- Gradient boosting models (XGBoost, LightGBM)
- Anomaly detection (VAE)
- Risk metrics (VaR, CVaR, Max Drawdown)
- Portfolio optimization (Markowitz, Black-Litterman, Risk Parity)
- Technical analysis indicators
- Options pricing
"""

# Data
from .data import DataLoader

# Technical Analysis
from .technical import TechnicalIndicators

# Deep Learning Models
from .models import (
    TimeSeriesPredictor,
    GRUPredictor,
    CNNLSTMPredictor,
    TransformerPredictor,
    EnsemblePredictor
)

# Machine Learning Models
from .ml_models import GradientBoostPredictor

# Anomaly Detection
from .anomaly import VAEAnomalyDetector

# Risk Metrics
from .risk import (
    RiskMetrics,
    historical_var,
    parametric_var,
    monte_carlo_var,
    cvar,
    max_drawdown
)

# Portfolio Optimization
from .portfolio import (
    PortfolioOptimizer,
    BlackLittermanOptimizer,
    RiskParityOptimizer
)

# Visualization
from .plotting import Plotter

# Utilities
from .utils import check_val

# Version
__version__ = '0.1.1'

__all__ = [
    # Data
    'DataLoader',
    # Technical
    'TechnicalIndicators',
    # DL Models
    'TimeSeriesPredictor',
    'GRUPredictor', 
    'CNNLSTMPredictor',
    'TransformerPredictor',
    'EnsemblePredictor',
    # ML Models
    'GradientBoostPredictor',
    # Anomaly
    'VAEAnomalyDetector',
    # Risk
    'RiskMetrics',
    'historical_var',
    'parametric_var',
    'monte_carlo_var',
    'cvar',
    'max_drawdown',
    # Portfolio
    'PortfolioOptimizer',
    'BlackLittermanOptimizer',
    'RiskParityOptimizer',
    # Visualization
    'Plotter',
    # Utils
    'check_val',
]