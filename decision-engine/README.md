# Autonomous Decision Engine

## Overview

Intelligent decision-making system that autonomously determines the best recovery actions based on system state, historical data, and ML predictions. Combines rule-based logic with ML-assisted decision making for optimal recovery strategies.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  AUTONOMOUS DECISION ENGINE                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input → Context Enrichment → Rule Engine → ML Models       │
│       → Strategy Selector → Decision Executor → Feedback    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Rule Engine (`rule_engine.py`)

**Priority-based rule evaluation** with cooldown periods:

- **14 predefined rules** covering:
  - High anomaly scores
  - Memory leaks
  - High latency
  - Service failures
  - Error spikes
  - CPU/traffic scaling
  - Business hours scheduling
  - Recovery cleanup

- **Operators**: `>`, `<`, `==`, `>=`, `<=`, `!=`, `in`, `contains`, `matches`
- **Cooldown**: Prevents rule re-execution for specified duration
- **Exclusive rules**: Stop evaluation after first match

### 2. ML Decision Models (`ml_decision_models.py`)

**Three ML models** for strategy selection:

**Random Forest Classifier**:
- Trained on historical incidents
- 10 features (anomaly score, error rate, latency, CPU, memory, etc.)
- 5 strategies (restart, scale up, rollback, circuit breaker, no action)
- Feature importance tracking

**Q-Learning Agent**:
- Reinforcement learning
- 1000 states, 5 actions
- Epsilon-greedy exploration (10%)
- Online learning from outcomes

**Thompson Sampling Bandit**:
- Bayesian approach
- Beta distribution for each strategy
- Balances exploration/exploitation
- Win rate tracking

### 3. Recovery Strategies (`recovery_strategies.py`)

**7 recovery strategies** with execution tracking:

1. **Restart Pod**: Restart unhealthy pods
2. **Scale Up**: Increase replicas
3. **Scale Down**: Decrease replicas
4. **Rollback**: Revert to previous version
5. **Circuit Breaker**: Enable/disable circuit breaker
6. **Notify**: Send notifications
7. **No Action**: Monitor only

Each strategy tracks:
- Execution count
- Success/failure rate
- Average duration
- Execution history (last 100)

### 4. Decision Engine (`decision_engine.py`)

**Main orchestrator** coordinating all components:

**Decision Flow**:
1. **Context Enrichment**: Add timestamp, time-based features
2. **Rule Evaluation**: Match rules by priority
3. **ML Recommendations**: Get predictions from all models
4. **Strategy Ranking**: Combine rules + ML, rank by confidence
5. **Strategy Selection**: Choose highest confidence
6. **Execution**: Execute and track outcome
7. **Feedback Loop**: Update ML models based on success/failure

**Decision Logging**:
- Unique ID for each decision
- Full context and reasoning
- Execution outcome
- Performance metrics

---

## API Endpoints

### Decision Making

**POST `/api/decision/make`**
- Make a decision without executing
- Returns: decision ID, strategy, confidence, reasoning

**POST `/api/decision/execute/{decision_id}`**
- Execute a previously made decision
- Returns: success status, execution time

**POST `/api/decision/decide-and-execute`**
- Make and execute decision immediately
- Returns: decision details + execution outcome

### Monitoring

**GET `/api/decision/recent?count=10`**
- Get recent decisions

**GET `/api/stats`**
- Get engine statistics (decisions, rules, strategies, ML models)

**GET `/api/rules`**
- List all rules

**POST `/api/rules/{rule_id}/enable`**
- Enable a rule

**POST `/api/rules/{rule_id}/disable`**
- Disable a rule

**GET `/api/strategies`**
- Get all strategies with statistics

**GET `/health`**
- Health check

**GET `/metrics`**
- Prometheus metrics

---

## Request Example

```json
{
  "service": "gateway-service",
  "anomaly_score": 0.85,
  "error_rate": 0.12,
  "p95_latency": 950,
  "cpu_usage": 0.75,
  "memory_usage": 0.65,
  "request_rate": 3500,
  "current_replicas": 5,
  "restart_count_last_hour": 1,
  "service_health": "unhealthy"
}
```

## Response Example

```json
{
  "decision_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "strategy": "restart_pod",
  "confidence": 0.92,
  "reasoning": "Rules matched: restart_pod | ML models: decision_tree: restart_pod (0.89); q_learning: restart_pod (0.70); thompson_sampling: restart_pod (0.85) | Selected: restart_pod (confidence: 0.92)",
  "executed": true,
  "success": true
}
```

---

## Deployment

### Build Docker Image

```bash
cd decision-engine
docker build -t decision-engine:latest .
```

### Train ML Model

