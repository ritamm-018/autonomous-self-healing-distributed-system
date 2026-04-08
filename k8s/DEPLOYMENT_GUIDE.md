# Kubernetes Deployment Guide - Self-Healing Distributed System

## Prerequisites

### 1. Kubernetes Cluster
- **Minimum**: 3 nodes, 8 vCPU and 16GB RAM each
- **Recommended**: 5-10 nodes for production (100k users)
- **Cloud Providers**: AWS EKS, Google GKE, Azure AKS, or on-premise

### 2. Required Tools
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Install Istio
curl -L https://istio.io/downloadIstio | sh -
cd istio-*
export PATH=$PWD/bin:$PATH

# Install Helm (for monitoring stack)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### 3. Docker Images
Build and push all service images to your container registry:

```bash
# Set your registry
export REGISTRY="your-registry.com/selfhealing"

# Build all images
cd gateway-service && docker build -t $REGISTRY/gateway-service:latest . && docker push $REGISTRY/gateway-service:latest
cd ../auth-service && docker build -t $REGISTRY/auth-service:latest . && docker push $REGISTRY/auth-service:latest
cd ../data-service && docker build -t $REGISTRY/data-service:latest . && docker push $REGISTRY/data-service:latest
cd ../health-monitor && docker build -t $REGISTRY/health-monitor:latest . && docker push $REGISTRY/health-monitor:latest
cd ../recovery-manager && docker build -t $REGISTRY/recovery-manager:latest . && docker push $REGISTRY/recovery-manager:latest
cd ../logging-service && docker build -t $REGISTRY/logging-service:latest . && docker push $REGISTRY/logging-service:latest
cd ../notification-service && docker build -t $REGISTRY/notification-service:latest . && docker push $REGISTRY/notification-service:latest
```

---

## Step 1: Install Istio Service Mesh

```bash
# Install Istio with default profile
istioctl install --set profile=production -y

# Verify installation
kubectl get pods -n istio-system

# Expected output: istiod and istio-ingressgateway pods running
```

---

## Step 2: Create Namespaces

```bash
kubectl apply -f k8s/00-namespaces.yaml

# Verify
kubectl get namespaces | grep self-healing
```

---

## Step 3: Configure Secrets

**IMPORTANT**: Update secrets with real values before deploying!

```bash
# Generate JWT secret
JWT_SECRET=$(openssl rand -base64 32)

# Update secrets file
sed -i "s/CHANGE_ME_IN_PRODUCTION_USE_STRONG_SECRET_KEY_HERE/$JWT_SECRET/g" k8s/config/secrets.yaml

# Add your Slack webhook URL
sed -i "s|https://hooks.slack.com/services/YOUR/WEBHOOK/URL|YOUR_ACTUAL_WEBHOOK_URL|g" k8s/config/secrets.yaml

# Apply secrets
kubectl apply -f k8s/config/secrets.yaml
```

---

## Step 4: Deploy ConfigMaps

```bash
kubectl apply -f k8s/config/configmaps.yaml

# Verify
kubectl get configmaps -n self-healing-prod
```

---

## Step 5: Deploy All Services

```bash
# Deploy all microservices
kubectl apply -f k8s/deployments/

# Wait for all pods to be ready (this may take 3-5 minutes)
kubectl wait --for=condition=ready pod --all -n self-healing-prod --timeout=300s

# Check status
kubectl get pods -n self-healing-prod
```

Expected output:
```
NAME                                  READY   STATUS    RESTARTS   AGE
gateway-service-xxx                   2/2     Running   0          2m
auth-service-xxx                      2/2     Running   0          2m
data-service-xxx                      2/2     Running   0          2m
health-monitor-xxx                    2/2     Running   0          2m
recovery-manager-xxx                  2/2     Running   0          2m
logging-service-xxx                   2/2     Running   0          2m
notification-service-xxx              2/2     Running   0          2m
```

Note: `2/2` means main container + Istio sidecar

---

## Step 6: Deploy Istio Configurations

```bash
# Deploy Istio Gateway
kubectl apply -f k8s/istio/gateway.yaml

# Deploy VirtualServices
kubectl apply -f k8s/istio/virtual-services.yaml

# Deploy DestinationRules
kubectl apply -f k8s/istio/destination-rules.yaml

# Deploy Security Policies
kubectl apply -f k8s/istio/security-policies.yaml

# Verify
kubectl get gateway,virtualservice,destinationrule -n self-healing-prod
```

---

## Step 7: Deploy Network Policies

```bash
kubectl apply -f k8s/security/network-policies.yaml

# Verify
kubectl get networkpolicies -n self-healing-prod
```

---

## Step 8: Configure Monitoring (Optional but Recommended)

```bash
# Install Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace self-healing-monitoring \
  --create-namespace

# Deploy ServiceMonitor
kubectl apply -f k8s/monitoring/servicemonitor.yaml

# Access Grafana
kubectl port-forward -n self-healing-monitoring svc/prometheus-grafana 3000:80
# Open http://localhost:3000 (admin/prom-operator)
```

---

## Step 9: Get External IP

```bash
# Get Istio Ingress Gateway external IP
kubectl get svc istio-ingressgateway -n istio-system

# Wait for EXTERNAL-IP to be assigned
# This may take a few minutes on cloud providers
```

---

