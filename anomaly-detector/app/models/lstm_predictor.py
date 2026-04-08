import numpy as np
import os
from typing import Optional, Tuple
from loguru import logger

try:
    from tensorflow import keras
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
    TENSORFLOW_AVAILABLE = True
except ImportError:
    logger.warning("TensorFlow not available, LSTM model will be disabled")
    TENSORFLOW_AVAILABLE = False

from app.config import settings


class LSTMPredictor:
    """LSTM model for time-series anomaly prediction"""
    
    def __init__(self):
        self.model = None
        self.is_trained = False
        if TENSORFLOW_AVAILABLE:
            self._load_model()
        logger.info("LSTMPredictor initialized")
    
    def _load_model(self):
        """Load pre-trained LSTM model if exists"""
        try:
            if os.path.exists(settings.LSTM_MODEL_PATH):
                self.model = load_model(settings.LSTM_MODEL_PATH)
                self.is_trained = True
                logger.info(f"Loaded LSTM model from {settings.LSTM_MODEL_PATH}")
            else:
                logger.info("No pre-trained LSTM model found")
        except Exception as e:
            logger.error(f"Failed to load LSTM model: {e}")
    
    def build_model(self, input_shape: Tuple[int, int]) -> bool:
        """
        Build LSTM model architecture
        
        Args:
            input_shape: (timesteps, features)
            
        Returns:
            True if successful
        """
        if not TENSORFLOW_AVAILABLE:
            logger.error("TensorFlow not available")
            return False
        
        try:
            timesteps, features = input_shape
            
            self.model = Sequential([
                # First LSTM layer with return sequences
                LSTM(
                    64,
                    return_sequences=True,
                    input_shape=(timesteps, features),
                    name='lstm_1'
                ),
                Dropout(0.2, name='dropout_1'),
                
                # Second LSTM layer
                LSTM(32, return_sequences=False, name='lstm_2'),
                Dropout(0.2, name='dropout_2'),
                
                # Dense layers
                Dense(16, activation='relu', name='dense_1'),
                Dense(1, activation='sigmoid', name='output')
            ])
            
            self.model.compile(
                optimizer='adam',
                loss='binary_crossentropy',
                metrics=['accuracy', 'precision', 'recall']
            )
            
            logger.info(f"LSTM model built with input shape: {input_shape}")
            logger.info(f"Total parameters: {self.model.count_params()}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to build model: {e}")
            return False
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        epochs: int = 50,
        batch_size: int = 32
    ) -> bool:
        """
        Train LSTM model
        
        Args:
            X_train: Training sequences (samples, timesteps, features)
            y_train: Training labels (0 = normal, 1 = anomaly)
            X_val: Validation sequences (optional)
            y_val: Validation labels (optional)
            epochs: Number of training epochs
            batch_size: Batch size
            
        Returns:
            True if training successful
        """
        if not TENSORFLOW_AVAILABLE:
            logger.error("TensorFlow not available")
            return False
        
        try:
            logger.info(f"Training LSTM with {X_train.shape[0]} samples")
            
            # Build model if not already built
            if self.model is None:
                input_shape = (X_train.shape[1], X_train.shape[2])
                self.build_model(input_shape)
            
            # Callbacks
            callbacks = [
                EarlyStopping(
                    monitor='val_loss' if X_val is not None else 'loss',
                    patience=10,
                    restore_best_weights=True,
                    verbose=1
                ),
                ModelCheckpoint(
                    settings.LSTM_MODEL_PATH,
                    monitor='val_loss' if X_val is not None else 'loss',
                    save_best_only=True,
                    verbose=1
                )
            ]
            
            # Train
            validation_data = (X_val, y_val) if X_val is not None else None
            
            history = self.model.fit(
                X_train,
                y_train,
                validation_data=validation_data,
                epochs=epochs,
                batch_size=batch_size,
                callbacks=callbacks,
                verbose=1
            )
            
            self.is_trained = True
            logger.info("LSTM training completed")
            
            # Save final model
            self.save_model()
            
            return True
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return False
    
    def predict(self, X: np.ndarray) -> Tuple[float, float]:
        """
        Predict anomaly probability for time-series sequence
        
        Args:
            X: Sequence data (1, timesteps, features)
            
        Returns:
            Tuple of (anomaly_score, confidence)
        """
        if not self.is_trained or self.model is None:
            logger.warning("LSTM model not trained, returning default score")
            return 0.0, 0.0
        
        if not TENSORFLOW_AVAILABLE:
            return 0.0, 0.0
        
        try:
            # Get prediction
            prediction = self.model.predict(X, verbose=0)[0][0]
            
            # Anomaly score (0-1)
            anomaly_score = float(prediction)
            
            # Confidence (distance from 0.5)
            confidence = abs(prediction - 0.5) * 2
            
            return anomaly_score, confidence
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return 0.0, 0.0
    
    def predict_future(
        self,
        X: np.ndarray,
        steps: int = 4
    ) -> Optional[np.ndarray]:
        """
        Predict future metric values
        
        Args:
            X: Current sequence (1, timesteps, features)
            steps: Number of steps to predict ahead
            
        Returns:
            Predicted values or None
        """
        if not self.is_trained or self.model is None:
            return None
        
        if not TENSORFLOW_AVAILABLE:
            return None
        
        try:
            predictions = []
            current_sequence = X.copy()
            
            for _ in range(steps):
                # Predict next value
                next_pred = self.model.predict(current_sequence, verbose=0)[0][0]
                predictions.append(next_pred)
                
                # Update sequence (shift and append)
                # This is simplified - in practice, you'd predict all features
                current_sequence = np.roll(current_sequence, -1, axis=1)
                current_sequence[0, -1, 0] = next_pred
            
            return np.array(predictions)
            
        except Exception as e:
            logger.error(f"Future prediction failed: {e}")
            return None
    
    def save_model(self):
        """Save trained model to disk"""
        if not TENSORFLOW_AVAILABLE or self.model is None:
            return
        
        try:
            os.makedirs(settings.MODEL_DIR, exist_ok=True)
            self.model.save(settings.LSTM_MODEL_PATH)
            logger.info(f"LSTM model saved to {settings.LSTM_MODEL_PATH}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """
        Evaluate model performance
        
        Args:
            X_test: Test sequences
            y_test: True labels
            
        Returns:
            Dictionary of evaluation metrics
        """
        if not self.is_trained or self.model is None:
            return {"error": "Model not trained"}
        
        if not TENSORFLOW_AVAILABLE:
            return {"error": "TensorFlow not available"}
        
        try:
            # Evaluate
            results = self.model.evaluate(X_test, y_test, verbose=0)
            
            # Get metric names
            metric_names = self.model.metrics_names
            
            # Create results dictionary
            evaluation = {
                name: float(value)
                for name, value in zip(metric_names, results)
            }
            
            # Get predictions for additional metrics
            predictions = self.model.predict(X_test, verbose=0)
            pred_classes = (predictions > 0.5).astype(int).flatten()
            
            # Calculate additional metrics
            tp = np.sum((pred_classes == 1) & (y_test == 1))
            fp = np.sum((pred_classes == 1) & (y_test == 0))
            fn = np.sum((pred_classes == 0) & (y_test == 1))
            tn = np.sum((pred_classes == 0) & (y_test == 0))
            
            evaluation.update({
                "true_positives": int(tp),
                "false_positives": int(fp),
                "false_negatives": int(fn),
                "true_negatives": int(tn)
            })
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {"error": str(e)}
    
    def get_model_summary(self) -> Optional[str]:
        """Get model architecture summary"""
        if self.model is None:
            return None
        
        try:
            from io import StringIO
            stream = StringIO()
            self.model.summary(print_fn=lambda x: stream.write(x + '\n'))
            return stream.getvalue()
        except Exception as e:
            logger.error(f"Failed to get summary: {e}")
            return None
