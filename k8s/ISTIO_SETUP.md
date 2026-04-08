# Istio Installation and Configuration Guide

## Overview

This guide covers installing Istio service mesh for the self-healing distributed system.

## Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Cluster admin permissions
- Minimum 8GB RAM available

## Step 1: Download Istio

```bash
# Download latest Istio
curl -L https://istio.io/downloadIstio | sh -

# Move to Istio directory
cd istio-*

# Add istioctl to PATH
export PATH=$PWD/bin:$PATH

# Verify installation
istioctl version
```

## Step 2: Install Istio

### Production Profile (Recommended)

```bash
# Install with production profile
istioctl install --set profile=production -y
```

This installs:
- **istiod**: Control plane for service mesh
- **istio-ingressgateway**: Entry point for external traffic
- **istio-egressgateway**: Exit point for external traffic

### Verify Installation

```bash
# Check Istio pods
kubectl get pods -n istio-system

# Expected output:
# NAME                                    READY   STATUS    RESTARTS   AGE
# istio-ingressgateway-xxx                1/1     Running   0          2m
# istio-egressgateway-xxx                 1/1     Running   0          2m
# istiod-xxx                              1/1     Running   0          2m
```

## Step 3: Enable Sidecar Injection

Automatic sidecar injection is already enabled via namespace label in `00-namespaces.yaml`:

```yaml
labels:
  istio-injection: enabled
```

Verify:
```bash
kubectl get namespace self-healing-prod --show-labels
```

## Step 4: Configure Istio Components

### Install Kiali (Service Mesh Dashboard)

```bash
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/kiali.yaml

# Wait for Kiali to be ready
kubectl wait --for=condition=available --timeout=300s deployment/kiali -n istio-system
```

### Install Jaeger (Distributed Tracing)

```bash
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/jaeger.yaml
```

### Install Prometheus (Metrics)

```bash
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/prometheus.yaml
```

### Install Grafana (Dashboards)

```bash
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/grafana.yaml
```

## Step 5: Configure Istio for Production

### Increase Resource Limits

```bash
kubectl patch deployment istiod -n istio-system --type='json' -p='[
  {
    "op": "replace",
    "path": "/spec/template/spec/containers/0/resources/requests/cpu",
    "value": "500m"
  },
  {
    "op": "replace",
    "path": "/spec/template/spec/containers/0/resources/requests/memory",
    "value": "2Gi"
  }
]'
```

### Enable Access Logging (Optional)

```bash
istioctl install --set profile=production \
  --set meshConfig.accessLogFile=/dev/stdout \
  -y
```

## Step 6: Verify Service Mesh

### Check Istio Configuration

```bash
istioctl analyze -n self-healing-prod
```

### Verify mTLS

```bash
# Check peer authentication
kubectl get peerauthentication -n self-healing-prod

# Verify mTLS status
istioctl authn tls-check <pod-name>.<namespace>
```

## Step 7: Access Dashboards

### Kiali (Service Mesh Visualization)

```bash
istioctl dashboard kiali
```

Features:
- Service topology graph
- Traffic flow visualization
- Configuration validation
- Health monitoring

### Jaeger (Distributed Tracing)

```bash
istioctl dashboard jaeger
```

Features:
- Request tracing across services
- Latency analysis
- Dependency graphs

### Grafana (Metrics Dashboards)

```bash
istioctl dashboard grafana
```

Pre-built dashboards:
- Istio Service Dashboard
- Istio Workload Dashboard
- Istio Performance Dashboard
- Istio Control Plane Dashboard

### Prometheus (Metrics)

```bash
istioctl dashboard prometheus
```

## Step 8: Configure Traffic Management

All traffic management configs are in `k8s/istio/`:

```bash
# Apply Gateway
kubectl apply -f k8s/istio/gateway.yaml

# Apply VirtualServices
kubectl apply -f k8s/istio/virtual-services.yaml

# Apply DestinationRules
kubectl apply -f k8s/istio/destination-rules.yaml

# Apply Security Policies
kubectl apply -f k8s/istio/security-policies.yaml
```

