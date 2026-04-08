#!/usr/bin/env python3
"""
Decision Engine Main Application - FastAPI service
"""

import asyncio
import os
import logging
from typing import Dict, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from decision_engine import AutonomousDecisionEngine, Decision
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
decision_counter = Counter(
    'decision_engine_decisions_total',
    'Total decisions made',
    ['strategy', 'success']
)
decision_duration = Histogram(
    'decision_engine_decision_duration_seconds',
    'Decision making duration'
)
execution_duration = Histogram(
    'decision_engine_execution_duration_seconds',
    'Decision execution duration'
)
confidence_gauge = Gauge(
    'decision_engine_confidence',
    'Decision confidence score'
)


# Request/Response models
class DecisionRequest(BaseModel):
    """Request for decision"""
    service: str
    anomaly_score: float = 0.0
    error_rate: float = 0.0
    p95_latency: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    request_rate: float = 0.0
    current_replicas: int = 3
    restart_count_last_hour: int = 0
    service_health: str = "healthy"
    additional_context: Dict = {}


class DecisionResponse(BaseModel):
    """Response with decision"""
    decision_id: str
    strategy: str
    confidence: float
    reasoning: str
    executed: bool = False
    success: bool = None


# Global engine instance
engine: AutonomousDecisionEngine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global engine
    
    # Startup
    logger.info("Starting Decision Engine...")
    
    rules_file = os.getenv('RULES_FILE', 'rules.yaml')
    recovery_manager_url = os.getenv(
        'RECOVERY_MANAGER_URL',
        'http://recovery-manager-service.self-healing-prod:8080'
    )
    notification_url = os.getenv(
        'NOTIFICATION_URL',
        'http://notification-service.self-healing-prod:8080'
    )
    prometheus_url = os.getenv(
        'PROMETHEUS_URL',
        'http://prometheus-kube-prometheus-prometheus.self-healing-monitoring:9090'
    )
    anomaly_detector_url = os.getenv(
        'ANOMALY_DETECTOR_URL',
        'http://anomaly-detector-service.self-healing-prod:8090'
    )
    
    engine = AutonomousDecisionEngine(
        rules_file=rules_file,
        recovery_manager_url=recovery_manager_url,
        notification_url=notification_url,
        prometheus_url=prometheus_url,
        anomaly_detector_url=anomaly_detector_url
    )
    
    logger.info("Decision Engine started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Decision Engine...")


# Create FastAPI app
app = FastAPI(
    title="Autonomous Decision Engine",
    description="Intelligent decision-making system for autonomous recovery",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "decision-engine"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/api/decision/make", response_model=DecisionResponse)
async def make_decision(request: DecisionRequest):
    """Make a decision without executing"""
    try:
        # Build context
        context = {
            'service': request.service,
            'anomaly_score': request.anomaly_score,
            'error_rate': request.error_rate,
            'p95_latency': request.p95_latency,
            'cpu_usage': request.cpu_usage,
            'memory_usage': request.memory_usage,
            'request_rate': request.request_rate,
            'current_replicas': request.current_replicas,
            'restart_count_last_hour': request.restart_count_last_hour,
            'service_health': request.service_health,
            **request.additional_context
        }
        
        # Make decision
        with decision_duration.time():
            decision = await engine.make_decision(context)
        
        # Update metrics
        confidence_gauge.set(decision.confidence)
        
        return DecisionResponse(
            decision_id=decision.id,
            strategy=decision.strategy,
            confidence=decision.confidence,
            reasoning=decision.reasoning
        )
    
    except Exception as e:
        logger.error(f"Error making decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/decision/execute/{decision_id}")
async def execute_decision(decision_id: str):
    """Execute a previously made decision"""
    try:
        # Find decision
        recent_decisions = engine.decision_log.get_recent(100)
        decision = next((d for d in recent_decisions if d.id == decision_id), None)
        
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        
        # Execute
        with execution_duration.time():
            success = await engine.execute_decision(decision)
        
        # Update metrics
        decision_counter.labels(
            strategy=decision.strategy,
            success=str(success)
        ).inc()
        
        return {
            "decision_id": decision_id,
            "success": success,
            "execution_time_ms": decision.execution_time_ms
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/decision/decide-and-execute", response_model=DecisionResponse)
async def decide_and_execute(request: DecisionRequest):
    """Make decision and execute it immediately"""
    try:
        # Build context
        context = {
            'service': request.service,
            'anomaly_score': request.anomaly_score,
            'error_rate': request.error_rate,
            'p95_latency': request.p95_latency,
            'cpu_usage': request.cpu_usage,
            'memory_usage': request.memory_usage,
            'request_rate': request.request_rate,
            'current_replicas': request.current_replicas,
            'restart_count_last_hour': request.restart_count_last_hour,
            'service_health': request.service_health,
            **request.additional_context
        }
        
        # Make and execute decision
        with decision_duration.time():
            decision = await engine.make_decision(context)
        
        with execution_duration.time():
            success = await engine.execute_decision(decision)
        
        # Update metrics
        confidence_gauge.set(decision.confidence)
        decision_counter.labels(
            strategy=decision.strategy,
            success=str(success)
        ).inc()
        
        return DecisionResponse(
            decision_id=decision.id,
            strategy=decision.strategy,
            confidence=decision.confidence,
            reasoning=decision.reasoning,
            executed=True,
            success=success
        )
    
    except Exception as e:
        logger.error(f"Error in decide-and-execute: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/decision/recent")
async def get_recent_decisions(count: int = 10):
    """Get recent decisions"""
    try:
        decisions = engine.decision_log.get_recent(count)
        return [d.to_dict() for d in decisions]
    
    except Exception as e:
        logger.error(f"Error getting recent decisions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """Get engine statistics"""
    try:
        return engine.get_stats()
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rules")
async def get_rules():
    """Get all rules"""
    try:
        return {
            'rules': [
                {
                    'id': rule.id,
                    'name': rule.name,
                    'priority': rule.priority,
                    'enabled': rule.enabled,
                    'cooldown': rule.cooldown
                }
                for rule in engine.rule_engine.rules
            ]
        }
    
    except Exception as e:
        logger.error(f"Error getting rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rules/{rule_id}/enable")
async def enable_rule(rule_id: str):
    """Enable a rule"""
    try:
        for rule in engine.rule_engine.rules:
            if rule.id == rule_id:
                rule.enabled = True
                return {"message": f"Rule {rule_id} enabled"}
        
        raise HTTPException(status_code=404, detail="Rule not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rules/{rule_id}/disable")
async def disable_rule(rule_id: str):
    """Disable a rule"""
    try:
        for rule in engine.rule_engine.rules:
            if rule.id == rule_id:
                rule.enabled = False
                return {"message": f"Rule {rule_id} disabled"}
        
        raise HTTPException(status_code=404, detail="Rule not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies")
async def get_strategies():
    """Get all strategies with stats"""
    try:
        return engine.strategy_catalog.get_all_stats()
    
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8095"))
    uvicorn.run(app, host="0.0.0.0", port=port)
