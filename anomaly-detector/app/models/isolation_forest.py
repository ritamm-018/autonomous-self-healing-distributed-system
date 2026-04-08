import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from typing import Optional, Tuple
from loguru import logger
import os

from app.config import settings


class IsolationForestModel:
    """Isolation Forest for unsupervised anomaly detection"""
    
    def __init__(self):
        self.model = None
        self.is_trained = False
        self._load_model()
        logger.info("IsolationForestModel initialized")
    
    def _load_model(self):
        """Load pre-trained model if exists"""
        try:
            if os.path.exists(settings.ISOLATION_FOREST_MODEL_PATH):
                self.model = joblib.load(settings.ISOLATION_FOREST_MODEL_PATH)
                self.is_trained = True
                logger.info(f"Loaded Isolation Forest model from {settings.ISOLATION_FOREST_MODEL_PATH}")
            else:
                logger.info("No pre-trained model found, will need training")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
    
    def train(self, X: np.ndarray) -> bool:
        """
        Train Isolation Forest on normal data
        
        Args:
            X: Training data (normal metrics)
            
        Returns:
            True if training successful
        """
        try:
            logger.info(f"Training Isolation Forest with {X.shape[0]} samples")
            
            self.model = IsolationForest(
                n_estimators=settings.ISOLATION_FOREST_N_ESTIMATORS,
                contamination=settings.ISOLATION_FOREST_CONTAMINATION,
                max_samples='auto',
                random_state=42,
                n_jobs=-1,
                verbose=0
            )
            
            self.model.fit(X)
            self.is_trained = True
            
            # Save model
            self.save_model()
            
            logger.info("Isolation Forest training completed")
            return True
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return False
    
    def predict(self, X: np.ndarray) -> Tuple[float, int]:
        """
        Predict anomaly score for input features
        
        Args:
            X: Feature vector (1, n_features)
            
        Returns:
            Tuple of (anomaly_score, prediction)
            - anomaly_score: 0.0 to 1.0 (higher = more anomalous)
            - prediction: -1 (anomaly) or 1 (normal)
        """
        if not self.is_trained or self.model is None:
            logger.warning("Model not trained, returning default score")
            return 0.0, 1
        
        try:
            # Get anomaly score (lower = more anomalous)
            score = self.model.score_samples(X)[0]
            
            # Get prediction (-1 = anomaly, 1 = normal)
            prediction = self.model.predict(X)[0]
            
            # Convert to 0-1 scale (higher = more anomalous)
            # Normalize using typical score range [-0.5, 0.5]
            anomaly_score = self._normalize_score(score)
            
            return anomaly_score, prediction
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return 0.0, 1
    
    def _normalize_score(self, score: float) -> float:
        """
        Normalize Isolation Forest score to 0-1 range
        
        Isolation Forest scores are typically in range [-0.5, 0.5]
        Lower scores = more anomalous
        
        Args:
            score: Raw Isolation Forest score
            
        Returns:
            Normalized score (0 = normal, 1 = anomaly)
        """
        # Invert and normalize to 0-1
        # Typical range: [-0.5, 0.5] -> [1.0, 0.0]
        normalized = (0.5 - score) / 1.0
        
        # Clip to [0, 1]
        return np.clip(normalized, 0.0, 1.0)
    
    def save_model(self):
        """Save trained model to disk"""
        try:
            os.makedirs(settings.MODEL_DIR, exist_ok=True)
            joblib.dump(self.model, settings.ISOLATION_FOREST_MODEL_PATH)
            logger.info(f"Model saved to {settings.ISOLATION_FOREST_MODEL_PATH}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def get_feature_importance(self) -> Optional[np.ndarray]:
        """
        Get feature importance scores
        
        Note: Isolation Forest doesn't have built-in feature importance,
        but we can estimate it using permutation importance
        
        Returns:
            Array of importance scores or None
        """
        if not self.is_trained:
            return None
        
        # For now, return None
        # Can implement permutation importance if needed
        return None
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> dict:
        """
        Evaluate model performance
        
        Args:
            X: Test features
            y: True labels (1 = normal, -1 = anomaly)
            
        Returns:
            Dictionary of evaluation metrics
        """
        if not self.is_trained:
            return {"error": "Model not trained"}
        
        try:
            predictions = self.model.predict(X)
            
            # Calculate metrics
            accuracy = np.mean(predictions == y)
            
            # True positives (correctly identified anomalies)
            tp = np.sum((predictions == -1) & (y == -1))
            
            # False positives (normal classified as anomaly)
            fp = np.sum((predictions == -1) & (y == 1))
            
            # False negatives (anomaly classified as normal)
            fn = np.sum((predictions == 1) & (y == -1))
            
            # True negatives (correctly identified normal)
            tn = np.sum((predictions == 1) & (y == 1))
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            return {
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1_score),
                "true_positives": int(tp),
                "false_positives": int(fp),
                "false_negatives": int(fn),
                "true_negatives": int(tn)
            }
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {"error": str(e)}
