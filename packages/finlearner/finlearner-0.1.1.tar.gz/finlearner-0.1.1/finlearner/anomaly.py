"""
Anomaly Detection Module for Financial Data.

Provides Variational Autoencoder (VAE) for detecting price anomalies,
unusual trading patterns, and market irregularities.
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from keras import layers
from sklearn.preprocessing import MinMaxScaler
from typing import Tuple, Optional


class Sampling(layers.Layer):
    """Sampling layer for VAE using reparameterization trick."""
    
    def call(self, inputs):
        z_mean, z_log_var = inputs
        batch = tf.shape(z_mean)[0]
        dim = tf.shape(z_mean)[1]
        epsilon = tf.random.normal(shape=(batch, dim))
        return z_mean + tf.exp(0.5 * z_log_var) * epsilon


class VAE(keras.Model):
    """Custom VAE Model for Keras 3.x compatibility."""
    
    def __init__(self, encoder, decoder, **kwargs):
        super().__init__(**kwargs)
        self.encoder = encoder
        self.decoder = decoder
        self.total_loss_tracker = keras.metrics.Mean(name="total_loss")
        self.reconstruction_loss_tracker = keras.metrics.Mean(name="reconstruction_loss")
        self.kl_loss_tracker = keras.metrics.Mean(name="kl_loss")
    
    @property
    def metrics(self):
        return [
            self.total_loss_tracker,
            self.reconstruction_loss_tracker,
            self.kl_loss_tracker,
        ]
    
    def call(self, inputs, training=False):
        z_mean, z_log_var, z = self.encoder(inputs)
        return self.decoder(z)
    
    def train_step(self, data):
        import keras.ops as ops
        
        with tf.GradientTape() as tape:
            z_mean, z_log_var, z = self.encoder(data)
            reconstruction = self.decoder(z)
            
            # Reconstruction loss
            reconstruction_loss = ops.mean(
                ops.sum(ops.square(data - reconstruction), axis=1)
            )
            
            # KL divergence loss
            kl_loss = -0.5 * ops.mean(
                ops.sum(1 + z_log_var - ops.square(z_mean) - ops.exp(z_log_var), axis=1)
            )
            
            total_loss = reconstruction_loss + kl_loss
        
        grads = tape.gradient(total_loss, self.trainable_weights)
        self.optimizer.apply_gradients(zip(grads, self.trainable_weights))
        
        self.total_loss_tracker.update_state(total_loss)
        self.reconstruction_loss_tracker.update_state(reconstruction_loss)
        self.kl_loss_tracker.update_state(kl_loss)
        
        return {
            "loss": self.total_loss_tracker.result(),
            "reconstruction_loss": self.reconstruction_loss_tracker.result(),
            "kl_loss": self.kl_loss_tracker.result(),
        }


class VAEAnomalyDetector:
    """
    Variational Autoencoder for Financial Anomaly Detection.
    
    Uses a VAE to learn the normal distribution of price patterns.
    Anomalies are detected by measuring reconstruction error.
    High reconstruction error = potential anomaly.
    
    Example:
        >>> detector = VAEAnomalyDetector(lookback_days=30)
        >>> detector.fit(df, epochs=50)
        >>> anomaly_scores = detector.detect_anomalies(df)
        >>> anomalies = detector.get_anomalies(df, threshold=0.95)
    """
    
    def __init__(self, 
                 lookback_days: int = 30, 
                 latent_dim: int = 8,
                 hidden_dims: Tuple[int, ...] = (64, 32)):
        """
        Initialize the VAE Anomaly Detector.
        
        Args:
            lookback_days: Number of past days to use for pattern detection
            latent_dim: Dimension of the latent space
            hidden_dims: Tuple of hidden layer dimensions
        """
        self.lookback_days = lookback_days
        self.latent_dim = latent_dim
        self.hidden_dims = hidden_dims
        self.encoder = None
        self.decoder = None
        self.vae = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.reconstruction_threshold = None

    def _build_encoder(self, input_dim: int):
        """Build the encoder network."""
        inputs = keras.Input(shape=(input_dim,))
        x = inputs
        
        for dim in self.hidden_dims:
            x = layers.Dense(dim, activation='relu')(x)
            x = layers.BatchNormalization()(x)
            x = layers.Dropout(0.2)(x)
        
        z_mean = layers.Dense(self.latent_dim, name='z_mean')(x)
        z_log_var = layers.Dense(self.latent_dim, name='z_log_var')(x)
        z = Sampling()([z_mean, z_log_var])
        
        encoder = keras.Model(inputs, [z_mean, z_log_var, z], name='encoder')
        return encoder

    def _build_decoder(self, input_dim: int):
        """Build the decoder network."""
        latent_inputs = keras.Input(shape=(self.latent_dim,))
        x = latent_inputs
        
        for dim in reversed(self.hidden_dims):
            x = layers.Dense(dim, activation='relu')(x)
            x = layers.BatchNormalization()(x)
        
        outputs = layers.Dense(input_dim, activation='sigmoid')(x)
        
        decoder = keras.Model(latent_inputs, outputs, name='decoder')
        return decoder

    def _build_vae(self, input_dim: int):
        """Build the complete VAE model using custom VAE class for Keras 3.x."""
        self.encoder = self._build_encoder(input_dim)
        self.decoder = self._build_decoder(input_dim)
        
        # Use custom VAE class that handles KL loss in train_step
        vae = VAE(self.encoder, self.decoder)
        
        return vae

    def _prepare_data(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare sliding windows of data."""
        close_prices = df['Close'].values.reshape(-1, 1)
        scaled_data = self.scaler.fit_transform(close_prices)
        
        windows = []
        for i in range(len(scaled_data) - self.lookback_days):
            window = scaled_data[i:i + self.lookback_days].flatten()
            windows.append(window)
        
        return np.array(windows)

    def fit(self, df: pd.DataFrame, epochs: int = 50, batch_size: int = 32, 
            validation_split: float = 0.1, verbose: int = 1):
        """
        Train the VAE on normal price patterns.
        
        Args:
            df: DataFrame with 'Close' prices
            epochs: Number of training epochs
            batch_size: Batch size for training
            validation_split: Fraction of data for validation
            verbose: Verbosity level (0, 1, or 2)
        """
        X = self._prepare_data(df)
        input_dim = X.shape[1]
        
        # Build VAE
        self.vae = self._build_vae(input_dim)
        # Custom VAE handles loss in train_step, just provide optimizer
        self.vae.compile(optimizer='adam')
        
        # Train - custom VAE uses data as both input and target in train_step
        history = self.vae.fit(
            X,
            epochs=epochs,
            batch_size=batch_size,
            verbose=verbose
        )
        
        # Calculate reconstruction threshold (95th percentile)
        reconstructions = self.vae(X, training=False)
        if hasattr(reconstructions, 'numpy'):
            reconstructions = reconstructions.numpy()
        reconstruction_errors = np.mean(np.square(X - reconstructions), axis=1)
        self.reconstruction_threshold = np.percentile(reconstruction_errors, 95)
        
        if verbose:
            print(f"✅ VAE trained. Anomaly threshold: {self.reconstruction_threshold:.6f}")
        
        return history

    def detect_anomalies(self, df: pd.DataFrame) -> np.ndarray:
        """
        Calculate anomaly scores for the data.
        
        Higher scores indicate more anomalous patterns.
        
        Args:
            df: DataFrame with 'Close' prices
            
        Returns:
            Array of anomaly scores (reconstruction errors)
        """
        if self.vae is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        X = self._prepare_data(df)
        reconstructions = self.vae(X, training=False)
        if hasattr(reconstructions, 'numpy'):
            reconstructions = reconstructions.numpy()
        anomaly_scores = np.mean(np.square(X - reconstructions), axis=1)
        
        return anomaly_scores

    def get_anomalies(self, df: pd.DataFrame, 
                      threshold: Optional[float] = None,
                      percentile: float = 95) -> pd.DataFrame:
        """
        Identify anomalous data points.
        
        Args:
            df: DataFrame with 'Close' prices
            threshold: Custom threshold for anomaly detection
            percentile: Percentile for automatic threshold (used if threshold is None)
            
        Returns:
            DataFrame with anomaly information
        """
        anomaly_scores = self.detect_anomalies(df)
        
        if threshold is None:
            threshold = self.reconstruction_threshold if self.reconstruction_threshold else \
                        np.percentile(anomaly_scores, percentile)
        
        # Create result DataFrame
        result_index = df.index[self.lookback_days:]
        result = pd.DataFrame({
            'Close': df['Close'].iloc[self.lookback_days:].values,
            'Anomaly_Score': anomaly_scores,
            'Is_Anomaly': anomaly_scores > threshold
        }, index=result_index)
        
        return result

    def get_latent_representation(self, df: pd.DataFrame) -> np.ndarray:
        """
        Get the latent space representation of the data.
        
        Useful for visualization and clustering.
        
        Args:
            df: DataFrame with 'Close' prices
            
        Returns:
            Array of latent space vectors
        """
        if self.encoder is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        X = self._prepare_data(df)
        
        # Keras 3.x compatible: use __call__ and convert outputs
        outputs = self.encoder(X, training=False)
        z_mean = outputs[0]  # First output is z_mean
        
        # Convert to numpy if needed
        if hasattr(z_mean, 'numpy'):
            return z_mean.numpy()
        return np.array(z_mean)

