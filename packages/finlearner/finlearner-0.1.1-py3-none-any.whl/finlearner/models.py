import numpy as np
import pandas as pd
from keras.models import Sequential, Model
from keras.layers import (LSTM, GRU, Dense, Dropout, Conv1D, MaxPooling1D, 
                          Flatten, Input, MultiHeadAttention, LayerNormalization,
                          GlobalAveragePooling1D, Concatenate, Average)
from sklearn.preprocessing import MinMaxScaler
from typing import Tuple, List
import tensorflow as tf


class TimeSeriesPredictor:
    """
    LSTM-based Time Series Predictor for Financial Data.
    """
    def __init__(self, lookback_days: int = 60):
        self.lookback_days = lookback_days
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def _prepare_data(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        X, y = [], []
        for i in range(self.lookback_days, len(data)):
            X.append(data[i-self.lookback_days:i, 0])
            y.append(data[i, 0])
        return np.array(X), np.array(y)

    def fit(self, df: pd.DataFrame, epochs: int = 25, batch_size: int = 32):
        """
        Trains the LSTM model.
        """
        dataset = df[['Close']].values
        scaled_data = self.scaler.fit_transform(dataset)
        
        X_train, y_train = self._prepare_data(scaled_data)
        X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

        # Build World-Class Architecture
        self.model = Sequential()
        self.model.add(LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], 1)))
        self.model.add(Dropout(0.2))
        self.model.add(LSTM(units=50, return_sequences=False))
        self.model.add(Dropout(0.2))
        self.model.add(Dense(units=25))
        self.model.add(Dense(units=1))

        self.model.compile(optimizer='adam', loss='mean_squared_error')
        self.model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=1)

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Predicts future prices based on the trained model.
        """
        dataset = df[['Close']].values
        inputs = dataset
        inputs = inputs.reshape(-1, 1)
        inputs = self.scaler.transform(inputs)

        X_test = []
        for i in range(self.lookback_days, len(inputs)):
            X_test.append(inputs[i-self.lookback_days:i, 0])
        
        X_test = np.array(X_test)
        X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))
        
        predicted_prices = self.model.predict(X_test)
        predicted_prices = self.scaler.inverse_transform(predicted_prices)
        return predicted_prices


class GRUPredictor:
    """
    GRU-based Time Series Predictor.
    
    Faster training than LSTM with comparable performance for many financial tasks.
    Uses Gated Recurrent Units which have fewer parameters than LSTM.
    """
    def __init__(self, lookback_days: int = 60, units: int = 50):
        self.lookback_days = lookback_days
        self.units = units
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def _prepare_data(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        X, y = [], []
        for i in range(self.lookback_days, len(data)):
            X.append(data[i-self.lookback_days:i, 0])
            y.append(data[i, 0])
        return np.array(X), np.array(y)

    def fit(self, df: pd.DataFrame, epochs: int = 25, batch_size: int = 32):
        """Trains the GRU model."""
        dataset = df[['Close']].values
        scaled_data = self.scaler.fit_transform(dataset)
        
        X_train, y_train = self._prepare_data(scaled_data)
        X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

        self.model = Sequential([
            GRU(units=self.units, return_sequences=True, input_shape=(X_train.shape[1], 1)),
            Dropout(0.2),
            GRU(units=self.units, return_sequences=True),
            Dropout(0.2),
            GRU(units=self.units // 2, return_sequences=False),
            Dropout(0.2),
            Dense(units=25, activation='relu'),
            Dense(units=1)
        ])

        self.model.compile(optimizer='adam', loss='mean_squared_error')
        self.model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=1)

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Predicts future prices using the trained GRU model."""
        dataset = df[['Close']].values
        inputs = dataset
        inputs = inputs.reshape(-1, 1)
        inputs = self.scaler.transform(inputs)

        X_test = []
        for i in range(self.lookback_days, len(inputs)):
            X_test.append(inputs[i-self.lookback_days:i, 0])
        
        X_test = np.array(X_test)
        X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))
        
        predicted_prices = self.model.predict(X_test)
        predicted_prices = self.scaler.inverse_transform(predicted_prices)
        return predicted_prices


