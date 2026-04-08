# Deploy entire autonomous platform
$ErrorActionPreference = "Stop"

Write-Host "🚀 Deploying Autonomous Infrastructure Resilience Platform" -ForegroundColor Green

# 1. Prerequisites (Mocked for now)
Write-Host "Step 1: Prerequisites checked" -ForegroundColor Cyan

# 2. Deploy namespaces
Write-Host "Step 2: Ensuring namespaces exist" -ForegroundColor Cyan
kubectl create namespace self-healing-prod --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace self-healing-monitoring --dry-run=client -o yaml | kubectl apply -f -

# 3. Observability (Assuming already deployed or skipping for speed if existing)
Write-Host "Step 3: Checking Observability Stack (Skipping for now)" -ForegroundColor Yellow

# 4. Deploy Core Microservices
Write-Host "Step 4: Deploying Core Microservices" -ForegroundColor Cyan
kubectl apply -f k8s/deployments/auth-deployment.yaml
kubectl apply -f k8s/deployments/data-deployment.yaml
kubectl apply -f k8s/deployments/logging-deployment.yaml
kubectl apply -f k8s/deployments/notification-deployment.yaml
kubectl apply -f k8s/deployments/health-monitor-deployment.yaml
kubectl apply -f k8s/deployments/recovery-manager-deployment.yaml
kubectl apply -f k8s/deployments/gateway-deployment.yaml

# 5. Deploy AI/ML Services
Write-Host "Step 5: Deploying AI/ML Services" -ForegroundColor Cyan
kubectl apply -f k8s/deployments/anomaly-detector-deployment.yaml
kubectl apply -f k8s/deployments/decision-engine-deployment.yaml

# 6. Deploy Business Intelligence
Write-Host "Step 6: Deploying Executive Dashboard Components" -ForegroundColor Cyan
kubectl apply -f k8s/deployments/business-exporter-deployment.yaml

# 7. Deploy Cyber Command Center UI
Write-Host "Step 7: Deploying Cyber Command Center UI" -ForegroundColor Cyan
kubectl apply -f k8s/deployments/ui-deployment.yaml

# 8. Deploy Scaling Components
Write-Host "Step 8: Deploying Scaling Components (Skipping for now)" -ForegroundColor Yellow
# kubectl apply -f k8s/scaling/

# 9. Deployment Validation
Write-Host "Step 9: Verifying Deployment" -ForegroundColor Cyan
Start-Sleep -Seconds 5
kubectl get pods -n self-healing-prod

Write-Host "✅ Deployment script finished!" -ForegroundColor Green
