# Auto-Scaling & Load Testing Deployment Guide

## Overview

This guide covers deploying the intelligent auto-scaling system with KEDA, load testing tools, chaos engineering, and predictive scaling.

---

## Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3.x
- Prometheus and Grafana deployed
- At least 10GB free storage
- 10+ CPU cores and 20GB+ RAM

---

## Deployment Steps

### 1. Install KEDA

```bash
# Add KEDA Helm repository
helm repo add kedacore https://kedacore.github.io/charts
helm repo update

# Install KEDA
helm install keda kedacore/keda \
  --namespace keda \
  --create-namespace \
  --set prometheus.metricServer.enabled=true \
  --set prometheus.metricServer.port=9022

# Verify installation
kubectl get pods -n keda

# Expected output:
# NAME                                      READY   STATUS    RESTARTS   AGE
# keda-operator-...                         1/1     Running   0          1m
# keda-metrics-apiserver-...                1/1     Running   0          1m
```

### 2. Deploy KEDA ScaledObjects

```bash
# Apply ScaledObjects for all services
kubectl apply -f k8s/scaling/keda-scaledobjects.yaml

# Verify ScaledObjects
kubectl get scaledobjects -n self-healing-prod

# Check HPA created by KEDA
kubectl get hpa -n self-healing-prod

# Expected output:
# NAME                           REFERENCE                     TARGETS   MINPODS   MAXPODS
# keda-hpa-gateway-service       Deployment/gateway-service    0/1000    3         50
# keda-hpa-auth-service          Deployment/auth-service       0/500     2         30
# ...
```

### 3. Deploy Predictive Scaler

```bash
# Build Docker image
cd scaling
docker build -t predictive-scaler:latest .

# Load image to cluster (for local development)
kind load docker-image predictive-scaler:latest

# Deploy predictive scaler
kubectl apply -f k8s/scaling/predictive-scaler-deployment.yaml

# Verify deployment
kubectl get pods -n self-healing-prod -l app=predictive-scaler

# Check logs
kubectl logs -n self-healing-prod -l app=predictive-scaler -f
```

### 4. Install Chaos Mesh

```bash
# Add Chaos Mesh Helm repository
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm repo update

# Install Chaos Mesh
helm install chaos-mesh chaos-mesh/chaos-mesh \
  --namespace chaos-testing \
  --create-namespace \
  --set chaosDaemon.runtime=containerd \
  --set chaosDaemon.socketPath=/run/containerd/containerd.sock \
  --set dashboard.create=true

# Verify installation
kubectl get pods -n chaos-testing

# Access Chaos Mesh Dashboard
kubectl port-forward -n chaos-testing svc/chaos-dashboard 2333:2333

# Open http://localhost:2333
```

### 5. Deploy Chaos Experiments

```bash
# Apply chaos experiments
kubectl apply -f chaos/chaos-experiments.yaml

# List experiments
kubectl get podchaos,networkchaos,stresschaos -n chaos-testing

# View experiment status
kubectl describe podchaos pod-failure-test -n chaos-testing

# Pause an experiment
kubectl annotate podchaos pod-failure-test \
  -n chaos-testing \
  experiment.chaos-mesh.org/pause=true

# Resume an experiment
kubectl annotate podchaos pod-failure-test \
  -n chaos-testing \
  experiment.chaos-mesh.org/pause-
```

### 6. Deploy Load Testing Tools

#### K6 (Standalone)

```bash
# Install K6
# On macOS
brew install k6

# On Linux
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | \
  sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# Run K6 test
cd load-testing
k6 run --vus 100 --duration 10m k6-load-test.js

# Run with Prometheus output
k6 run --out experimental-prometheus-rw k6-load-test.js
```

#### Locust (Distributed)

```bash
# Create ConfigMap from script
kubectl create configmap locust-scripts \
  --from-file=locust-load-test.py \
  -n self-healing-prod

# Deploy Locust
kubectl apply -f k8s/scaling/locust-deployment.yaml

# Verify deployment
kubectl get pods -n self-healing-prod -l app=locust

# Access Locust UI
kubectl port-forward -n self-healing-prod svc/locust-master 8089:8089

# Open http://localhost:8089
# Set users: 1000
# Set spawn rate: 10/s
# Click "Start swarming"
```

---

## Load Testing Scenarios

### Scenario 1: Gradual Ramp-up

**Objective**: Test smooth scaling behavior

```bash
# K6
k6 run --stage 2m:100 --stage 5m:100 --stage 2m:500 --stage 5m:500 k6-load-test.js

# Locust
# In UI: Start with 100 users, gradually increase to 500
```

**Expected Behavior**:
- Pods scale up smoothly
- No errors during scaling
- P95 latency < 500ms

### Scenario 2: Spike Test

**Objective**: Test rapid scale-up

```bash
# K6
k6 run --stage 30s:10 --stage 1m:1000 --stage 5m:1000 k6-load-test.js
```

**Expected Behavior**:
- Rapid scale-up (< 2 minutes)
- Error rate < 5% during spike
- Recovery to normal latency within 3 minutes

### Scenario 3: Sustained Load

**Objective**: Test stability under constant load

```bash
# K6
k6 run --vus 500 --duration 30m k6-load-test.js
```

**Expected Behavior**:
- Stable pod count
- No pod restarts
- Consistent latency

### Scenario 4: Soak Test

**Objective**: Test for memory leaks

```bash
# K6
k6 run --vus 200 --duration 4h k6-load-test.js
```

**Expected Behavior**:
- No memory growth
- No performance degradation
- Stable error rate

---

## Chaos Testing Scenarios

### Scenario 1: Pod Failure Recovery

