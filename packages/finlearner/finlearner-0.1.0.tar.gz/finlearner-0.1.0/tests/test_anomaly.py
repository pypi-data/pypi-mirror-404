"""
Unit tests for finlearner.anomaly module.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from finlearner.anomaly import VAEAnomalyDetector, Sampling


class TestSampling:
    """Tests for the Sampling layer."""
    
    def test_sampling_output_shape(self):
        """Test that sampling layer outputs correct shape."""
        import tensorflow as tf
        
        sampling = Sampling()
        z_mean = tf.constant([[0.0, 0.0, 0.0, 0.0]])
        z_log_var = tf.constant([[0.0, 0.0, 0.0, 0.0]])
        
        result = sampling([z_mean, z_log_var])
        
        assert result.shape == (1, 4)


class TestVAEAnomalyDetector:
    """Tests for the VAEAnomalyDetector class."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame with Close prices."""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=200, freq='D')
        prices = 100 * np.cumprod(1 + np.random.normal(0.001, 0.02, 200))
        return pd.DataFrame({'Close': prices}, index=dates)
    
    def test_init_default_params(self):
        """Test default initialization."""
        detector = VAEAnomalyDetector()
        assert detector.lookback_days == 30
        assert detector.latent_dim == 8
        assert detector.hidden_dims == (64, 32)
        assert detector.encoder is None
        assert detector.decoder is None
        assert detector.vae is None
    
    def test_init_custom_params(self):
        """Test custom initialization."""
        detector = VAEAnomalyDetector(
            lookback_days=60,
            latent_dim=16,
            hidden_dims=(128, 64, 32)
        )
        assert detector.lookback_days == 60
        assert detector.latent_dim == 16
        assert detector.hidden_dims == (128, 64, 32)
    
    def test_prepare_data(self, sample_df):
        """Test data preparation creates sliding windows."""
        detector = VAEAnomalyDetector(lookback_days=30)
        X = detector._prepare_data(sample_df)
        
        # Should have (200 - 30) = 170 windows
        assert X.shape[0] == 170
        assert X.shape[1] == 30  # lookback_days
    
    def test_build_encoder(self):
        """Test encoder building."""
        detector = VAEAnomalyDetector(latent_dim=8)
        encoder = detector._build_encoder(input_dim=30)
        
        assert encoder is not None
        # Encoder should have 3 outputs: z_mean, z_log_var, z
        assert len(encoder.outputs) == 3
    
    def test_build_decoder(self):
        """Test decoder building."""
        detector = VAEAnomalyDetector(latent_dim=8)
        decoder = detector._build_decoder(input_dim=30)
        
        assert decoder is not None
        # Decoder input should match latent_dim
        assert decoder.input_shape[1] == 8
    
    def test_build_vae(self):
        """Test complete VAE building."""
        detector = VAEAnomalyDetector(latent_dim=8)
        vae = detector._build_vae(input_dim=30)
        
        assert vae is not None
        assert detector.encoder is not None
        assert detector.decoder is not None
    
    def test_fit_builds_model(self, sample_df):
        """Test that fit builds and trains the VAE."""
        detector = VAEAnomalyDetector(lookback_days=30, latent_dim=4)
        
        # Use small epochs for testing
        history = detector.fit(sample_df, epochs=2, batch_size=16, verbose=0)
        
        assert detector.vae is not None
        assert detector.reconstruction_threshold is not None
        assert hasattr(history, 'history')
    
    def test_detect_anomalies_requires_fitted_model(self, sample_df):
        """Test that detect_anomalies requires fitted model."""
        detector = VAEAnomalyDetector()
        
        with pytest.raises(ValueError, match="Model not trained"):
            detector.detect_anomalies(sample_df)
    
    def test_detect_anomalies_returns_scores(self, sample_df):
        """Test that detect_anomalies returns anomaly scores."""
        detector = VAEAnomalyDetector(lookback_days=30, latent_dim=4)
        detector.fit(sample_df, epochs=2, batch_size=16, verbose=0)
        
        scores = detector.detect_anomalies(sample_df)
        
        assert isinstance(scores, np.ndarray)
        assert len(scores) == 170  # 200 - 30
        assert all(score >= 0 for score in scores)  # Scores should be non-negative
    
    def test_get_anomalies_returns_dataframe(self, sample_df):
        """Test that get_anomalies returns DataFrame with anomaly info."""
        detector = VAEAnomalyDetector(lookback_days=30, latent_dim=4)
        detector.fit(sample_df, epochs=2, batch_size=16, verbose=0)
        
        result = detector.get_anomalies(sample_df)
        
        assert isinstance(result, pd.DataFrame)
        assert 'Close' in result.columns
        assert 'Anomaly_Score' in result.columns
        assert 'Is_Anomaly' in result.columns
    
    def test_get_anomalies_custom_threshold(self, sample_df):
        """Test get_anomalies with custom threshold."""
        detector = VAEAnomalyDetector(lookback_days=30, latent_dim=4)
        detector.fit(sample_df, epochs=2, batch_size=16, verbose=0)
        
        # Very high threshold should result in few/no anomalies
        result = detector.get_anomalies(sample_df, threshold=1e10)
        assert result['Is_Anomaly'].sum() == 0
        
        # Very low threshold should result in many anomalies
        result = detector.get_anomalies(sample_df, threshold=0)
        assert result['Is_Anomaly'].sum() > 0
    
    def test_get_latent_representation_requires_model(self, sample_df):
        """Test that get_latent_representation requires fitted model."""
        detector = VAEAnomalyDetector()
        
        with pytest.raises(ValueError, match="Model not trained"):
            detector.get_latent_representation(sample_df)
    
    def test_get_latent_representation_returns_array(self, sample_df):
        """Test that get_latent_representation returns latent vectors."""
        detector = VAEAnomalyDetector(lookback_days=30, latent_dim=4)
        detector.fit(sample_df, epochs=2, batch_size=16, verbose=0)
        
        latent = detector.get_latent_representation(sample_df)
        
        assert isinstance(latent, np.ndarray)
        assert latent.shape[0] == 170  # 200 - 30
        assert latent.shape[1] == 4  # latent_dim