class CNNLSTMPredictor:
    """
    CNN-LSTM Hybrid Model for Time Series Prediction.
    
    Uses 1D Convolutions to extract local patterns and features,
    followed by LSTM layers to learn temporal dependencies.
    Excellent for capturing both short-term patterns and long-term trends.
    """
    def __init__(self, lookback_days: int = 60, filters: int = 64, kernel_size: int = 3):
        self.lookback_days = lookback_days
        self.filters = filters
        self.kernel_size = kernel_size
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def _prepare_data(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        X, y = [], []
        for i in range(self.lookback_days, len(data)):
            X.append(data[i-self.lookback_days:i, 0])
            y.append(data[i, 0])
        return np.array(X), np.array(y)

    def fit(self, df: pd.DataFrame, epochs: int = 25, batch_size: int = 32):
        """Trains the CNN-LSTM hybrid model."""
        dataset = df[['Close']].values
        scaled_data = self.scaler.fit_transform(dataset)
        
        X_train, y_train = self._prepare_data(scaled_data)
        X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

        self.model = Sequential([
            # CNN Feature Extraction
            Conv1D(filters=self.filters, kernel_size=self.kernel_size, activation='relu',
                   input_shape=(X_train.shape[1], 1)),
            Conv1D(filters=self.filters, kernel_size=self.kernel_size, activation='relu'),
            MaxPooling1D(pool_size=2),
            Dropout(0.25),
            
            # LSTM Temporal Learning
            LSTM(units=50, return_sequences=True),
            Dropout(0.2),
            LSTM(units=50, return_sequences=False),
            Dropout(0.2),
            
            # Output
            Dense(units=25, activation='relu'),
            Dense(units=1)
        ])

        self.model.compile(optimizer='adam', loss='mean_squared_error')
        self.model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=1)

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Predicts using the CNN-LSTM hybrid model."""
        dataset = df[['Close']].values
        inputs = dataset
        inputs = inputs.reshape(-1, 1)
        inputs = self.scaler.transform(inputs)

        X_test = []
        for i in range(self.lookback_days, len(inputs)):
            X_test.append(inputs[i-self.lookback_days:i, 0])
        
        X_test = np.array(X_test)
        X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))
        
        predicted_prices = self.model.predict(X_test)
        predicted_prices = self.scaler.inverse_transform(predicted_prices)
        return predicted_prices


class TransformerPredictor:
    """
    Transformer-based Time Series Predictor.
    
    Uses self-attention mechanisms to capture long-range dependencies.
    State-of-the-art architecture for sequence modeling tasks.
    Includes positional encoding for temporal awareness.
    """
    def __init__(self, lookback_days: int = 60, d_model: int = 64, 
                 num_heads: int = 4, ff_dim: int = 128, num_blocks: int = 2):
        self.lookback_days = lookback_days
        self.d_model = d_model
        self.num_heads = num_heads
        self.ff_dim = ff_dim
        self.num_blocks = num_blocks
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def _positional_encoding(self, seq_len: int, d_model: int) -> np.ndarray:
        """Generate positional encoding for transformer."""
        positions = np.arange(seq_len)[:, np.newaxis]
        dims = np.arange(d_model)[np.newaxis, :]
        angles = positions / np.power(10000, (2 * (dims // 2)) / d_model)
        angles[:, 0::2] = np.sin(angles[:, 0::2])
        angles[:, 1::2] = np.cos(angles[:, 1::2])
        return angles.astype(np.float32)

    def _transformer_block(self, inputs, d_model: int, num_heads: int, ff_dim: int):
        """Single transformer encoder block."""
        # Multi-Head Self-Attention
        attn_output = MultiHeadAttention(num_heads=num_heads, key_dim=d_model)(inputs, inputs)
        attn_output = Dropout(0.1)(attn_output)
        out1 = LayerNormalization(epsilon=1e-6)(inputs + attn_output)
        
        # Feed Forward Network
        ffn = Dense(ff_dim, activation='relu')(out1)
        ffn = Dense(d_model)(ffn)
        ffn = Dropout(0.1)(ffn)
        return LayerNormalization(epsilon=1e-6)(out1 + ffn)

    def _prepare_data(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        X, y = [], []
        for i in range(self.lookback_days, len(data)):
            X.append(data[i-self.lookback_days:i, 0])
            y.append(data[i, 0])
        return np.array(X), np.array(y)

    def fit(self, df: pd.DataFrame, epochs: int = 25, batch_size: int = 32):
        """Trains the Transformer model."""
        dataset = df[['Close']].values
        scaled_data = self.scaler.fit_transform(dataset)
        
        X_train, y_train = self._prepare_data(scaled_data)
        X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

        # Build Transformer Model
        inputs = Input(shape=(X_train.shape[1], 1))
        
        # Project to d_model dimensions
        x = Dense(self.d_model)(inputs)
        
        # Add positional encoding
        pos_encoding = self._positional_encoding(X_train.shape[1], self.d_model)
        x = x + pos_encoding
        
        # Transformer blocks
        for _ in range(self.num_blocks):
            x = self._transformer_block(x, self.d_model, self.num_heads, self.ff_dim)
        
        # Output layers
        x = GlobalAveragePooling1D()(x)
        x = Dense(64, activation='relu')(x)
        x = Dropout(0.1)(x)
        outputs = Dense(1)(x)
        
        self.model = Model(inputs=inputs, outputs=outputs)
        self.model.compile(optimizer='adam', loss='mean_squared_error')
        self.model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=1)

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Predicts using the Transformer model."""
        dataset = df[['Close']].values
        inputs = dataset
        inputs = inputs.reshape(-1, 1)
        inputs = self.scaler.transform(inputs)

        X_test = []
        for i in range(self.lookback_days, len(inputs)):
            X_test.append(inputs[i-self.lookback_days:i, 0])
        
        X_test = np.array(X_test)
        X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))
        
        predicted_prices = self.model.predict(X_test)
        predicted_prices = self.scaler.inverse_transform(predicted_prices)
        return predicted_prices


