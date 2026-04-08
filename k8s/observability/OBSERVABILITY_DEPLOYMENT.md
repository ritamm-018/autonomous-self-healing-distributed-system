# Observability Stack Deployment Guide

## Overview

This guide covers deploying the complete observability stack for the self-healing system:
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **ELK Stack**: Centralized logging (Elasticsearch, Logstash, Kibana)
- **Jaeger**: Distributed tracing

---

## Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3.x (optional, for Prometheus stack)
- At least 50GB storage available
- 20+ CPU cores and 40GB+ RAM for full stack

---

## Deployment Steps

### 1. Create Namespace

```bash
kubectl create namespace self-healing-monitoring
```

### 2. Deploy Prometheus Stack (Option A: Helm - Recommended)

```bash
# Add Prometheus Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace self-healing-monitoring \
  --set prometheus.prometheusSpec.retention=15d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=50Gi \
  --set grafana.enabled=false \
  --set alertmanager.enabled=true

# Verify installation
kubectl get pods -n self-healing-monitoring
```

### 2. Deploy Prometheus Stack (Option B: Manual)

```bash
# Apply recording and alert rules
kubectl apply -f k8s/observability/prometheus-rules.yaml

# Verify rules loaded
kubectl port-forward -n self-healing-monitoring \
  svc/prometheus-kube-prometheus-prometheus 9090:9090

# Open http://localhost:9090/rules
```

### 3. Deploy Grafana

```bash
# Apply Grafana deployment
kubectl apply -f k8s/observability/grafana-deployment.yaml

# Wait for Grafana to be ready
kubectl wait --for=condition=ready pod \
  -l app=grafana \
  -n self-healing-monitoring \
  --timeout=300s

# Get Grafana password
kubectl get secret grafana-secrets \
  -n self-healing-monitoring \
  -o jsonpath='{.data.admin-password}' | base64 -d

# Port forward to access
kubectl port-forward -n self-healing-monitoring svc/grafana 3000:3000

# Open http://localhost:3000
# Login: admin / <password from above>
```

### 4. Deploy ELK Stack

```bash
# Deploy Elasticsearch cluster
kubectl apply -f k8s/observability/elk-stack.yaml

# Wait for Elasticsearch cluster to be healthy
kubectl wait --for=condition=ready pod \
  -l app=elasticsearch \
  -n self-healing-monitoring \
  --timeout=600s

# Check cluster health
kubectl port-forward -n self-healing-monitoring svc/elasticsearch-client 9200:9200

curl http://localhost:9200/_cluster/health?pretty

# Expected output:
# {
#   "status" : "green",
#   "number_of_nodes" : 3
# }
```

### 5. Deploy Jaeger

```bash
# Deploy Jaeger
kubectl apply -f k8s/observability/jaeger-deployment.yaml

# Wait for Jaeger to be ready
kubectl wait --for=condition=ready pod \
  -l app=jaeger \
  -n self-healing-monitoring \
  --timeout=300s

# Access Jaeger UI
kubectl port-forward -n self-healing-monitoring svc/jaeger-query 16686:16686

# Open http://localhost:16686
```

### 6. Configure Service Instrumentation

Add OpenTelemetry dependencies to each microservice:

**pom.xml** (for all Java services):
```xml
<dependencies>
    <!-- OpenTelemetry API -->
    <dependency>
        <groupId>io.opentelemetry</groupId>
        <artifactId>opentelemetry-api</artifactId>
        <version>1.32.0</version>
    </dependency>
    
    <!-- OpenTelemetry SDK -->
    <dependency>
        <groupId>io.opentelemetry</groupId>
        <artifactId>opentelemetry-sdk</artifactId>
        <version>1.32.0</version>
    </dependency>
    
    <!-- OpenTelemetry Jaeger Exporter -->
    <dependency>
        <groupId>io.opentelemetry</groupId>
        <artifactId>opentelemetry-exporter-jaeger</artifactId>
        <version>1.32.0</version>
    </dependency>
    
    <!-- Spring Boot Starter for OpenTelemetry -->
    <dependency>
        <groupId>io.opentelemetry.instrumentation</groupId>
        <artifactId>opentelemetry-spring-boot-starter</artifactId>
        <version>1.32.0-alpha</version>
    </dependency>
</dependencies>
```

