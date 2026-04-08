import numpy as np
from typing import Dict, Tuple, Optional, List
from loguru import logger

from app.models.isolation_forest import IsolationForestModel
from app.models.lstm_predictor import LSTMPredictor
from app.config import settings


class EnsembleModel:
    """Ensemble model combining Isolation Forest and LSTM predictions"""
    
    def __init__(self):
        self.isolation_forest = IsolationForestModel()
        self.lstm = LSTMPredictor()
        
        # Weights for ensemble
        self.if_weight = 0.4  # Isolation Forest weight
        self.lstm_weight = 0.6  # LSTM weight
        
        logger.info("EnsembleModel initialized")
    
    def predict(
        self,
        features: np.ndarray,
        time_series: Optional[np.ndarray] = None,
        metrics: Optional[Dict] = None
    ) -> Dict:
        """
        Predict anomaly score using ensemble of models
        
        Args:
            features: Feature vector for Isolation Forest (1, n_features)
            time_series: Time-series data for LSTM (1, timesteps, features)
            metrics: Raw metrics dictionary for additional analysis
            
        Returns:
            Dictionary with prediction results
        """
        try:
            # Get Isolation Forest prediction
            if_score, if_prediction = self.isolation_forest.predict(features)
            
            # Get LSTM prediction if time series available
            lstm_score = 0.0
            lstm_confidence = 0.0
            
            if time_series is not None and self.lstm.is_trained:
                lstm_score, lstm_confidence = self.lstm.predict(time_series)
            
            # Calculate ensemble score
            if time_series is not None and self.lstm.is_trained:
                # Both models available
                base_score = (
                    self.if_weight * if_score +
                    self.lstm_weight * lstm_score
                )
            else:
                # Only Isolation Forest available
                base_score = if_score
            
            # Apply severity multipliers based on metrics
            severity_multiplier = 1.0
            anomaly_indicators = []
            
            if metrics:
                severity_multiplier, anomaly_indicators = self._calculate_severity(metrics)
            
            # Final score
            final_score = min(base_score * severity_multiplier, 1.0)
            
            # Determine anomaly type
            anomaly_type = self._determine_anomaly_type(metrics) if metrics else "unknown"
            
            # Determine status
            status = self._determine_status(final_score)
            
            # Estimate crash time
            predicted_crash_time = self._estimate_crash_time(
                final_score,
                lstm_score,
                metrics
            )
            
            # Generate recommendation
            recommendation = self._generate_recommendation(
                final_score,
                anomaly_type,
                anomaly_indicators
            )
            
            return {
                "anomaly_score": round(final_score, 3),
                "status": status,
                "anomaly_type": anomaly_type,
                "confidence": round(lstm_confidence, 3) if time_series is not None else 0.5,
                "predicted_crash_time_minutes": predicted_crash_time,
                "recommendation": recommendation,
                "model_scores": {
                    "isolation_forest": round(if_score, 3),
                    "lstm": round(lstm_score, 3) if time_series is not None else None
                },
                "anomaly_indicators": anomaly_indicators,
                "severity_multiplier": round(severity_multiplier, 2)
            }
            
        except Exception as e:
            logger.error(f"Ensemble prediction failed: {e}")
            return {
                "anomaly_score": 0.0,
                "status": "error",
                "error": str(e)
            }
    
    def _calculate_severity(self, metrics: Dict) -> Tuple[float, List[str]]:
        """
        Calculate severity multiplier based on metrics
        
        Args:
            metrics: Raw metrics dictionary
            
        Returns:
            Tuple of (multiplier, list of indicators)
        """
        multiplier = 1.0
        indicators = []
        
        # High error rate
        if metrics.get('error_rate', 0) > 0.05:
            multiplier += 0.2
            indicators.append('high_error_rate')
        
        # Memory leak
        if metrics.get('memory_growth_rate', 0) > 0.1:
            multiplier += 0.2
            indicators.append('memory_leak')
        
        # CPU saturation
        if metrics.get('cpu_usage', 0) > 0.9:
            multiplier += 0.1
            indicators.append('cpu_saturation')
        
        # Memory pressure
        if metrics.get('memory_usage', 0) > 0.9:
            multiplier += 0.15
            indicators.append('memory_pressure')
        
        # High latency
        if metrics.get('latency_p99', 0) > 1.0:
            multiplier += 0.1
            indicators.append('high_latency')
        
        # Excessive GC
        if metrics.get('gc_pause_time', 0) > 0.1:
            multiplier += 0.1
            indicators.append('excessive_gc')
        
        return multiplier, indicators
    
    def _determine_anomaly_type(self, metrics: Dict) -> str:
        """Determine primary anomaly type"""
        if not metrics:
            return "unknown"
        
        # Check each type in order of severity
        if metrics.get('error_rate', 0) > 0.05:
            return "errors"
        
        if metrics.get('memory_growth_rate', 0) > 0.1:
            return "memory_leak"
        
        if metrics.get('memory_usage', 0) > 0.9:
            return "memory_pressure"
        
        if metrics.get('cpu_usage', 0) > 0.9:
            return "cpu_saturation"
        
        if metrics.get('latency_p99', 0) > 1.0:
            return "latency"
        
        if metrics.get('gc_pause_time', 0) > 0.1:
            return "gc_pressure"
        
        return "combined"
    
    def _determine_status(self, score: float) -> str:
        """Determine status based on score"""
        if score >= settings.THRESHOLD_EMERGENCY:
            return "emergency"
        elif score >= settings.THRESHOLD_CRITICAL:
            return "critical"
        elif score >= settings.THRESHOLD_WARNING:
            return "warning"
        else:
            return "normal"
    
    def _estimate_crash_time(
        self,
        score: float,
        lstm_score: float,
        metrics: Optional[Dict]
    ) -> Optional[int]:
        """
        Estimate time until crash in minutes
        
        Args:
            score: Final anomaly score
            lstm_score: LSTM prediction score
            metrics: Raw metrics
            
        Returns:
            Estimated minutes until crash or None
        """
        if score < settings.THRESHOLD_WARNING:
            return None
        
        # Base estimation on score
        if score >= 0.9:
            base_time = 5  # 5 minutes
        elif score >= 0.8:
            base_time = 10
        elif score >= 0.6:
            base_time = 30
        else:
            base_time = 60
        
        # Adjust based on growth rates
        if metrics:
            memory_growth = metrics.get('memory_growth_rate', 0)
            if memory_growth > 0.2:
                base_time = int(base_time * 0.5)  # Faster crash
            elif memory_growth > 0.1:
                base_time = int(base_time * 0.7)
        
        return max(base_time, 1)  # At least 1 minute
    
    def _generate_recommendation(
        self,
        score: float,
        anomaly_type: str,
        indicators: List[str]
    ) -> str:
        """Generate action recommendation"""
        if score < settings.THRESHOLD_WARNING:
            return "Continue normal operation"
        
        if score >= settings.THRESHOLD_EMERGENCY:
            # Emergency actions
            if anomaly_type == "memory_leak" or "memory_pressure" in indicators:
                return "EMERGENCY: Increase memory limit and restart pod immediately"
            elif anomaly_type == "cpu_saturation":
                return "EMERGENCY: Scale replicas immediately"
            elif anomaly_type == "errors":
                return "EMERGENCY: Restart pod to recover from errors"
            else:
                return "EMERGENCY: Trigger immediate recovery action"
        
        elif score >= settings.THRESHOLD_CRITICAL:
            # Critical warnings
            if anomaly_type == "memory_leak":
                return "CRITICAL: Memory leak detected, prepare for restart"
            elif anomaly_type == "latency":
                return "CRITICAL: High latency, consider scaling or circuit breaker"
            elif anomaly_type == "cpu_saturation":
                return "CRITICAL: CPU saturation, scale replicas"
            else:
                return "CRITICAL: Monitor closely, prepare recovery resources"
        
        else:
            # Warnings
            return f"WARNING: {anomaly_type} detected, monitor closely"
    
    def train_isolation_forest(self, X: np.ndarray) -> bool:
        """Train Isolation Forest model"""
        return self.isolation_forest.train(X)
    
    def train_lstm(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        epochs: int = 50
    ) -> bool:
        """Train LSTM model"""
        return self.lstm.train(X_train, y_train, X_val, y_val, epochs)
    
    def is_ready(self) -> bool:
        """Check if ensemble is ready for predictions"""
        return self.isolation_forest.is_trained
    
    def get_model_status(self) -> Dict:
        """Get status of all models"""
        return {
            "isolation_forest_trained": self.isolation_forest.is_trained,
            "lstm_trained": self.lstm.is_trained,
            "ensemble_ready": self.is_ready()
        }