```bash
# Trigger pod failure
kubectl apply -f - <<EOF
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: manual-pod-failure
  namespace: chaos-testing
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - self-healing-prod
    labelSelectors:
      app: gateway-service
  duration: "30s"
EOF

# Monitor recovery
kubectl get pods -n self-healing-prod -w

# Check metrics
kubectl port-forward -n self-healing-monitoring svc/grafana 3000:3000
# View "System Overview" dashboard
```

**Expected Behavior**:
- Pod recreated within 30s
- No service disruption
- Anomaly detector triggers warning

### Scenario 2: Network Latency

```bash
# Add 200ms latency
kubectl apply -f - <<EOF
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: manual-network-delay
  namespace: chaos-testing
spec:
  action: delay
  mode: all
  selector:
    namespaces:
      - self-healing-prod
    labelSelectors:
      app: data-service
  delay:
    latency: "200ms"
  duration: "5m"
EOF

# Monitor latency
# P95 should increase but stay < 700ms
```

### Scenario 3: CPU Stress

```bash
# Stress CPU
kubectl apply -f - <<EOF
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: manual-cpu-stress
  namespace: chaos-testing
spec:
  mode: one
  selector:
    namespaces:
      - self-healing-prod
    labelSelectors:
      app: auth-service
  stressors:
    cpu:
      workers: 4
      load: 90
  duration: "5m"
EOF

# Monitor scaling
kubectl get hpa -n self-healing-prod -w

# Should scale up due to CPU pressure
```

---

## Monitoring Scaling Events

### Prometheus Queries

```promql
# Current replica count
kube_deployment_status_replicas{namespace="self-healing-prod"}

# Desired vs actual replicas
kube_deployment_spec_replicas{namespace="self-healing-prod"}
- kube_deployment_status_replicas{namespace="self-healing-prod"}

# HPA current metrics
kube_horizontalpodautoscaler_status_current_metrics{namespace="self-healing-prod"}

# Scaling events
rate(kube_hpa_status_condition{status="true"}[5m])

# Pod creation rate
rate(kube_pod_created{namespace="self-healing-prod"}[5m])
```

### Grafana Dashboard

```bash
# Import scaling dashboard
kubectl port-forward -n self-healing-monitoring svc/grafana 3000:3000

# Navigate to Dashboards > Import
# Upload: k8s/observability/dashboards/scaling-dashboard.json
```

---

## Troubleshooting

### KEDA Not Scaling

```bash
# Check KEDA logs
kubectl logs -n keda -l app=keda-operator

# Check ScaledObject status
kubectl describe scaledobject gateway-service-scaler -n self-healing-prod

# Check metrics server
kubectl get apiservice v1beta1.external.metrics.k8s.io

# Test Prometheus query manually
kubectl port-forward -n self-healing-monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Visit http://localhost:9090
# Run query: sum(rate(http_requests_total{app="gateway-service"}[1m]))
```

### Predictive Scaler Not Working

```bash
# Check logs
kubectl logs -n self-healing-prod -l app=predictive-scaler

# Check RBAC permissions
kubectl auth can-i update deployments --as=system:serviceaccount:self-healing-prod:predictive-scaler

# Manually trigger scaling cycle
kubectl exec -n self-healing-prod deployment/predictive-scaler -- \
  python -c "from predictive_scaler import PredictiveScaler; PredictiveScaler().run_scaling_cycle()"
```

### Chaos Experiments Failing

```bash
# Check Chaos Mesh status
kubectl get pods -n chaos-testing

# Check experiment status
kubectl get podchaos,networkchaos,stresschaos -A

# View experiment logs
kubectl logs -n chaos-testing -l app.kubernetes.io/component=controller-manager

# Check if chaos-daemon is running
kubectl get pods -n chaos-testing -l app.kubernetes.io/component=chaos-daemon
```

### Load Test Not Generating Traffic

```bash
# Check Locust pods
kubectl get pods -n self-healing-prod -l app=locust

# Check master logs
kubectl logs -n self-healing-prod -l app=locust,role=master

# Check worker logs
kubectl logs -n self-healing-prod -l app=locust,role=worker

# Verify service connectivity
kubectl exec -n self-healing-prod deployment/locust-master -- \
  curl -v http://gateway-service/api/health
```

---

## Performance Benchmarks

### Scaling Performance

| Metric | Target | Measured |
|--------|--------|----------|
| Scale-up time (10→50 pods) | < 2 min | TBD |
| Scale-down time (50→10 pods) | < 5 min | TBD |
| Max throughput | 100k RPS | TBD |
| P95 latency (under load) | < 500ms | TBD |
| Error rate (during scaling) | < 1% | TBD |

### Chaos Resilience

| Test | Target | Result |
|------|--------|--------|
| Pod failure recovery | < 30s | TBD |
| Network latency tolerance | P95 < 700ms | TBD |
| CPU stress handling | Auto-scale | TBD |
| Memory leak detection | No leaks | TBD |

---

## Best Practices

1. **Start Small**: Begin with low load and gradually increase
2. **Monitor Closely**: Watch metrics during scaling events
3. **Test in Staging**: Run chaos tests in non-production first
4. **Set Alerts**: Configure alerts for scaling failures
5. **Document Results**: Record benchmark results for comparison
6. **Regular Testing**: Run load tests weekly
7. **Gradual Rollout**: Enable chaos experiments gradually
8. **Backup Plan**: Have rollback procedures ready

---

## Next Steps

1. Run baseline load tests
2. Measure scaling performance
3. Execute chaos experiments
4. Tune KEDA thresholds
5. Optimize predictive scaler
6. Create custom dashboards
7. Set up automated testing
8. Document lessons learned
