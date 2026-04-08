# Kubernetes Migration - Self-Healing Distributed System

## Overview

This directory contains all Kubernetes manifests and configurations to deploy the self-healing distributed system on Kubernetes with Istio service mesh, designed to handle 100k+ concurrent users.

## Architecture

- **7 Microservices**: Gateway, Auth, Data, Health Monitor, Recovery Manager, Logging, Notification
- **Istio Service Mesh**: Traffic management, security, observability
- **Horizontal Pod Autoscaling**: Automatic scaling based on CPU/memory
- **Self-Healing**: Kubernetes-native recovery using API instead of Docker socket

## Directory Structure

```
k8s/
├── 00-namespaces.yaml              # Namespace definitions
├── architecture-diagram.md         # Visual architecture documentation
├── DEPLOYMENT_GUIDE.md            # Step-by-step deployment instructions
├── ISTIO_SETUP.md                 # Istio installation guide
│
├── deployments/                    # Service deployments
│   ├── gateway-deployment.yaml
│   ├── auth-deployment.yaml
│   ├── data-deployment.yaml
│   ├── health-monitor-deployment.yaml
│   ├── recovery-manager-deployment.yaml
│   ├── logging-deployment.yaml
│   └── notification-deployment.yaml
│
├── config/                         # Configuration
│   ├── configmaps.yaml
│   └── secrets.yaml
│
├── istio/                          # Istio service mesh
│   ├── gateway.yaml
│   ├── virtual-services.yaml
│   ├── destination-rules.yaml
│   └── security-policies.yaml
│
├── security/                       # Security policies
│   └── network-policies.yaml
│
└── monitoring/                     # Observability
    └── servicemonitor.yaml
```

## Quick Start

### Prerequisites

1. Kubernetes cluster (3+ nodes, 8 vCPU, 16GB RAM each)
2. kubectl configured
3. Istio installed
4. Docker images built and pushed to registry

### Deploy

```bash
# 1. Install Istio (see ISTIO_SETUP.md)
istioctl install --set profile=production -y

# 2. Create namespaces
kubectl apply -f 00-namespaces.yaml

# 3. Configure secrets (UPDATE WITH REAL VALUES FIRST!)
kubectl apply -f config/secrets.yaml

# 4. Deploy ConfigMaps
kubectl apply -f config/configmaps.yaml

# 5. Deploy all services
kubectl apply -f deployments/

# 6. Deploy Istio configurations
kubectl apply -f istio/

# 7. Deploy security policies
kubectl apply -f security/

# 8. Verify deployment
kubectl get pods -n self-healing-prod
```

## Key Features

### Horizontal Pod Autoscaling

All services automatically scale based on:
- CPU utilization (70% target)
- Memory utilization (80% target)

Replica ranges:
- Gateway: 3-20 pods
- Auth: 2-15 pods
- Data: 3-25 pods (critical service)
- Health Monitor: 2-5 pods
- Recovery Manager: 2-5 pods
- Logging: 2-10 pods
- Notification: 2-8 pods

### Istio Service Mesh

- **Traffic Management**: Intelligent routing, load balancing
- **Security**: Mutual TLS, authorization policies
- **Observability**: Metrics, logs, distributed tracing
- **Resilience**: Circuit breakers, retries, timeouts

### Health Probes

All services have:
- **Liveness Probe**: Restart unhealthy pods
- **Readiness Probe**: Remove from service until ready
- **Startup Probe**: Allow slow-starting applications

### Rolling Updates

Zero-downtime deployments with:
- `maxSurge: 1` - Create 1 extra pod during update
- `maxUnavailable: 0` - Never reduce capacity

### Security

- **Network Policies**: Default deny, explicit allow
- **RBAC**: Least privilege for Recovery Manager
- **mTLS**: Automatic encryption between services
- **Pod Security**: Non-root, read-only filesystem

## Resource Requirements

### Baseline (Minimum Replicas)
- **Pods**: ~20
- **CPU**: ~6 cores
- **Memory**: ~8 GB

### Peak Load (Maximum Replicas)
- **Pods**: ~90
- **CPU**: ~50 cores
- **Memory**: ~60 GB

### Recommended Cluster
- **Nodes**: 5-10 (auto-scaling)
- **Node Size**: 8 vCPU, 16 GB RAM each
- **Total Capacity**: 40-80 vCPU, 80-160 GB RAM

## Monitoring

Access dashboards:

```bash
# Kiali (Service Mesh)
istioctl dashboard kiali

# Jaeger (Tracing)
istioctl dashboard jaeger

# Grafana (Metrics)
kubectl port-forward -n self-healing-monitoring svc/prometheus-grafana 3000:80

# Prometheus
kubectl port-forward -n self-healing-monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
```

## Testing Self-Healing

```bash
# Delete a pod
kubectl delete pod -l app=data-service -n self-healing-prod

# Watch recovery
kubectl get pods -n self-healing-prod -w

# Check Recovery Manager logs
kubectl logs -f deployment/recovery-manager -n self-healing-prod
```

## Scaling

### Manual Scaling
```bash
kubectl scale deployment gateway-service --replicas=10 -n self-healing-prod
```

### Load Testing
```bash
# Install k6
brew install k6  # or download from k6.io

# Run load test
k6 run --vus 1000 --duration 5m load-test.js
```

## Troubleshooting

### Pods Not Starting
```bash
kubectl describe pod <pod-name> -n self-healing-prod
kubectl logs <pod-name> -n self-healing-prod
```

### Istio Issues
```bash
istioctl analyze -n self-healing-prod
istioctl proxy-status
```

### HPA Not Scaling
```bash
kubectl get hpa -n self-healing-prod
kubectl top pods -n self-healing-prod
```

## Rollback

```bash
# Rollback deployment
kubectl rollout undo deployment/<service-name> -n self-healing-prod

# Check history
kubectl rollout history deployment/<service-name> -n self-healing-prod
```

## Cleanup

```bash
# Delete all resources
kubectl delete namespace self-healing-prod

# Uninstall Istio
istioctl uninstall --purge -y
```

## Documentation

- [Architecture Diagram](architecture-diagram.md) - Visual architecture
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Step-by-step deployment
- [Istio Setup](ISTIO_SETUP.md) - Istio installation and configuration

## Code Changes

The Recovery Manager has been updated to use Kubernetes API:
- Added `io.fabric8:kubernetes-client` dependency
- New `KubernetesRecoveryService` for pod management
- RBAC permissions for pod operations
- Environment variable `RECOVERY_MODE=kubernetes`

## Production Checklist

- [ ] All secrets updated with real values
- [ ] TLS certificates configured
- [ ] DNS records configured
- [ ] Monitoring stack deployed
- [ ] Load testing completed
- [ ] Backup strategy in place
- [ ] Team trained on kubectl and Istio

## Support

For detailed instructions, see:
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- [ISTIO_SETUP.md](ISTIO_SETUP.md)
- [architecture-diagram.md](architecture-diagram.md)