**application.yml** (add to each service):
```yaml
otel:
  traces:
    exporter: jaeger
  exporter:
    jaeger:
      endpoint: http://jaeger-collector.self-healing-monitoring:14250
  service:
    name: ${spring.application.name}
  resource:
    attributes:
      service.namespace: self-healing-prod
```

### 7. Configure Log Shipping

Add Filebeat as a sidecar to each service deployment:

```yaml
# Add to each deployment's pod spec
- name: filebeat
  image: docker.elastic.co/beats/filebeat:8.11.3
  args: [
    "-c", "/etc/filebeat.yml",
    "-e",
  ]
  volumeMounts:
  - name: filebeat-config
    mountPath: /etc/filebeat.yml
    subPath: filebeat.yml
  - name: logs
    mountPath: /var/log/app
```

**Filebeat ConfigMap**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: filebeat-config
  namespace: self-healing-prod
data:
  filebeat.yml: |
    filebeat.inputs:
    - type: log
      enabled: true
      paths:
        - /var/log/app/*.log
      json.keys_under_root: true
      json.add_error_key: true
    
    output.logstash:
      hosts: ["logstash.self-healing-monitoring:5044"]
```

### 8. Verify Complete Stack

```bash
# Check all pods are running
kubectl get pods -n self-healing-monitoring

# Expected output:
# NAME                            READY   STATUS    RESTARTS   AGE
# prometheus-...                  1/1     Running   0          10m
# alertmanager-...                1/1     Running   0          10m
# grafana-...                     1/1     Running   0          8m
# elasticsearch-0                 1/1     Running   0          6m
# elasticsearch-1                 1/1     Running   0          6m
# elasticsearch-2                 1/1     Running   0          6m
# logstash-...                    1/1     Running   0          5m
# kibana-...                      1/1     Running   0          5m
# jaeger-...                      1/1     Running   0          4m

# Check services
kubectl get svc -n self-healing-monitoring
```

---

## Accessing the Stack

### Prometheus

```bash
kubectl port-forward -n self-healing-monitoring \
  svc/prometheus-kube-prometheus-prometheus 9090:9090
```
Open: http://localhost:9090

### Grafana

```bash
kubectl port-forward -n self-healing-monitoring svc/grafana 3000:3000
```
Open: http://localhost:3000
- Username: `admin`
- Password: (from secret)

### Kibana

```bash
kubectl port-forward -n self-healing-monitoring svc/kibana 5601:5601
```
Open: http://localhost:5601

### Jaeger

```bash
kubectl port-forward -n self-healing-monitoring svc/jaeger-query 16686:16686
```
Open: http://localhost:16686

---

## Post-Deployment Configuration

### 1. Import Grafana Dashboards

```bash
# System Overview Dashboard
curl -X POST http://admin:admin123@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @k8s/observability/dashboards/system-overview.json

# Service Dashboard
curl -X POST http://admin:admin123@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @k8s/observability/dashboards/service-dashboard.json

# Anomaly Dashboard
curl -X POST http://admin:admin123@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @k8s/observability/dashboards/anomaly-dashboard.json

# SLO Dashboard
curl -X POST http://admin:admin123@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @k8s/observability/dashboards/slo-dashboard.json
```

### 2. Configure Kibana Index Patterns

```bash
# Create index pattern for logs
curl -X POST http://localhost:5601/api/saved_objects/index-pattern/logs-* \
  -H "kbn-xsrf: true" \
  -H "Content-Type: application/json" \
  -d '{
    "attributes": {
      "title": "logs-*",
      "timeFieldName": "@timestamp"
    }
  }'
```

### 3. Configure AlertManager

Edit AlertManager configuration:

```bash
kubectl edit configmap alertmanager-prometheus-kube-prometheus-alertmanager \
  -n self-healing-monitoring
```

Add notification receivers:

```yaml
receivers:
- name: 'slack'
  slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    channel: '#alerts'
    title: '{{ .GroupLabels.alertname }}'
    text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

- name: 'email'
  email_configs:
  - to: 'team@example.com'
    from: 'alertmanager@example.com'
    smarthost: 'smtp.example.com:587'
    auth_username: 'alertmanager@example.com'
    auth_password: 'password'
```

---

## Troubleshooting

### Prometheus Not Scraping

```bash
# Check ServiceMonitor
kubectl get servicemonitor -n self-healing-prod

# Check Prometheus targets
kubectl port-forward -n self-healing-monitoring \
  svc/prometheus-kube-prometheus-prometheus 9090:9090

# Visit http://localhost:9090/targets
```

### Elasticsearch Cluster Not Healthy

```bash
# Check pod logs
kubectl logs -n self-healing-monitoring elasticsearch-0

# Check cluster status
kubectl exec -n self-healing-monitoring elasticsearch-0 -- \
  curl -s http://localhost:9200/_cluster/health?pretty

# Common issues:
# - Insufficient memory (increase ES_JAVA_OPTS)
# - vm.max_map_count too low (check init container)
# - Disk space (check PVC)
```

### Logs Not Appearing in Kibana

```bash
# Check Logstash is receiving logs
kubectl logs -n self-healing-monitoring deployment/logstash

# Check Elasticsearch indices
kubectl exec -n self-healing-monitoring elasticsearch-0 -- \
  curl -s http://localhost:9200/_cat/indices?v

# Check Filebeat on services
kubectl logs -n self-healing-prod <pod-name> -c filebeat
```

### Traces Not Appearing in Jaeger

```bash
# Check Jaeger collector logs
kubectl logs -n self-healing-monitoring deployment/jaeger

# Verify service instrumentation
# Check application logs for OpenTelemetry initialization

# Test with manual trace
curl -X POST http://jaeger-collector:14268/api/traces \
  -H "Content-Type: application/json" \
  -d '{"data": [{"traceID": "test", "spans": []}]}'
```

---

## Resource Monitoring

Monitor observability stack resource usage:

```bash
# CPU and memory usage
kubectl top pods -n self-healing-monitoring

# Storage usage
kubectl get pvc -n self-healing-monitoring
```

---

## Backup and Restore

### Grafana Dashboards

```bash
# Backup
kubectl get configmap grafana-dashboards \
  -n self-healing-monitoring \
  -o yaml > grafana-dashboards-backup.yaml

# Restore
kubectl apply -f grafana-dashboards-backup.yaml
```

### Elasticsearch Snapshots

```bash
# Configure snapshot repository
curl -X PUT "localhost:9200/_snapshot/backup" \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "fs",
    "settings": {
      "location": "/backup"
    }
  }'

# Create snapshot
curl -X PUT "localhost:9200/_snapshot/backup/snapshot_1?wait_for_completion=true"
```

---

## Production Checklist

- [ ] Prometheus retention configured (15 days minimum)
- [ ] AlertManager notifications configured
- [ ] Grafana admin password changed
- [ ] Elasticsearch cluster healthy (green status)
- [ ] Log retention policy configured (30 days)
- [ ] Jaeger sampling rates configured
- [ ] All services instrumented for tracing
- [ ] Filebeat configured on all services
- [ ] Dashboards imported and tested
- [ ] Alerts tested and verified
- [ ] Backup strategy in place
- [ ] Team trained on tools

---

## Next Steps

1. Create custom dashboards for specific use cases
2. Set up alert routing and escalation
3. Configure log retention policies
4. Tune Jaeger sampling rates
5. Set up automated backups
6. Create runbooks for common alerts
7. Integrate with incident management system
