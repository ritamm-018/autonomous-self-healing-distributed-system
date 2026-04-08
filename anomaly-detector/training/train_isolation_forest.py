import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.isolation_forest import IsolationForestModel
from app.feature_extractor import FeatureExtractor
from app.config import settings
from loguru import logger


def generate_synthetic_data(n_normal=1000, n_anomaly=100):
    """
    Generate synthetic training data
    
    Args:
        n_normal: Number of normal samples
        n_anomaly: Number of anomaly samples
        
    Returns:
        X: Feature matrix
        y: Labels (1 = normal, -1 = anomaly)
    """
    logger.info(f"Generating {n_normal} normal and {n_anomaly} anomaly samples")
    
    # Normal data (typical healthy metrics)
    normal_data = {
        'request_rate': np.random.normal(100, 20, n_normal),
        'request_rate_change': np.random.normal(0, 5, n_normal),
        'latency_p50': np.random.normal(0.05, 0.01, n_normal),
        'latency_p95': np.random.normal(0.15, 0.03, n_normal),
        'latency_p99': np.random.normal(0.25, 0.05, n_normal),
        'error_rate': np.random.uniform(0, 0.01, n_normal),
        'cpu_usage': np.random.normal(0.4, 0.1, n_normal),
        'cpu_spike': np.random.normal(0, 0.05, n_normal),
        'memory_usage': np.random.normal(0.6, 0.1, n_normal),
        'memory_growth_rate': np.random.normal(0, 0.02, n_normal),
        'gc_pause_time': np.random.uniform(0, 0.02, n_normal),
        'gc_frequency': np.random.normal(2, 0.5, n_normal)
    }
    
    # Anomaly data (various failure patterns)
    anomaly_data = {
        'request_rate': np.concatenate([
            np.random.normal(100, 20, n_anomaly // 4),  # Normal rate
            np.random.normal(200, 30, n_anomaly // 4),  # High rate
            np.random.normal(10, 5, n_anomaly // 4),    # Low rate
            np.random.normal(100, 20, n_anomaly // 4)   # Normal rate
        ]),
        'request_rate_change': np.concatenate([
            np.random.normal(50, 10, n_anomaly // 4),   # Sudden spike
            np.random.normal(-30, 10, n_anomaly // 4),  # Sudden drop
            np.random.normal(0, 5, n_anomaly // 2)      # Normal
        ]),
        'latency_p50': np.concatenate([
            np.random.normal(0.5, 0.1, n_anomaly // 2),  # High latency
            np.random.normal(0.05, 0.01, n_anomaly // 2) # Normal
        ]),
        'latency_p95': np.concatenate([
            np.random.normal(2.0, 0.5, n_anomaly // 2),  # Very high
            np.random.normal(0.15, 0.03, n_anomaly // 2) # Normal
        ]),
        'latency_p99': np.concatenate([
            np.random.normal(5.0, 1.0, n_anomaly // 2),  # Extremely high
            np.random.normal(0.25, 0.05, n_anomaly // 2) # Normal
        ]),
        'error_rate': np.concatenate([
            np.random.uniform(0.05, 0.2, n_anomaly // 2),  # High errors
            np.random.uniform(0, 0.01, n_anomaly // 2)     # Normal
        ]),
        'cpu_usage': np.concatenate([
            np.random.normal(0.95, 0.02, n_anomaly // 3),  # CPU saturation
            np.random.normal(0.4, 0.1, 2 * n_anomaly // 3) # Normal
        ]),
        'cpu_spike': np.concatenate([
            np.random.normal(0.5, 0.1, n_anomaly // 3),    # Large spike
            np.random.normal(0, 0.05, 2 * n_anomaly // 3)  # Normal
        ]),
        'memory_usage': np.concatenate([
            np.random.normal(0.95, 0.02, n_anomaly // 3),  # Memory pressure
            np.random.normal(0.6, 0.1, 2 * n_anomaly // 3) # Normal
        ]),
        'memory_growth_rate': np.concatenate([
            np.random.normal(0.2, 0.05, n_anomaly // 3),   # Memory leak
            np.random.normal(0, 0.02, 2 * n_anomaly // 3)  # Normal
        ]),
        'gc_pause_time': np.concatenate([
            np.random.uniform(0.1, 0.5, n_anomaly // 3),   # Excessive GC
            np.random.uniform(0, 0.02, 2 * n_anomaly // 3) # Normal
        ]),
        'gc_frequency': np.concatenate([
            np.random.normal(10, 2, n_anomaly // 3),       # High frequency
            np.random.normal(2, 0.5, 2 * n_anomaly // 3)   # Normal
        ])
    }
    
    # Combine data
    X_normal = np.column_stack([normal_data[feature] for feature in settings.FEATURE_NAMES])
    X_anomaly = np.column_stack([anomaly_data[feature] for feature in settings.FEATURE_NAMES])
    
    X = np.vstack([X_normal, X_anomaly])
    y = np.array([1] * n_normal + [-1] * n_anomaly)
    
    # Shuffle
    indices = np.random.permutation(len(X))
    X = X[indices]
    y = y[indices]
    
    logger.info(f"Generated data shape: {X.shape}")
    return X, y


def train_isolation_forest():
    """Train Isolation Forest model"""
    logger.info("=" * 60)
    logger.info("Training Isolation Forest Model")
    logger.info("=" * 60)
    
    # Generate data
    X, y = generate_synthetic_data(n_normal=2000, n_anomaly=200)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    logger.info(f"Training set: {X_train.shape[0]} samples")
    logger.info(f"Test set: {X_test.shape[0]} samples")
    
    # Initialize feature extractor and normalize
    feature_extractor = FeatureExtractor()
    X_train_normalized = feature_extractor.normalize_features(X_train, fit=True)
    X_test_normalized = feature_extractor.normalize_features(X_test, fit=False)
    
    # Save scaler
    feature_extractor.save_scaler()
    
    # Train model (only on normal data for unsupervised learning)
    X_train_normal = X_train_normalized[y_train == 1]
    logger.info(f"Training on {X_train_normal.shape[0]} normal samples")
    
    model = IsolationForestModel()
    success = model.train(X_train_normal)
    
    if not success:
        logger.error("Training failed!")
        return
    
    # Evaluate
    logger.info("\nEvaluating model...")
    evaluation = model.evaluate(X_test_normalized, y_test)
    
    logger.info("\nEvaluation Results:")
    logger.info(f"  Accuracy: {evaluation['accuracy']:.3f}")
    logger.info(f"  Precision: {evaluation['precision']:.3f}")
    logger.info(f"  Recall: {evaluation['recall']:.3f}")
    logger.info(f"  F1-Score: {evaluation['f1_score']:.3f}")
    logger.info(f"  True Positives: {evaluation['true_positives']}")
    logger.info(f"  False Positives: {evaluation['false_positives']}")
    logger.info(f"  False Negatives: {evaluation['false_negatives']}")
    logger.info(f"  True Negatives: {evaluation['true_negatives']}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Training Complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    # Create models directory
    os.makedirs(settings.MODEL_DIR, exist_ok=True)
    
    # Train
    train_isolation_forest()
