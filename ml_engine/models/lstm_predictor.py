"""
LSTM Price Prediction Model
"""
import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
from loguru import logger

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    from sklearn.preprocessing import MinMaxScaler
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logger.warning("TensorFlow not installed. ML features will be limited.")


class LSTMPricePredictor:
    """
    LSTM Model for Price Prediction

    Features:
    - Multi-step ahead prediction
    - Multiple input features (price, volume, indicators)
    - Sequence-to-sequence architecture
    """

    def __init__(
        self,
        sequence_length: int = 60,
        n_features: int = 5,
        lstm_units: int = 50,
        dropout: float = 0.2,
    ):
        """
        Args:
            sequence_length: Length of input sequences (e.g., 60 days)
            n_features: Number of input features
            lstm_units: Number of LSTM units
            dropout: Dropout rate
        """
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.lstm_units = lstm_units
        self.dropout = dropout

        self.model = None
        self.scaler = MinMaxScaler()

        if TF_AVAILABLE:
            self._build_model()

    def _build_model(self):
        """Build LSTM model"""
        model = keras.Sequential([
            layers.LSTM(
                self.lstm_units,
                return_sequences=True,
                input_shape=(self.sequence_length, self.n_features)
            ),
            layers.Dropout(self.dropout),
            layers.LSTM(self.lstm_units, return_sequences=False),
            layers.Dropout(self.dropout),
            layers.Dense(25),
            layers.Dense(1)
        ])

        model.compile(
            optimizer='adam',
            loss='mean_squared_error',
            metrics=['mae']
        )

        self.model = model
        logger.info(f"LSTM model built: {model.count_params()} parameters")

    def prepare_data(
        self,
        df: pd.DataFrame,
        target_column: str = 'close',
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for training

        Args:
            df: DataFrame with price data
            target_column: Column to predict

        Returns:
            X, y arrays
        """
        # Scale data
        scaled_data = self.scaler.fit_transform(df)

        X, y = [], []

        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i - self.sequence_length:i])
            y.append(scaled_data[i, df.columns.get_loc(target_column)])

        return np.array(X), np.array(y)

    def train(
        self,
        df: pd.DataFrame,
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.2,
    ):
        """
        Train the model

        Args:
            df: Training data
            epochs: Number of epochs
            batch_size: Batch size
            validation_split: Validation split ratio
        """
        if not TF_AVAILABLE or self.model is None:
            logger.error("TensorFlow not available or model not built")
            return

        X, y = self.prepare_data(df)

        logger.info(f"Training LSTM model on {len(X)} samples...")

        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=1,
        )

        logger.info("Training completed")
        return history

    def predict(
        self,
        recent_data: pd.DataFrame,
        steps: int = 5,
    ) -> np.ndarray:
        """
        Predict future prices

        Args:
            recent_data: Recent price data (at least sequence_length rows)
            steps: Number of steps to predict

        Returns:
            Predicted prices
        """
        if not TF_AVAILABLE or self.model is None:
            logger.error("TensorFlow not available or model not built")
            return np.array([])

        # Prepare input
        scaled_data = self.scaler.transform(recent_data.tail(self.sequence_length))
        X = scaled_data.reshape(1, self.sequence_length, self.n_features)

        predictions = []

        for _ in range(steps):
            pred = self.model.predict(X, verbose=0)
            predictions.append(pred[0, 0])

            # Update input for next prediction (shift window)
            # This is simplified - in practice would update all features
            X = np.roll(X, -1, axis=1)
            X[0, -1, 0] = pred[0, 0]

        # Inverse transform predictions
        dummy = np.zeros((len(predictions), self.n_features))
        dummy[:, 0] = predictions
        predictions = self.scaler.inverse_transform(dummy)[:, 0]

        return predictions

    def save(self, path: str):
        """Save model"""
        if self.model:
            self.model.save(path)
            logger.info(f"Model saved to {path}")

    def load(self, path: str):
        """Load model"""
        if TF_AVAILABLE:
            self.model = keras.models.load_model(path)
            logger.info(f"Model loaded from {path}")


class XGBoostDirectionClassifier:
    """
    XGBoost for predicting price direction (UP/DOWN/SIDEWAYS)
    """

    def __init__(self):
        try:
            import xgboost as xgb
            self.xgb = xgb
            self.model = None
            logger.info("XGBoost classifier initialized")
        except ImportError:
            logger.warning("XGBoost not installed")
            self.xgb = None

    def train(self, X: np.ndarray, y: np.ndarray):
        """Train classifier"""
        if self.xgb is None:
            return

        self.model = self.xgb.XGBClassifier(
            objective='multi:softmax',
            num_class=3,
            max_depth=5,
            learning_rate=0.1,
            n_estimators=100,
        )

        self.model.fit(X, y)
        logger.info("XGBoost model trained")

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict direction"""
        if self.model is None:
            return np.array([])

        predictions = self.model.predict(X)
        # 0 = DOWN, 1 = SIDEWAYS, 2 = UP
        return predictions


# Global instances
lstm_predictor = LSTMPricePredictor() if TF_AVAILABLE else None
direction_classifier = XGBoostDirectionClassifier()
