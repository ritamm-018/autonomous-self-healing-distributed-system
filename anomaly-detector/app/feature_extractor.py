import numpy as np
from typing import Dict, List, Optional
from sklearn.preprocessing import StandardScaler
import joblib
from loguru import logger

from app.config import settings


class FeatureExtractor:
    """Extracts and preprocesses features for ML models"""
    
    def __init__(self):
        self.scaler = self._load_or_create_scaler()
        self.feature_names = settings.FEATURE_NAMES
        logger.info("FeatureExtractor initialized")
    
    def _load_or_create_scaler(self) -> StandardScaler:
        """Load existing scaler or create new one"""
        try:
            scaler = joblib.load(settings.SCALER_PATH)
            logger.info(f"Loaded scaler from {settings.SCALER_PATH}")
            return scaler
        except FileNotFoundError:
            logger.info("Creating new scaler")
            return StandardScaler()
    
    def extract_features(self, metrics: Dict) -> Optional[np.ndarray]:
        """
        Extract feature vector from metrics dictionary
        
        Args:
            metrics: Dictionary of raw metrics
            
        Returns:
            Numpy array of features or None if extraction fails
        """
        try:
            features = []
            
            for feature_name in self.feature_names:
                value = metrics.get(feature_name, 0.0)
                features.append(float(value))
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return None
    
    def extract_time_series_features(
        self,
        time_series: List[Dict]
    ) -> Optional[np.ndarray]:
        """
        Extract feature matrix for LSTM from time-series data
        
        Args:
            time_series: List of metric dictionaries ordered by time
            
        Returns:
            3D numpy array (samples, timesteps, features) or None
        """
        try:
            if len(time_series) < settings.LSTM_SEQUENCE_LENGTH:
                logger.warning(
                    f"Insufficient time series data: {len(time_series)} < {settings.LSTM_SEQUENCE_LENGTH}"
                )
                return None
            
            # Extract features for each timestep
            feature_matrix = []
            for metrics in time_series[-settings.LSTM_SEQUENCE_LENGTH:]:
                features = self.extract_features(metrics)
                if features is not None:
                    feature_matrix.append(features.flatten())
            
            if len(feature_matrix) != settings.LSTM_SEQUENCE_LENGTH:
                return None
            
            # Shape: (1, timesteps, features)
            return np.array(feature_matrix).reshape(
                1,
                settings.LSTM_SEQUENCE_LENGTH,
                len(self.feature_names)
            )
            
        except Exception as e:
            logger.error(f"Time series feature extraction failed: {e}")
            return None
    
    def normalize_features(
        self,
        features: np.ndarray,
        fit: bool = False
    ) -> np.ndarray:
        """
        Normalize features using StandardScaler
        
        Args:
            features: Feature array
            fit: Whether to fit the scaler (training mode)
            
        Returns:
            Normalized features
        """
        try:
            if fit:
                return self.scaler.fit_transform(features)
            else:
                return self.scaler.transform(features)
        except Exception as e:
            logger.error(f"Feature normalization failed: {e}")
            return features
    
    def save_scaler(self):
        """Save the fitted scaler to disk"""
        try:
            joblib.dump(self.scaler, settings.SCALER_PATH)
            logger.info(f"Scaler saved to {settings.SCALER_PATH}")
        except Exception as e:
            logger.error(f"Failed to save scaler: {e}")
    
    def calculate_derived_metrics(self, metrics: Dict) -> Dict:
        """
        Calculate additional derived metrics
        
        Args:
            metrics: Raw metrics dictionary
            
        Returns:
            Enhanced metrics with derived values
        """
        enhanced = metrics.copy()
        
        # Error percentage
        if 'error_rate' in metrics and 'request_rate' in metrics:
            total = metrics['request_rate']
            enhanced['error_percentage'] = (
                (metrics['error_rate'] / total * 100) if total > 0 else 0.0
            )
        
        # Memory pressure (usage + growth)
        if 'memory_usage' in metrics and 'memory_growth_rate' in metrics:
            enhanced['memory_pressure'] = (
                metrics['memory_usage'] * 0.7 +
                min(metrics['memory_growth_rate'] * 10, 0.3)
            )
        
        # CPU pressure (usage + spike)
        if 'cpu_usage' in metrics and 'cpu_spike' in metrics:
            enhanced['cpu_pressure'] = (
                metrics['cpu_usage'] * 0.8 +
                min(abs(metrics['cpu_spike']) * 5, 0.2)
            )
        
        # Latency degradation (p99 / p50 ratio)
        if 'latency_p99' in metrics and 'latency_p50' in metrics:
            p50 = metrics['latency_p50']
            enhanced['latency_degradation'] = (
                (metrics['latency_p99'] / p50) if p50 > 0 else 1.0
            )
        
        # GC pressure
        if 'gc_pause_time' in metrics and 'gc_frequency' in metrics:
            enhanced['gc_pressure'] = (
                metrics['gc_pause_time'] * 0.6 +
                metrics['gc_frequency'] * 0.4
            )
        
        return enhanced
    
    def detect_anomaly_indicators(self, metrics: Dict) -> List[str]:
        """
        Detect obvious anomaly indicators in metrics
        
        Args:
            metrics: Metrics dictionary
            
        Returns:
            List of detected anomaly indicators
        """
        indicators = []
        
        # High error rate
        if metrics.get('error_rate', 0) > 0.05:
            indicators.append('high_error_rate')
        
        # Memory leak
        if metrics.get('memory_growth_rate', 0) > 0.1:
            indicators.append('memory_leak')
        
        # CPU spike
        if metrics.get('cpu_spike', 0) > 0.3:
            indicators.append('cpu_spike')
        
        # High latency
        if metrics.get('latency_p99', 0) > 1.0:  # 1 second
            indicators.append('high_latency')
        
        # Memory pressure
        if metrics.get('memory_usage', 0) > 0.9:
            indicators.append('memory_pressure')
        
        # CPU saturation
        if metrics.get('cpu_usage', 0) > 0.9:
            indicators.append('cpu_saturation')
        
        # Excessive GC
        if metrics.get('gc_pause_time', 0) > 0.1:
            indicators.append('excessive_gc')
        
        return indicators
