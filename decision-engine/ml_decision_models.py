#!/usr/bin/env python3
"""
ML Decision Models - Machine learning models for recovery strategy selection
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import pickle
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MLPrediction:
    """ML model prediction"""
    strategy: str
    confidence: float
    model_name: str
    reasoning: str = ""


class DecisionTreeModel:
    """
    Decision Tree classifier for strategy selection
    Uses Random Forest for robustness
    """
    
    def __init__(self, model_path: str = None):
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
        except ImportError:
            logger.error("scikit-learn not installed")
            raise
        
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        
        self.strategy_map = {
            0: 'restart_pod',
            1: 'scale_up',
            2: 'rollback',
            3: 'circuit_breaker',
            4: 'no_action'
        }
        self.reverse_map = {v: k for k, v in self.strategy_map.items()}
        
        if model_path and os.path.exists(model_path):
            self.load(model_path)
    
    def extract_features(self, context: Dict) -> np.ndarray:
        """Extract features from context"""
        features = [
            context.get('anomaly_score', 0),
            context.get('error_rate', 0),
            context.get('p95_latency', 0) / 1000,  # Normalize to seconds
            context.get('cpu_usage', 0),
            context.get('memory_usage', 0),
            context.get('request_rate', 0) / 1000,  # Normalize
            context.get('current_replicas', 3),
            context.get('restart_count_last_hour', 0),
            context.get('deployment_age_minutes', 0) / 60,  # Normalize to hours
            int(context.get('service_health', 'healthy') == 'unhealthy')
        ]
        
        return np.array(features).reshape(1, -1)
    
    def train(self, X: np.ndarray, y: np.ndarray):
        """Train model on historical data"""
        logger.info(f"Training decision tree on {len(X)} samples")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        # Log feature importance
        feature_names = [
            'anomaly_score', 'error_rate', 'p95_latency',
            'cpu_usage', 'memory_usage', 'request_rate',
            'current_replicas', 'restart_count', 'deployment_age',
            'service_unhealthy'
        ]
        
        importance = self.model.feature_importances_
        for name, imp in zip(feature_names, importance):
            logger.info(f"Feature importance - {name}: {imp:.3f}")
    
    def predict(self, context: Dict) -> MLPrediction:
        """Predict best recovery strategy"""
        if not self.is_trained:
            logger.warning("Model not trained, returning default")
            return MLPrediction(
                strategy='no_action',
                confidence=0.5,
                model_name='decision_tree',
                reasoning='Model not trained'
            )
        
        features = self.extract_features(context)
        features_scaled = self.scaler.transform(features)
        
        # Predict
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]
        confidence = probabilities.max()
        
        strategy = self.strategy_map[prediction]
        
        # Get top 3 strategies for reasoning
        top_indices = np.argsort(probabilities)[-3:][::-1]
        top_strategies = [
            f"{self.strategy_map[i]} ({probabilities[i]:.2f})"
            for i in top_indices
        ]
        
        reasoning = f"Top strategies: {', '.join(top_strategies)}"
        
        return MLPrediction(
            strategy=strategy,
            confidence=confidence,
            model_name='decision_tree',
            reasoning=reasoning
        )
    
    def save(self, filepath: str):
        """Save model to disk"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'is_trained': self.is_trained
            }, f)
        logger.info(f"Model saved to {filepath}")
    
    def load(self, filepath: str):
        """Load model from disk"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self.model = data['model']
        self.scaler = data['scaler']
        self.is_trained = data['is_trained']
        logger.info(f"Model loaded from {filepath}")


class QLearningAgent:
    """
    Q-Learning reinforcement learning agent
    Learns optimal strategies through trial and error
    """
    
    def __init__(self, n_states: int = 1000, n_actions: int = 5):
        self.q_table = np.zeros((n_states, n_actions))
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.epsilon = 0.1  # Exploration rate
        
        self.actions = [
            'restart_pod',
            'scale_up',
            'rollback',
            'circuit_breaker',
            'no_action'
        ]
        
        self.state_history = []
        self.action_history = []
    
    def get_state_index(self, context: Dict) -> int:
        """Convert context to state index using feature hashing"""
        # Discretize continuous features
        anomaly_bucket = min(int(context.get('anomaly_score', 0) * 10), 9)
        error_bucket = min(int(context.get('error_rate', 0) * 10), 9)
        latency_bucket = min(int(context.get('p95_latency', 0) / 100), 9)
        cpu_bucket = min(int(context.get('cpu_usage', 0) * 10), 9)
        
        # Combine into state index
        state = (
            anomaly_bucket * 1000 +
            error_bucket * 100 +
            latency_bucket * 10 +
            cpu_bucket
        )
        
        return min(state, len(self.q_table) - 1)
    
    def select_action(self, context: Dict) -> MLPrediction:
        """Select action using epsilon-greedy policy"""
        state = self.get_state_index(context)
        
        if np.random.random() < self.epsilon:
            # Explore
            action_idx = np.random.randint(len(self.actions))
            confidence = 0.5
            reasoning = "Exploration (random action)"
        else:
            # Exploit
            action_idx = np.argmax(self.q_table[state])
            q_values = self.q_table[state]
            confidence = self._softmax(q_values)[action_idx]
            
            # Get top actions for reasoning
            top_indices = np.argsort(q_values)[-3:][::-1]
            top_actions = [
                f"{self.actions[i]} (Q={q_values[i]:.2f})"
                for i in top_indices
            ]
            reasoning = f"Q-values: {', '.join(top_actions)}"
        
        strategy = self.actions[action_idx]
        
        # Record for learning
        self.state_history.append(state)
        self.action_history.append(action_idx)
        
        return MLPrediction(
            strategy=strategy,
            confidence=confidence,
            model_name='q_learning',
            reasoning=reasoning
        )
    
    def update(self, reward: float, next_context: Dict):
        """Update Q-table based on outcome"""
        if not self.state_history:
            return
        
        state = self.state_history[-1]
        action = self.action_history[-1]
        next_state = self.get_state_index(next_context)
        
        # Q-learning update
        old_value = self.q_table[state, action]
        next_max = np.max(self.q_table[next_state])
        
        new_value = old_value + self.learning_rate * (
            reward + self.discount_factor * next_max - old_value
        )
        
        self.q_table[state, action] = new_value
        
        logger.debug(
            f"Q-update: state={state}, action={self.actions[action]}, "
            f"reward={reward:.2f}, Q={old_value:.2f} -> {new_value:.2f}"
        )
    
    def _softmax(self, values: np.ndarray) -> np.ndarray:
        """Softmax for probability distribution"""
        exp_values = np.exp(values - np.max(values))
        return exp_values / exp_values.sum()
    
    def save(self, filepath: str):
        """Save Q-table"""
        np.save(filepath, self.q_table)
        logger.info(f"Q-table saved to {filepath}")
    
    def load(self, filepath: str):
        """Load Q-table"""
        self.q_table = np.load(filepath)
        logger.info(f"Q-table loaded from {filepath}")


class ThompsonSamplingBandit:
    """
    Thompson Sampling multi-armed bandit
    Balances exploration and exploitation using Bayesian approach
    """
    
    def __init__(self, strategies: List[str] = None):
        if strategies is None:
            strategies = [
                'restart_pod',
                'scale_up',
                'rollback',
                'circuit_breaker',
                'no_action'
            ]
        
        self.strategies = strategies
        
        # Beta distribution parameters (successes, failures)
        self.successes = {s: 1 for s in strategies}  # Prior
        self.failures = {s: 1 for s in strategies}   # Prior
    
    def select_strategy(self) -> MLPrediction:
        """Select strategy using Thompson Sampling"""
        samples = {}
        
        for strategy in self.strategies:
            # Sample from Beta distribution
            alpha = self.successes[strategy]
            beta = self.failures[strategy]
            samples[strategy] = np.random.beta(alpha, beta)
        
        # Select strategy with highest sample
        selected = max(samples, key=samples.get)
        
        # Calculate confidence (win rate)
        confidence = self.get_win_rate(selected)
        
        # Reasoning
        win_rates = {
            s: self.get_win_rate(s)
            for s in self.strategies
        }
        sorted_strategies = sorted(
            win_rates.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        reasoning = "Win rates: " + ", ".join(
            f"{s} ({r:.2f})" for s, r in sorted_strategies
        )
        
        return MLPrediction(
            strategy=selected,
            confidence=confidence,
            model_name='thompson_sampling',
            reasoning=reasoning
        )
    
    def update(self, strategy: str, success: bool):
        """Update based on outcome"""
        if success:
            self.successes[strategy] += 1
        else:
            self.failures[strategy] += 1
        
        logger.debug(
            f"Bandit update: {strategy}, success={success}, "
            f"win_rate={self.get_win_rate(strategy):.3f}"
        )
    
    def get_win_rate(self, strategy: str) -> float:
        """Get estimated win rate"""
        total = self.successes[strategy] + self.failures[strategy]
        return self.successes[strategy] / total
    
    def get_stats(self) -> Dict:
        """Get statistics for all strategies"""
        stats = {}
        for strategy in self.strategies:
            stats[strategy] = {
                'successes': self.successes[strategy],
                'failures': self.failures[strategy],
                'win_rate': self.get_win_rate(strategy),
                'total_trials': self.successes[strategy] + self.failures[strategy]
            }
        return stats
    
    def save(self, filepath: str):
        """Save bandit state"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'successes': self.successes,
                'failures': self.failures
            }, f)
        logger.info(f"Bandit saved to {filepath}")
    
    def load(self, filepath: str):
        """Load bandit state"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self.successes = data['successes']
        self.failures = data['failures']
        logger.info(f"Bandit loaded from {filepath}")


# Example usage
if __name__ == '__main__':
    # Test context
    context = {
        'anomaly_score': 0.75,
        'error_rate': 0.08,
        'p95_latency': 800,
        'cpu_usage': 0.7,
        'memory_usage': 0.6,
        'request_rate': 2000,
        'current_replicas': 5,
        'restart_count_last_hour': 1,
        'deployment_age_minutes': 45,
        'service_health': 'healthy'
    }
    
    # Decision Tree
    dt_model = DecisionTreeModel()
    # Would need training data: dt_model.train(X, y)
    
    # Q-Learning
    ql_agent = QLearningAgent()
    prediction = ql_agent.select_action(context)
    print(f"Q-Learning: {prediction}")
    
    # Thompson Sampling
    bandit = ThompsonSamplingBandit()
    prediction = bandit.select_strategy()
    print(f"Bandit: {prediction}")
