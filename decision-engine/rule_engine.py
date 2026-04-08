#!/usr/bin/env python3
"""
Rule Engine - Evaluates rules and determines recovery actions
"""

import yaml
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Operator(Enum):
    """Comparison operators"""
    GT = ">"
    LT = "<"
    EQ = "=="
    GTE = ">="
    LTE = "<="
    NE = "!="
    IN = "in"
    CONTAINS = "contains"
    MATCHES = "matches"


@dataclass
class Condition:
    """Rule condition"""
    field: str
    operator: Operator
    value: Any
    
    def evaluate(self, context: Dict) -> bool:
        """Evaluate condition against context"""
        actual = self._get_nested_value(context, self.field)
        
        if actual is None:
            logger.debug(f"Field {self.field} not found in context")
            return False
        
        try:
            if self.operator == Operator.GT:
                return actual > self.value
            elif self.operator == Operator.LT:
                return actual < self.value
            elif self.operator == Operator.EQ:
                return actual == self.value
            elif self.operator == Operator.GTE:
                return actual >= self.value
            elif self.operator == Operator.LTE:
                return actual <= self.value
            elif self.operator == Operator.NE:
                return actual != self.value
            elif self.operator == Operator.IN:
                return actual in self.value
            elif self.operator == Operator.CONTAINS:
                return self.value in actual
            elif self.operator == Operator.MATCHES:
                import re
                return bool(re.match(self.value, str(actual)))
            else:
                logger.warning(f"Unknown operator: {self.operator}")
                return False
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get value from nested dict using dot notation"""
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
            
            if value is None:
                return None
        
        return value


@dataclass
class Action:
    """Recovery action"""
    type: str
    params: Dict
    
    def __repr__(self):
        return f"Action(type={self.type}, params={self.params})"


@dataclass
class Rule:
    """Decision rule"""
    id: str
    name: str
    priority: int
    conditions: List[Condition]
    actions: List[Action]
    cooldown: int = 0  # seconds
    exclusive: bool = False
    enabled: bool = True
    
    def evaluate(self, context: Dict) -> bool:
        """Evaluate all conditions (AND logic)"""
        if not self.enabled:
            return False
        
        for condition in self.conditions:
            if not condition.evaluate(context):
                return False
        
        return True


class RuleEngine:
    """
    Rule-based decision engine
    Evaluates rules and determines recovery actions
    """
    
    def __init__(self, rules_file: str = None):
        self.rules: List[Rule] = []
        self.rule_history: Dict[str, datetime] = {}
        
        if rules_file:
            self.load_rules_from_file(rules_file)
    
    def load_rules_from_file(self, filepath: str):
        """Load rules from YAML file"""
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
            
            self.rules = []
            for rule_data in data.get('rules', []):
                rule = self._parse_rule(rule_data)
                self.rules.append(rule)
            
            logger.info(f"Loaded {len(self.rules)} rules from {filepath}")
        
        except Exception as e:
            logger.error(f"Error loading rules: {e}")
            raise
    
    def _parse_rule(self, data: Dict) -> Rule:
        """Parse rule from dict"""
        # Parse conditions
        conditions = []
        for cond_data in data.get('conditions', []):
            condition = Condition(
                field=cond_data['field'],
                operator=Operator(cond_data['operator']),
                value=cond_data['value']
            )
            conditions.append(condition)
        
        # Parse actions
        actions = []
        for action_data in data.get('actions', []):
            action = Action(
                type=action_data['type'],
                params=action_data.get('params', {})
            )
            actions.append(action)
        
        return Rule(
            id=data['id'],
            name=data['name'],
            priority=data.get('priority', 50),
            conditions=conditions,
            actions=actions,
            cooldown=data.get('cooldown', 0),
            exclusive=data.get('exclusive', False),
            enabled=data.get('enabled', True)
        )
    
    def add_rule(self, rule: Rule):
        """Add a rule to the engine"""
        self.rules.append(rule)
        # Sort by priority (highest first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def remove_rule(self, rule_id: str):
        """Remove a rule by ID"""
        self.rules = [r for r in self.rules if r.id != rule_id]
    
    def evaluate(self, context: Dict) -> List[Action]:
        """
        Evaluate all rules against context
        Returns list of actions to execute
        """
        matched_rules = []
        
        logger.info(f"Evaluating {len(self.rules)} rules")
        
        for rule in self.rules:
            # Check cooldown
            if self._is_in_cooldown(rule.id, rule.cooldown):
                logger.debug(f"Rule {rule.id} is in cooldown, skipping")
                continue
            
            # Evaluate conditions
            if rule.evaluate(context):
                logger.info(f"Rule matched: {rule.name} (priority: {rule.priority})")
                matched_rules.append(rule)
                
                # Record execution
                self._record_rule_execution(rule.id)
                
                # Stop at first match if exclusive
                if rule.exclusive:
                    logger.info(f"Rule {rule.id} is exclusive, stopping evaluation")
                    break
        
        # Extract actions
        actions = []
        for rule in matched_rules:
            actions.extend(rule.actions)
        
        logger.info(f"Matched {len(matched_rules)} rules, {len(actions)} actions")
        
        return actions
    
    def _is_in_cooldown(self, rule_id: str, cooldown: int) -> bool:
        """Check if rule is in cooldown period"""
        if cooldown == 0:
            return False
        
        last_execution = self.rule_history.get(rule_id)
        if last_execution is None:
            return False
        
        elapsed = (datetime.now() - last_execution).total_seconds()
        return elapsed < cooldown
    
    def _record_rule_execution(self, rule_id: str):
        """Record rule execution time"""
        self.rule_history[rule_id] = datetime.now()
    
    def get_rule_stats(self) -> Dict:
        """Get statistics about rule executions"""
        stats = {
            'total_rules': len(self.rules),
            'enabled_rules': len([r for r in self.rules if r.enabled]),
            'executions': {}
        }
        
        for rule in self.rules:
            last_exec = self.rule_history.get(rule.id)
            stats['executions'][rule.id] = {
                'name': rule.name,
                'last_execution': last_exec.isoformat() if last_exec else None,
                'enabled': rule.enabled
            }
        
        return stats


# Example usage
if __name__ == '__main__':
    # Create rule engine
    engine = RuleEngine()
    
    # Add a test rule
    rule = Rule(
        id='test-high-anomaly',
        name='High Anomaly Score',
        priority=100,
        conditions=[
            Condition('anomaly_score', Operator.GT, 0.8),
            Condition('service', Operator.EQ, 'gateway-service')
        ],
        actions=[
            Action('restart_pod', {'grace_period': 30}),
            Action('notify', {'severity': 'critical'})
        ],
        cooldown=300
    )
    
    engine.add_rule(rule)
    
    # Test context
    context = {
        'anomaly_score': 0.85,
        'service': 'gateway-service',
        'error_rate': 0.05
    }
    
    # Evaluate
    actions = engine.evaluate(context)
    
    print(f"Actions: {actions}")
