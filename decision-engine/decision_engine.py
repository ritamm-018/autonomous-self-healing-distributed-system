#!/usr/bin/env python3
"""
Autonomous Decision Engine - Main decision-making system
"""

import asyncio
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json

from rule_engine import RuleEngine, Action as RuleAction
from ml_decision_models import (
    DecisionTreeModel,
    QLearningAgent,
    ThompsonSamplingBandit,
    MLPrediction
)
from recovery_strategies import StrategyCatalog, RecoveryStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Decision:
    """Decision made by the engine"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict = field(default_factory=dict)
    strategy: str = ""
    confidence: float = 0.0
    reasoning: str = ""
    rule_matches: List[str] = field(default_factory=list)
    ml_recommendations: List[MLPrediction] = field(default_factory=list)
    executed: bool = False
    success: Optional[bool] = None
    execution_time_ms: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'context': self.context,
            'strategy': self.strategy,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'rule_matches': self.rule_matches,
            'ml_recommendations': [
                {
                    'model': pred.model_name,
                    'strategy': pred.strategy,
                    'confidence': pred.confidence
                }
                for pred in self.ml_recommendations
            ],
            'executed': self.executed,
            'success': self.success,
            'execution_time_ms': self.execution_time_ms
        }


class DecisionLog:
    """Log and track decisions"""
    
    def __init__(self, max_size: int = 1000):
        self.decisions: List[Decision] = []
        self.max_size = max_size
    
    def record(self, decision: Decision):
        """Record a decision"""
        self.decisions.append(decision)
        
        # Keep only recent decisions
        if len(self.decisions) > self.max_size:
            self.decisions = self.decisions[-self.max_size:]
    
    def update_outcome(self, decision_id: str, success: bool, execution_time_ms: float):
        """Update decision outcome"""
        for decision in self.decisions:
            if decision.id == decision_id:
                decision.executed = True
                decision.success = success
                decision.execution_time_ms = execution_time_ms
                break
    
    def get_recent(self, count: int = 10) -> List[Decision]:
        """Get recent decisions"""
        return self.decisions[-count:]
    
    def get_stats(self) -> Dict:
        """Get decision statistics"""
        total = len(self.decisions)
        executed = len([d for d in self.decisions if d.executed])
        successful = len([d for d in self.decisions if d.success])
        
        return {
            'total_decisions': total,
            'executed': executed,
            'successful': successful,
            'success_rate': successful / executed if executed > 0 else 0,
            'avg_confidence': sum(d.confidence for d in self.decisions) / total if total > 0 else 0
        }


class AutonomousDecisionEngine:
    """
    Main decision engine coordinating rules, ML, and strategies
    """
    
    def __init__(
        self,
        rules_file: str,
        recovery_manager_url: str,
        notification_url: str,
        prometheus_url: str,
        anomaly_detector_url: str
    ):
        # Initialize components
        self.rule_engine = RuleEngine(rules_file)
        
        self.ml_models = {
            'decision_tree': DecisionTreeModel(),
            'q_learning': QLearningAgent(),
            'bandit': ThompsonSamplingBandit()
        }
        
        self.strategy_catalog = StrategyCatalog(
            recovery_manager_url=recovery_manager_url,
            notification_url=notification_url
        )
        
        self.decision_log = DecisionLog()
        
        # URLs for context enrichment
        self.prometheus_url = prometheus_url
        self.anomaly_detector_url = anomaly_detector_url
        
        logger.info("Autonomous Decision Engine initialized")
    
    async def enrich_context(self, context: Dict) -> Dict:
        """Enrich context with additional data"""
        enriched = context.copy()
        
        # Add timestamp
        enriched['timestamp'] = datetime.now().isoformat()
        
        # Add time-based features
        now = datetime.now()
        enriched['hour_of_day'] = now.hour
        enriched['day_of_week'] = now.weekday() + 1  # 1-7
        
        # Could fetch additional metrics from Prometheus
        # Could get predictions from anomaly detector
        
        return enriched
    
    def get_ml_recommendations(self, context: Dict) -> List[MLPrediction]:
        """Get recommendations from all ML models"""
        recommendations = []
        
        try:
            # Decision tree
            dt_pred = self.ml_models['decision_tree'].predict(context)
            recommendations.append(dt_pred)
        except Exception as e:
            logger.error(f"Error getting decision tree prediction: {e}")
        
        try:
            # Q-Learning
            ql_pred = self.ml_models['q_learning'].select_action(context)
            recommendations.append(ql_pred)
        except Exception as e:
            logger.error(f"Error getting Q-learning prediction: {e}")
        
        try:
            # Bandit
            bandit_pred = self.ml_models['bandit'].select_strategy()
            recommendations.append(bandit_pred)
        except Exception as e:
            logger.error(f"Error getting bandit prediction: {e}")
        
        return recommendations
    
    def rank_strategies(
        self,
        rule_actions: List[RuleAction],
        ml_recommendations: List[MLPrediction],
        context: Dict
    ) -> List[Dict]:
        """Combine and rank strategies"""
        candidates = {}
        
        # Add rule-based strategies
        for action in rule_actions:
            strategy_name = action.type
            if strategy_name not in candidates:
                candidates[strategy_name] = {
                    'name': strategy_name,
                    'confidence': 0.9,  # High confidence for rule matches
                    'sources': [],
                    'params': action.params
                }
            candidates[strategy_name]['sources'].append('rules')
        
        # Add ML recommendations
        for pred in ml_recommendations:
            strategy_name = pred.strategy
            if strategy_name not in candidates:
                candidates[strategy_name] = {
                    'name': strategy_name,
                    'confidence': pred.confidence,
                    'sources': [],
                    'params': {}
                }
            else:
                # Average confidence if multiple sources
                old_conf = candidates[strategy_name]['confidence']
                candidates[strategy_name]['confidence'] = (old_conf + pred.confidence) / 2
            
            candidates[strategy_name]['sources'].append(pred.model_name)
        
        # Sort by confidence
        ranked = sorted(
            candidates.values(),
            key=lambda x: x['confidence'],
            reverse=True
        )
        
        return ranked
    
    def select_strategy(self, candidates: List[Dict]) -> Dict:
        """Select best strategy from candidates"""
        if not candidates:
            logger.warning("No candidate strategies, defaulting to no_action")
            return {
                'name': 'no_action',
                'confidence': 0.5,
                'sources': ['default'],
                'params': {}
            }
        
        # Select highest confidence
        selected = candidates[0]
        
        logger.info(
            f"Selected strategy: {selected['name']} "
            f"(confidence: {selected['confidence']:.2f}, "
            f"sources: {', '.join(selected['sources'])})"
        )
        
        return selected
    
    def explain_decision(
        self,
        rule_actions: List[RuleAction],
        ml_recommendations: List[MLPrediction],
        selected_strategy: Dict
    ) -> str:
        """Generate explanation for decision"""
        explanation = []
        
        # Rule matches
        if rule_actions:
            rule_strategies = [a.type for a in rule_actions]
            explanation.append(f"Rules matched: {', '.join(set(rule_strategies))}")
        
        # ML recommendations
        if ml_recommendations:
            ml_summary = []
            for pred in ml_recommendations:
                ml_summary.append(f"{pred.model_name}: {pred.strategy} ({pred.confidence:.2f})")
            explanation.append(f"ML models: {'; '.join(ml_summary)}")
        
        # Selected strategy
        explanation.append(
            f"Selected: {selected_strategy['name']} "
            f"(confidence: {selected_strategy['confidence']:.2f})"
        )
        
        return " | ".join(explanation)
    
    async def make_decision(self, context: Dict) -> Decision:
        """
        Make autonomous decision based on context
        """
        logger.info("=" * 60)
        logger.info("Making decision")
        logger.info("=" * 60)
        
        # 1. Enrich context
        enriched_context = await self.enrich_context(context)
        logger.info(f"Context: {json.dumps(enriched_context, indent=2)}")
        
        # 2. Evaluate rules
        rule_actions = self.rule_engine.evaluate(enriched_context)
        logger.info(f"Rule actions: {len(rule_actions)}")
        
        # 3. Get ML recommendations
        ml_recommendations = self.get_ml_recommendations(enriched_context)
        logger.info(f"ML recommendations: {len(ml_recommendations)}")
        
        # 4. Combine and rank strategies
        candidate_strategies = self.rank_strategies(
            rule_actions,
            ml_recommendations,
            enriched_context
        )
        logger.info(f"Candidate strategies: {len(candidate_strategies)}")
        
        # 5. Select best strategy
        selected_strategy = self.select_strategy(candidate_strategies)
        
        # 6. Create decision
        decision = Decision(
            context=enriched_context,
            strategy=selected_strategy['name'],
            confidence=selected_strategy['confidence'],
            reasoning=self.explain_decision(
                rule_actions,
                ml_recommendations,
                selected_strategy
            ),
            rule_matches=[a.type for a in rule_actions],
            ml_recommendations=ml_recommendations
        )
        
        # 7. Log decision
        self.decision_log.record(decision)
        
        logger.info(f"Decision: {decision.strategy} (confidence: {decision.confidence:.2f})")
        logger.info(f"Reasoning: {decision.reasoning}")
        logger.info("=" * 60)
        
        return decision
    
    async def execute_decision(self, decision: Decision) -> bool:
        """Execute decision and track outcome"""
        logger.info(f"Executing decision: {decision.id}")
        
        start_time = datetime.now()
        
        # Get strategy
        strategy = self.strategy_catalog.get(decision.strategy)
        
        if not strategy:
            logger.error(f"Strategy not found: {decision.strategy}")
            self.decision_log.update_outcome(decision.id, False, 0)
            return False
        
        # Execute
        success = await strategy.execute_with_tracking(decision.context)
        
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Update decision log
        self.decision_log.update_outcome(decision.id, success, execution_time_ms)
        
        # Update ML models
        await self.update_ml_models(decision, success)
        
        logger.info(
            f"Decision executed: success={success}, "
            f"time={execution_time_ms:.2f}ms"
        )
        
        return success
    
    async def update_ml_models(self, decision: Decision, success: bool):
        """Update ML models based on outcome"""
        # Calculate reward
        reward = 1.0 if success else -1.0
        
        # Adjust reward based on confidence
        if decision.confidence > 0.8:
            reward *= 1.2  # Bonus for high confidence correct decisions
        
        try:
            # Update Q-Learning
            self.ml_models['q_learning'].update(reward, decision.context)
        except Exception as e:
            logger.error(f"Error updating Q-learning: {e}")
        
        try:
            # Update Bandit
            self.ml_models['bandit'].update(decision.strategy, success)
        except Exception as e:
            logger.error(f"Error updating bandit: {e}")
    
    async def decide_and_execute(self, context: Dict) -> bool:
        """Make decision and execute it"""
        decision = await self.make_decision(context)
        return await self.execute_decision(decision)
    
    def get_stats(self) -> Dict:
        """Get engine statistics"""
        return {
            'decisions': self.decision_log.get_stats(),
            'rules': self.rule_engine.get_rule_stats(),
            'strategies': self.strategy_catalog.get_all_stats(),
            'ml_models': {
                'bandit': self.ml_models['bandit'].get_stats()
            }
        }


# Example usage
if __name__ == '__main__':
    async def test():
        engine = AutonomousDecisionEngine(
            rules_file='rules.yaml',
            recovery_manager_url='http://recovery-manager:8080',
            notification_url='http://notification-service:8080',
            prometheus_url='http://prometheus:9090',
            anomaly_detector_url='http://anomaly-detector:8090'
        )
        
        # Test context
        context = {
            'service': 'gateway-service',
            'anomaly_score': 0.85,
            'error_rate': 0.12,
            'p95_latency': 950,
            'cpu_usage': 0.75,
            'memory_usage': 0.65,
            'request_rate': 3500,
            'current_replicas': 5,
            'restart_count_last_hour': 1,
            'service_health': 'unhealthy'
        }
        
        # Make and execute decision
        success = await engine.decide_and_execute(context)
        
        print(f"\nSuccess: {success}")
        print(f"\nStats: {json.dumps(engine.get_stats(), indent=2)}")
    
    asyncio.run(test())
