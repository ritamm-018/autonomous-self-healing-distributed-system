# AI-Powered Anomaly Detection Service

## Overview

Predictive anomaly detection platform using machine learning to forecast failures before they occur.

## Features

- **Isolation Forest**: Unsupervised anomaly detection
- **LSTM**: Time-series prediction and trend analysis
- **Ensemble Scoring**: Combined predictions with confidence scores
- **Prometheus Integration**: Real-time metrics collection
- **REST API**: 5 endpoints for predictions and status
- **Automated Triggers**: Threshold-based recovery actions

## Architecture

```
Prometheus → Metrics Collector → Feature Extractor → ML Models → Anomaly Score → Recovery Manager
                                                         ↓
                                                  Isolation Forest
                                                       LSTM
                                                    Ensemble
```

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Train models (generates synthetic data)
python training/train_isolation_forest.py

# Run service
python -m app.main
```

Service will be available at `http://localhost:8090`

### Docker

```bash
# Build image
docker build -t anomaly-detector:latest .

# Run container
docker run -p 8090:8090 \
  -e PROMETHEUS_URL=http://prometheus:9090 \
  anomaly-detector:latest
```

### Kubernetes

```bash
# Deploy
kubectl apply -f k8s/deployments/anomaly-detector-deployment.yaml

# Check status
kubectl get pods -n self-healing-prod -l app=anomaly-detector
```

## API Endpoints

### 1. Get Anomaly Score
```http
GET /api/anomaly/score/{service_name}
```

Returns current anomaly score and recommendation.

### 2. Get All Services Status
```http
GET /api/anomaly/status
```

Returns anomaly status for all monitored services.

### 3. Manual Prediction
```http
POST /api/anomaly/predict
Content-Type: application/json

{
  "service": "gateway-service",
  "metrics": {
    "cpu_usage": 0.85,
    "memory_usage": 0.78
  }
}
```

### 4. Models Status
```http
GET /api/anomaly/models/status
```

### 5. Health Check
```http
GET /health
```

## Configuration

Environment variables:

- `PROMETHEUS_URL`: Prometheus server URL
- `RECOVERY_MANAGER_URL`: Recovery Manager URL
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)

## ML Models

### Isolation Forest

- **Purpose**: Statistical anomaly detection
- **Algorithm**: Unsupervised learning
- **Training**: Normal metrics only
- **Output**: Anomaly score 0-1

### LSTM

- **Purpose**: Time-series prediction
- **Architecture**: 2 LSTM layers + Dense layers
- **Input**: 60 timesteps (15 minutes)
- **Output**: Crash probability 0-1

### Ensemble

- **Weights**: 40% Isolation Forest + 60% LSTM
- **Severity Multipliers**: Based on metrics
- **Thresholds**:
  - 0.3: Warning
  - 0.6: Critical
  - 0.8: Emergency

## Training

```bash
# Train Isolation Forest
python training/train_isolation_forest.py

# Models saved to models/ directory
```

## Metrics

The service exports Prometheus metrics:

- `anomaly_score{service}`: Current anomaly score
- `anomaly_predictions_total{service,severity}`: Total predictions
- `anomaly_model_inference_seconds`: Inference time

## Integration

### With Recovery Manager

```java
// Recovery Manager calls anomaly detector
String anomalyUrl = "http://anomaly-detector-service:8090/api/anomaly/score/" + serviceName;
AnomalyResult result = restTemplate.getForObject(anomalyUrl, AnomalyResult.class);

if (result.getScore() >= 0.8) {
    executeRecovery(serviceName, result.getRecommendation());
}
```

## Development

### Project Structure

```
anomaly-detector/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── metrics_collector.py    # Prometheus queries
│   ├── feature_extractor.py    # Feature engineering
│   ├── models/
│   │   ├── isolation_forest.py
│   │   ├── lstm_predictor.py
│   │   └── ensemble.py
│   └── api/
│       └── routes.py           # REST endpoints
├── training/
│   └── train_isolation_forest.py
├── models/                     # Saved models
├── requirements.txt
├── Dockerfile
└── README.md
```

## License

MIT