## Step 10: Configure DNS

Point your domain to the Istio Ingress Gateway external IP:

```bash
# Example DNS record
selfhealing.example.com  A  <EXTERNAL-IP>
```

---

## Step 11: Update TLS Certificates

```bash
# Create TLS secret with your certificates
kubectl create secret tls istio-ingressgateway-certs \
  --cert=path/to/cert.pem \
  --key=path/to/key.pem \
  -n istio-system

# Or use cert-manager for automatic certificates
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

---

## Step 12: Verify Deployment

### Check All Pods
```bash
kubectl get pods -n self-healing-prod
```

### Check HPA Status
```bash
kubectl get hpa -n self-healing-prod
```

### Check Services
```bash
kubectl get svc -n self-healing-prod
```

### Test External Access
```bash
# Get external IP
EXTERNAL_IP=$(kubectl get svc istio-ingressgateway -n istio-system -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test gateway
curl -k https://$EXTERNAL_IP/actuator/health
```

### View Logs
```bash
# Gateway logs
kubectl logs -f deployment/gateway-service -n self-healing-prod -c gateway

# Recovery Manager logs
kubectl logs -f deployment/recovery-manager -n self-healing-prod -c recovery-manager
```

---

## Step 13: Test Self-Healing

```bash
# Delete a pod to test recovery
kubectl delete pod -l app=data-service -n self-healing-prod --force

# Watch recovery in action
kubectl get pods -n self-healing-prod -w

# Check Recovery Manager logs
kubectl logs -f deployment/recovery-manager -n self-healing-prod
```

---

## Scaling for 100k Users

### Manual Scaling
```bash
# Scale specific service
kubectl scale deployment gateway-service --replicas=10 -n self-healing-prod
```

### Verify HPA
```bash
# HPA will automatically scale based on CPU/Memory
kubectl get hpa -n self-healing-prod -w

# Generate load to test autoscaling
kubectl run -it --rm load-generator --image=busybox --restart=Never -- /bin/sh
# Inside the pod:
while true; do wget -q -O- http://gateway-service:8080/actuator/health; done
```

---

## Monitoring & Observability

### Access Kiali (Service Mesh Dashboard)
```bash
istioctl dashboard kiali
# Opens browser to http://localhost:20001
```

### Access Jaeger (Distributed Tracing)
```bash
istioctl dashboard jaeger
```

### Access Prometheus
```bash
kubectl port-forward -n self-healing-monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Open http://localhost:9090
```

### Access Grafana
```bash
kubectl port-forward -n self-healing-monitoring svc/prometheus-grafana 3000:80
# Open http://localhost:3000
```

---

## Troubleshooting

### Pods Not Starting
```bash
# Describe pod to see events
kubectl describe pod <pod-name> -n self-healing-prod

# Check logs
kubectl logs <pod-name> -n self-healing-prod -c <container-name>
```

### Istio Sidecar Issues
```bash
# Check if sidecar is injected
kubectl get pod <pod-name> -n self-healing-prod -o jsonpath='{.spec.containers[*].name}'
# Should show: main-container,istio-proxy

# Restart pod to inject sidecar
kubectl delete pod <pod-name> -n self-healing-prod
```

### HPA Not Scaling
```bash
# Check metrics server
kubectl top nodes
kubectl top pods -n self-healing-prod

# If metrics not available, install metrics-server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### Network Policy Issues
```bash
# Temporarily disable to test
kubectl delete networkpolicy --all -n self-healing-prod

# Re-enable after testing
kubectl apply -f k8s/security/network-policies.yaml
```

---

## Rollback

If something goes wrong:

```bash
# Rollback a deployment
kubectl rollout undo deployment/gateway-service -n self-healing-prod

# Check rollout history
kubectl rollout history deployment/gateway-service -n self-healing-prod

# Rollback to specific revision
kubectl rollout undo deployment/gateway-service --to-revision=2 -n self-healing-prod
```

---

## Cleanup

To remove everything:

```bash
# Delete all resources
kubectl delete namespace self-healing-prod
kubectl delete namespace self-healing-staging
kubectl delete namespace self-healing-monitoring

# Uninstall Istio
istioctl uninstall --purge -y
kubectl delete namespace istio-system
```

---

## Production Checklist

- [ ] All secrets updated with real values
- [ ] TLS certificates configured
- [ ] DNS records pointing to external IP
- [ ] Monitoring stack deployed
- [ ] Backup strategy in place (Velero)
- [ ] Resource quotas configured
- [ ] Network policies tested
- [ ] Load testing completed
- [ ] Disaster recovery plan documented
- [ ] Team trained on kubectl and monitoring tools

---

## Next Steps

1. **Load Testing**: Use k6 or Gatling to simulate 100k users
2. **Chaos Engineering**: Use Chaos Mesh to test resilience
3. **CI/CD**: Set up GitOps with ArgoCD or Flux
4. **Multi-Region**: Deploy to multiple regions for HA
5. **Cost Optimization**: Configure cluster autoscaler

---

## Support

For issues or questions:
- Check logs: `kubectl logs -f deployment/<service-name> -n self-healing-prod`
- View events: `kubectl get events -n self-healing-prod --sort-by='.lastTimestamp'`
- Describe resources: `kubectl describe <resource-type> <resource-name> -n self-healing-prod`