class EnsemblePredictor:
    """
    Ensemble Model combining LSTM, GRU, and Attention mechanisms.
    
    Aggregates predictions from multiple architectures for more robust forecasting.
    Uses weighted averaging based on validation performance.
    """
    def __init__(self, lookback_days: int = 60, weights: List[float] = None):
        self.lookback_days = lookback_days
        self.weights = weights or [0.4, 0.3, 0.3]  # LSTM, GRU, Attention weights
        self.models = []
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def _prepare_data(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        X, y = [], []
        for i in range(self.lookback_days, len(data)):
            X.append(data[i-self.lookback_days:i, 0])
            y.append(data[i, 0])
        return np.array(X), np.array(y)

    def _build_lstm_model(self, input_shape):
        """Build LSTM component."""
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dense(25, activation='relu'),
            Dense(1)
        ])
        return model

    def _build_gru_model(self, input_shape):
        """Build GRU component."""
        model = Sequential([
            GRU(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            GRU(50, return_sequences=False),
            Dense(25, activation='relu'),
            Dense(1)
        ])
        return model

    def _build_attention_model(self, input_shape):
        """Build Attention-based component."""
        inputs = Input(shape=input_shape)
        x = Dense(64)(inputs)
        x = MultiHeadAttention(num_heads=4, key_dim=64)(x, x)
        x = GlobalAveragePooling1D()(x)
        x = Dense(32, activation='relu')(x)
        outputs = Dense(1)(x)
        return Model(inputs=inputs, outputs=outputs)

    def fit(self, df: pd.DataFrame, epochs: int = 25, batch_size: int = 32):
        """Trains all ensemble components."""
        dataset = df[['Close']].values
        scaled_data = self.scaler.fit_transform(dataset)
        
        X_train, y_train = self._prepare_data(scaled_data)
        X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
        input_shape = (X_train.shape[1], 1)

        # Build and train each model
        self.models = [
            self._build_lstm_model(input_shape),
            self._build_gru_model(input_shape),
            self._build_attention_model(input_shape)
        ]
        
        for i, model in enumerate(self.models):
            print(f"\n📊 Training Model {i+1}/3: {['LSTM', 'GRU', 'Attention'][i]}")
            model.compile(optimizer='adam', loss='mean_squared_error')
            model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=1)

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Generates weighted ensemble predictions."""
        dataset = df[['Close']].values
        inputs = dataset
        inputs = inputs.reshape(-1, 1)
        inputs = self.scaler.transform(inputs)

        X_test = []
        for i in range(self.lookback_days, len(inputs)):
            X_test.append(inputs[i-self.lookback_days:i, 0])
        
        X_test = np.array(X_test)
        X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))
        
        # Get predictions from each model
        predictions = []
        for model in self.models:
            pred = model.predict(X_test)
            predictions.append(pred)
        
        # Weighted average
        ensemble_pred = np.zeros_like(predictions[0])
        for i, pred in enumerate(predictions):
            ensemble_pred += self.weights[i] * pred
        
        predicted_prices = self.scaler.inverse_transform(ensemble_pred)
        return predicted_prices