## Step 9: Test Service Mesh

### Verify Sidecar Injection

```bash
# Deploy a test pod
kubectl run test-pod --image=nginx -n self-healing-prod

# Check containers (should have 2: nginx + istio-proxy)
kubectl get pod test-pod -n self-healing-prod -o jsonpath='{.spec.containers[*].name}'

# Cleanup
kubectl delete pod test-pod -n self-healing-prod
```

### Test mTLS

```bash
# From inside a pod
kubectl exec -it <pod-name> -n self-healing-prod -c <container-name> -- curl http://gateway-service:8080/actuator/health

# Should work because mTLS is automatic
```

## Step 10: Monitor Service Mesh Health

```bash
# Check Istio proxy status
istioctl proxy-status

# View Istio configuration
istioctl proxy-config cluster <pod-name> -n self-healing-prod

# Check for configuration issues
istioctl analyze --all-namespaces
```

## Troubleshooting

### Sidecar Not Injected

```bash
# Check namespace label
kubectl get namespace self-healing-prod --show-labels

# If missing, add label
kubectl label namespace self-healing-prod istio-injection=enabled

# Restart pods
kubectl rollout restart deployment -n self-healing-prod
```

### mTLS Issues

```bash
# Check peer authentication
kubectl get peerauthentication -n self-healing-prod

# Verify TLS mode
istioctl authn tls-check <pod-name>.<namespace>

# Check for conflicting policies
kubectl get peerauthentication,destinationrule --all-namespaces
```

### High Latency

```bash
# Check Envoy stats
istioctl dashboard envoy <pod-name>.<namespace>

# View circuit breaker stats
istioctl proxy-config cluster <pod-name> -n self-healing-prod --fqdn <service-name>
```

### Gateway Not Working

```bash
# Check gateway status
kubectl get gateway -n self-healing-prod

# Describe gateway
kubectl describe gateway self-healing-gateway -n self-healing-prod

# Check ingress gateway logs
kubectl logs -n istio-system -l app=istio-ingressgateway
```

## Advanced Configuration

### Custom Istio Profile

Create `istio-config.yaml`:

```yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  profile: production
  meshConfig:
    accessLogFile: /dev/stdout
    enableTracing: true
    defaultConfig:
      tracing:
        sampling: 100.0
  components:
    ingressGateways:
    - name: istio-ingressgateway
      enabled: true
      k8s:
        resources:
          requests:
            cpu: 1000m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 2Gi
        hpaSpec:
          minReplicas: 2
          maxReplicas: 10
```

Apply:
```bash
istioctl install -f istio-config.yaml -y
```

### Enable Telemetry v2

```bash
istioctl install --set profile=production \
  --set values.telemetry.v2.enabled=true \
  -y
```

## Upgrade Istio

```bash
# Download new version
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.0 sh -

# Check upgrade compatibility
istioctl x precheck

# Perform canary upgrade
istioctl upgrade --set profile=production

# Verify upgrade
istioctl version
```

## Uninstall Istio

```bash
# Remove Istio
istioctl uninstall --purge -y

# Delete namespace
kubectl delete namespace istio-system

# Remove CRDs
kubectl get crd -o name | grep --color=never 'istio.io' | xargs kubectl delete
```

## Production Checklist

- [ ] Istio installed with production profile
- [ ] Resource limits configured
- [ ] Kiali, Jaeger, Prometheus, Grafana deployed
- [ ] Sidecar injection verified
- [ ] mTLS enabled and tested
- [ ] Gateway configured with TLS
- [ ] VirtualServices and DestinationRules applied
- [ ] Circuit breakers configured
- [ ] Monitoring dashboards accessible
- [ ] Team trained on Istio tools

## References

- [Istio Documentation](https://istio.io/latest/docs/)
- [Istio Best Practices](https://istio.io/latest/docs/ops/best-practices/)
- [Kiali Documentation](https://kiali.io/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
