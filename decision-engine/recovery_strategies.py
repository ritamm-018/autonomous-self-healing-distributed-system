#!/usr/bin/env python3
"""
Recovery Strategies - Catalog of recovery actions
"""

import httpx
import logging
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class StrategyExecution:
    """Record of strategy execution"""
    timestamp: datetime
    context: Dict
    success: bool
    duration_ms: float
    error: Optional[str] = None


class RecoveryStrategy(ABC):
    """Base class for recovery strategies"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.execution_history: list[StrategyExecution] = []
        
        # Statistics
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_duration_ms = 0
    
    @abstractmethod
    async def execute(self, context: Dict) -> bool:
        """Execute strategy, return success"""
        pass
    
    async def execute_with_tracking(self, context: Dict) -> bool:
        """Execute and track outcome"""
        start_time = datetime.now()
        success = False
        error = None
        
        try:
            success = await self.execute(context)
            self.execution_count += 1
            
            if success:
                self.success_count += 1
            else:
                self.failure_count += 1
        
        except Exception as e:
            logger.error(f"Error executing {self.name}: {e}")
            self.execution_count += 1
            self.failure_count += 1
            error = str(e)
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.total_duration_ms += duration_ms
        
        # Record execution
        execution = StrategyExecution(
            timestamp=start_time,
            context=context,
            success=success,
            duration_ms=duration_ms,
            error=error
        )
        self.execution_history.append(execution)
        
        # Keep only last 100 executions
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
        
        return success
    
    def get_success_rate(self) -> float:
        """Calculate success rate"""
        if self.execution_count == 0:
            return 0.5  # Unknown
        return self.success_count / self.execution_count
    
    def get_avg_duration_ms(self) -> float:
        """Calculate average execution duration"""
        if self.execution_count == 0:
            return 0
        return self.total_duration_ms / self.execution_count
    
    def get_stats(self) -> Dict:
        """Get strategy statistics"""
        return {
            'name': self.name,
            'description': self.description,
            'execution_count': self.execution_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': self.get_success_rate(),
            'avg_duration_ms': self.get_avg_duration_ms()
        }


class RestartPodStrategy(RecoveryStrategy):
    """Restart unhealthy pods"""
    
    def __init__(self, recovery_manager_url: str):
        super().__init__(
            name="restart_pod",
            description="Restart unhealthy pod"
        )
        self.recovery_manager_url = recovery_manager_url
    
    async def execute(self, context: Dict) -> bool:
        service = context.get('service')
        grace_period = context.get('grace_period', 30)
        
        if not service:
            logger.error("No service specified for restart")
            return False
        
        logger.info(f"Restarting {service} (grace period: {grace_period}s)")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.recovery_manager_url}/api/recovery/restart/{service}",
                    json={'grace_period': grace_period}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully restarted {service}")
                    return True
                else:
                    logger.error(f"Failed to restart {service}: {response.status_code}")
                    return False
        
        except Exception as e:
            logger.error(f"Error restarting {service}: {e}")
            return False


class ScaleUpStrategy(RecoveryStrategy):
    """Scale up service replicas"""
    
    def __init__(self, recovery_manager_url: str):
        super().__init__(
            name="scale_up",
            description="Scale up service replicas"
        )
        self.recovery_manager_url = recovery_manager_url
    
    async def execute(self, context: Dict) -> bool:
        service = context.get('service')
        increment = context.get('increment', 2)
        
        if not service:
            logger.error("No service specified for scale up")
            return False
        
        logger.info(f"Scaling up {service} by {increment} replicas")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.recovery_manager_url}/api/recovery/scale/{service}",
                    json={'increment': increment}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully scaled up {service}")
                    return True
                else:
                    logger.error(f"Failed to scale up {service}: {response.status_code}")
                    return False
        
        except Exception as e:
            logger.error(f"Error scaling up {service}: {e}")
            return False


class ScaleDownStrategy(RecoveryStrategy):
    """Scale down service replicas"""
    
    def __init__(self, recovery_manager_url: str):
        super().__init__(
            name="scale_down",
            description="Scale down service replicas"
        )
        self.recovery_manager_url = recovery_manager_url
    
    async def execute(self, context: Dict) -> bool:
        service = context.get('service')
        decrement = context.get('decrement', 1)
        
        if not service:
            logger.error("No service specified for scale down")
            return False
        
        logger.info(f"Scaling down {service} by {decrement} replicas")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.recovery_manager_url}/api/recovery/scale/{service}",
                    json={'increment': -decrement}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully scaled down {service}")
                    return True
                else:
                    logger.error(f"Failed to scale down {service}: {response.status_code}")
                    return False
        
        except Exception as e:
            logger.error(f"Error scaling down {service}: {e}")
            return False


class RollbackStrategy(RecoveryStrategy):
    """Rollback to previous version"""
    
    def __init__(self, recovery_manager_url: str):
        super().__init__(
            name="rollback",
            description="Rollback to previous version"
        )
        self.recovery_manager_url = recovery_manager_url
    
    async def execute(self, context: Dict) -> bool:
        service = context.get('service')
        target = context.get('target', 'previous')
        
        if not service:
            logger.error("No service specified for rollback")
            return False
        
        logger.info(f"Rolling back {service} to {target}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.recovery_manager_url}/api/recovery/rollback/{service}",
                    json={'target': target}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully rolled back {service}")
                    return True
                else:
                    logger.error(f"Failed to rollback {service}: {response.status_code}")
                    return False
        
        except Exception as e:
            logger.error(f"Error rolling back {service}: {e}")
            return False


class CircuitBreakerStrategy(RecoveryStrategy):
    """Enable circuit breaker"""
    
    def __init__(self, recovery_manager_url: str):
        super().__init__(
            name="circuit_breaker",
            description="Enable circuit breaker"
        )
        self.recovery_manager_url = recovery_manager_url
    
    async def execute(self, context: Dict) -> bool:
        service = context.get('service')
        timeout = context.get('timeout', 60)
        enabled = context.get('enabled', True)
        
        if not service:
            logger.error("No service specified for circuit breaker")
            return False
        
        action = "Enabling" if enabled else "Disabling"
        logger.info(f"{action} circuit breaker for {service} (timeout: {timeout}s)")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.recovery_manager_url}/api/recovery/circuit-breaker/{service}",
                    json={'enabled': enabled, 'timeout': timeout}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully updated circuit breaker for {service}")
                    return True
                else:
                    logger.error(f"Failed to update circuit breaker: {response.status_code}")
                    return False
        
        except Exception as e:
            logger.error(f"Error updating circuit breaker: {e}")
            return False


class NotifyStrategy(RecoveryStrategy):
    """Send notification"""
    
    def __init__(self, notification_url: str):
        super().__init__(
            name="notify",
            description="Send notification"
        )
        self.notification_url = notification_url
    
    async def execute(self, context: Dict) -> bool:
        severity = context.get('severity', 'info')
        message = context.get('message', 'Automated recovery action')
        channel = context.get('channel', 'default')
        
        logger.info(f"Sending {severity} notification: {message}")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.notification_url}/api/notifications/send",
                    json={
                        'severity': severity,
                        'message': message,
                        'channel': channel
                    }
                )
                
                return response.status_code == 200
        
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False


class NoActionStrategy(RecoveryStrategy):
    """No action - monitoring only"""
    
    def __init__(self):
        super().__init__(
            name="no_action",
            description="No action required"
        )
    
    async def execute(self, context: Dict) -> bool:
        logger.info("No action required, continuing to monitor")
        return True


class CompositeStrategy(RecoveryStrategy):
    """Execute multiple strategies in sequence"""
    
    def __init__(self, strategies: list[RecoveryStrategy]):
        super().__init__(
            name="composite",
            description="Multiple recovery actions"
        )
        self.strategies = strategies
    
    async def execute(self, context: Dict) -> bool:
        logger.info(f"Executing composite strategy with {len(self.strategies)} actions")
        
        for i, strategy in enumerate(self.strategies):
            logger.info(f"Executing step {i+1}/{len(self.strategies)}: {strategy.name}")
            
            success = await strategy.execute_with_tracking(context)
            
            if not success:
                logger.error(f"Composite strategy failed at step {i+1}: {strategy.name}")
                return False
        
        logger.info("Composite strategy completed successfully")
        return True


class StrategyCatalog:
    """Catalog of all available recovery strategies"""
    
    def __init__(
        self,
        recovery_manager_url: str,
        notification_url: str
    ):
        self.strategies: Dict[str, RecoveryStrategy] = {}
        
        # Register strategies
        self.register(RestartPodStrategy(recovery_manager_url))
        self.register(ScaleUpStrategy(recovery_manager_url))
        self.register(ScaleDownStrategy(recovery_manager_url))
        self.register(RollbackStrategy(recovery_manager_url))
        self.register(CircuitBreakerStrategy(recovery_manager_url))
        self.register(NotifyStrategy(notification_url))
        self.register(NoActionStrategy())
    
    def register(self, strategy: RecoveryStrategy):
        """Register a strategy"""
        self.strategies[strategy.name] = strategy
        logger.info(f"Registered strategy: {strategy.name}")
    
    def get(self, name: str) -> Optional[RecoveryStrategy]:
        """Get strategy by name"""
        return self.strategies.get(name)
    
    def get_all_stats(self) -> Dict:
        """Get statistics for all strategies"""
        return {
            name: strategy.get_stats()
            for name, strategy in self.strategies.items()
        }


# Example usage
if __name__ == '__main__':
    import asyncio
    
    async def test():
        catalog = StrategyCatalog(
            recovery_manager_url="http://recovery-manager:8080",
            notification_url="http://notification-service:8080"
        )
        
        context = {
            'service': 'gateway-service',
            'increment': 2
        }
        
        strategy = catalog.get('scale_up')
        if strategy:
            success = await strategy.execute_with_tracking(context)
            print(f"Success: {success}")
            print(f"Stats: {strategy.get_stats()}")
    
    asyncio.run(test())