```bash
python training/train_model.py
```

### Deploy to Kubernetes

```bash
kubectl apply -f k8s/deployments/decision-engine-deployment.yaml
```

### Verify Deployment

```bash
# Check pods
kubectl get pods -n self-healing-prod -l app=decision-engine

# Check logs
kubectl logs -n self-healing-prod -l app=decision-engine -f

# Test API
kubectl port-forward -n self-healing-prod svc/decision-engine-service 8095:8095

curl http://localhost:8095/health
curl http://localhost:8095/api/stats
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RULES_FILE` | `rules.yaml` | Path to rules configuration |
| `RECOVERY_MANAGER_URL` | `http://recovery-manager-service:8080` | Recovery manager endpoint |
| `NOTIFICATION_URL` | `http://notification-service:8080` | Notification service endpoint |
| `PROMETHEUS_URL` | `http://prometheus:9090` | Prometheus endpoint |
| `ANOMALY_DETECTOR_URL` | `http://anomaly-detector:8090` | Anomaly detector endpoint |
| `PORT` | `8095` | Service port |
| `LOG_LEVEL` | `INFO` | Logging level |

### Rules Configuration

Edit `rules.yaml` to customize decision rules:

```yaml
rules:
  - id: custom-rule
    name: "Custom Rule"
    priority: 100
    conditions:
      - field: anomaly_score
        operator: ">"
        value: 0.8
    actions:
      - type: restart_pod
        params:
          grace_period: 30
    cooldown: 300
    exclusive: false
    enabled: true
```

---

## Monitoring

### Prometheus Metrics

- `decision_engine_decisions_total{strategy, success}`: Total decisions
- `decision_engine_decision_duration_seconds`: Decision making duration
- `decision_engine_execution_duration_seconds`: Execution duration
- `decision_engine_confidence`: Current decision confidence

### Grafana Dashboard

Import dashboard from `k8s/observability/dashboards/decision-engine-dashboard.json`

---

## ML Model Training

### Generate Training Data

```python
from training.train_model import generate_training_data

X, y = generate_training_data(n_samples=5000)
```

### Train Model

```bash
python training/train_model.py
```

### Evaluate Model

The training script outputs:
- Classification report
- Confusion matrix
- Feature importance

### Update Model

1. Train new model
2. Save to `models/decision_tree.pkl`
3. Restart decision engine pods

---

## Integration Example

### From Anomaly Detector

```python
import httpx

async def trigger_decision(service: str, anomaly_score: float):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://decision-engine-service:8095/api/decision/decide-and-execute",
            json={
                "service": service,
                "anomaly_score": anomaly_score,
                "error_rate": 0.05,
                "p95_latency": 300,
                "cpu_usage": 0.6,
                "memory_usage": 0.5,
                "request_rate": 1000,
                "current_replicas": 3,
                "service_health": "healthy"
            }
        )
        
        return response.json()
```

---

## Performance

| Metric | Target | Typical |
|--------|--------|---------|
| Decision latency | < 100ms | ~50ms |
| Execution latency | < 5s | ~2s |
| Decision accuracy | > 85% | ~90% |
| Strategy success rate | > 90% | ~92% |

---

## Troubleshooting

### Decision Engine Not Starting

```bash
# Check logs
kubectl logs -n self-healing-prod -l app=decision-engine

# Common issues:
# - Rules file not found
# - Invalid YAML syntax
# - Missing dependencies
```

### Low Decision Accuracy

```bash
# Retrain model with more data
python training/train_model.py

# Check rule configuration
curl http://localhost:8095/api/rules

# Review recent decisions
curl http://localhost:8095/api/decision/recent?count=50
```

### Strategy Failures

```bash
# Check strategy statistics
curl http://localhost:8095/api/strategies

# Verify recovery manager connectivity
kubectl exec -n self-healing-prod deployment/decision-engine -- \
  curl http://recovery-manager-service:8080/health
```

---

## Best Practices

1. **Start Conservative**: Begin with high confidence thresholds
2. **Monitor Closely**: Watch decision outcomes for first week
3. **Tune Rules**: Adjust priorities and cooldowns based on results
4. **Train Regularly**: Retrain ML models monthly with new data
5. **A/B Testing**: Test new rules in shadow mode first
6. **Document Decisions**: Review decision logs for insights
7. **Gradual Rollout**: Enable rules incrementally

---

## Future Enhancements

- [ ] Deep learning models (LSTM, Transformer)
- [ ] Multi-objective optimization
- [ ] Explainable AI (SHAP values)
- [ ] Automated rule generation
- [ ] Federated learning across clusters
- [ ] Real-time model updates
- [ ] Decision simulation mode

---

## License

MIT License
