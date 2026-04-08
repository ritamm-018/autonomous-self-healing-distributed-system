# Grafana Dashboards Guide

This directory contains pre-configured Grafana dashboards for the self-healing system.

## Dashboards

### 1. System Overview Dashboard
**File**: `system-overview-dashboard.json`

**Panels**:
- Total requests/sec across all services
- Overall error rate
- P50/P95/P99 latency
- CPU and memory usage (cluster-wide)
- Pod count by service
- Anomaly score heatmap
- Active alerts

**Use Case**: High-level system health monitoring

---

### 2. Service Dashboard
**File**: `service-dashboard.json`

**Panels**:
- Request rate
- Error rate and error count
- Latency percentiles (p50, p95, p99)
- CPU usage
- Memory usage (heap and non-heap)
- JVM metrics (GC pause time, GC frequency)
- Active connections
- Anomaly score timeline
- Recent errors (from Elasticsearch)

**Variables**:
- `$service`: Service selector
- `$namespace`: Namespace selector

**Use Case**: Deep-dive into individual service performance

---

### 3. Anomaly Detection Dashboard
**File**: `anomaly-dashboard.json`

**Panels**:
- Anomaly score timeline (all services)
- Anomaly type distribution (pie chart)
- Predicted crash times
- Model scores comparison (Isolation Forest vs LSTM)
- Anomaly indicators count
- Recovery actions triggered
- Model inference time

**Use Case**: Monitor ML-based anomaly detection

---

### 4. SLA/SLO Dashboard
**File**: `slo-dashboard.json`

**Panels**:
- SLO compliance percentage (99.9% target)
- Error budget remaining
- MTTR (Mean Time To Recovery)
- MTBF (Mean Time Between Failures)
- Incident frequency
- Recovery success rate
- Downtime cost estimation

**Use Case**: Business-level SLA tracking

---

## Installation

### Option 1: Helm (Recommended)

```bash
# Install kube-prometheus-stack with Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace self-healing-monitoring \
  --create-namespace \
  --set grafana.enabled=true \
  --set grafana.adminPassword=admin123
```

### Option 2: Manual Deployment

```bash
# Deploy Grafana
kubectl apply -f grafana-deployment.yaml

# Import dashboards
kubectl create configmap grafana-dashboards \
  --from-file=system-overview-dashboard.json \
  --from-file=service-dashboard.json \
  --from-file=anomaly-dashboard.json \
  --from-file=slo-dashboard.json \
  -n self-healing-monitoring
```

---

## Accessing Grafana

### Port Forward

```bash
kubectl port-forward -n self-healing-monitoring svc/grafana 3000:3000
```

Then open: http://localhost:3000

**Default credentials**:
- Username: `admin`
- Password: `admin123` (change in production)

### Ingress (Production)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: grafana-ingress
  namespace: self-healing-monitoring
spec:
  rules:
  - host: grafana.self-healing.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: grafana
            port:
              number: 3000
```

---

## Useful Queries

### Request Rate
```promql
sum(rate(http_requests_total[5m])) by (service)
```

### Error Rate
```promql
sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
/ sum(rate(http_requests_total[5m])) by (service)
```

### P99 Latency
```promql
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)
)
```

### Anomaly Score
```promql
anomaly_score{service="gateway-service"}
```

### SLO Compliance
```promql
100 * (1 - (
  sum(rate(http_requests_total{status=~"5.."}[30d]))
  /
  sum(rate(http_requests_total[30d]))
))
```

---

## Dashboard Variables

### Service Selector
```
label_values(http_requests_total, service)
```

### Namespace Selector
```
label_values(kube_pod_info, namespace)
```

### Time Range
- Last 5 minutes
- Last 15 minutes
- Last 1 hour
- Last 6 hours
- Last 24 hours
- Last 7 days

---

## Alerts Integration

Grafana dashboards show active alerts from Prometheus AlertManager:

- **Emergency**: Red background
- **Critical**: Orange background
- **Warning**: Yellow background
- **Normal**: Green background

---

## Customization

### Adding New Panels

1. Open dashboard in edit mode
2. Click "Add Panel"
3. Select visualization type
4. Enter PromQL query
5. Configure panel settings
6. Save dashboard

### Exporting Dashboards

```bash
# Export dashboard JSON
curl -u admin:admin123 \
  http://localhost:3000/api/dashboards/uid/system-overview \
  | jq '.dashboard' > system-overview-dashboard.json
```

---

## Troubleshooting

### Dashboard Not Loading

Check datasource connection:
```bash
kubectl logs -n self-healing-monitoring deployment/grafana
```

### No Data in Panels

Verify Prometheus is scraping:
```bash
kubectl port-forward -n self-healing-monitoring \
  svc/prometheus-kube-prometheus-prometheus 9090:9090

# Open http://localhost:9090/targets
```

### Slow Queries

Optimize with recording rules in `prometheus-rules.yaml`

---

## Best Practices

1. **Use Variables**: Make dashboards reusable across services
2. **Set Thresholds**: Add visual indicators for SLOs
3. **Add Annotations**: Mark deployments and incidents
4. **Use Templates**: Create dashboard templates for new services
5. **Regular Backups**: Export dashboards regularly
