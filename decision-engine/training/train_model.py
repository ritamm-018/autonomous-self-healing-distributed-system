#!/usr/bin/env python3
"""
Training script for decision tree model
Generates synthetic training data and trains the model
"""

import numpy as np
import logging
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_decision_models import DecisionTreeModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_training_data(n_samples: int = 1000):
    """Generate synthetic training data"""
    logger.info(f"Generating {n_samples} training samples")
    
    X = []
    y = []
    
    for _ in range(n_samples):
        # Generate features
        anomaly_score = np.random.random()
        error_rate = np.random.random() * 0.3
        p95_latency = np.random.random() * 2000
        cpu_usage = np.random.random()
        memory_usage = np.random.random()
        request_rate = np.random.random() * 10000
        current_replicas = np.random.randint(1, 20)
        restart_count = np.random.randint(0, 5)
        deployment_age = np.random.random() * 120
        service_unhealthy = np.random.choice([0, 1], p=[0.8, 0.2])
        
        features = [
            anomaly_score,
            error_rate,
            p95_latency / 1000,
            cpu_usage,
            memory_usage,
            request_rate / 1000,
            current_replicas,
            restart_count,
            deployment_age / 60,
            service_unhealthy
        ]
        
        # Determine label based on rules
        if anomaly_score > 0.8 and service_unhealthy:
            label = 0  # restart_pod
        elif error_rate > 0.15 and deployment_age < 30:
            label = 2  # rollback
        elif p95_latency > 1000 and error_rate > 0.1:
            label = 3  # circuit_breaker
        elif cpu_usage > 0.8 or request_rate > 5000:
            label = 1  # scale_up
        else:
            label = 4  # no_action
        
        X.append(features)
        y.append(label)
    
    return np.array(X), np.array(y)


def main():
    """Train and save model"""
    # Generate data
    X, y = generate_training_data(n_samples=5000)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    logger.info(f"Training set: {len(X_train)} samples")
    logger.info(f"Test set: {len(X_test)} samples")
    
    # Create and train model
    model = DecisionTreeModel()
    model.train(X_train, y_train)
    
    # Evaluate
    logger.info("Evaluating model...")
    
    y_pred = []
    for features in X_test:
        context = {
            'anomaly_score': features[0],
            'error_rate': features[1],
            'p95_latency': features[2] * 1000,
            'cpu_usage': features[3],
            'memory_usage': features[4],
            'request_rate': features[5] * 1000,
            'current_replicas': int(features[6]),
            'restart_count_last_hour': int(features[7]),
            'deployment_age_minutes': features[8] * 60,
            'service_health': 'unhealthy' if features[9] else 'healthy'
        }
        
        prediction = model.predict(context)
        y_pred.append(model.reverse_map[prediction.strategy])
    
    y_pred = np.array(y_pred)
    
    # Print results
    logger.info("\nClassification Report:")
    print(classification_report(
        y_test,
        y_pred,
        target_names=list(model.strategy_map.values())
    ))
    
    logger.info("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    # Save model
    model_path = os.path.join(
        os.path.dirname(__file__),
        '../models/decision_tree.pkl'
    )
    
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    model.save(model_path)
    
    logger.info(f"\nModel saved to {model_path}")


if __name__ == '__main__':
    main()
