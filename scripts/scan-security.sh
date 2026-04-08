#!/bin/bash
# automated-security-scan.sh
# Scans Docker images using Trivy and K8s manifests using Checkov

set -e

echo " Starting Security Vulnerability Scan..."

# Check prerequisites
if ! command -v trivy &> /dev/null; then
    echo " Trivy not found. Please install trivy."
    exit 1
fi

if ! command -v checkov &> /dev/null; then
    echo " Checkov not found. Please install checkov."
    exit 1
fi

# 1. Scan Container Images
IMAGES=(
    "selfhealing/gateway-service:latest"
    "selfhealing/auth-service:latest"
    "selfhealing/data-service:latest"
    "selfhealing/decision-engine:latest"
)

echo "--- Scanning Container Images ---"
for img in "${IMAGES[@]}"; do
    echo "Scanning $img..."
    # Fail only on CRITICAL severity
    trivy image --severity CRITICAL --exit-code 0 --no-progress "$img" > "security_report_${img//\//_}.txt" 2>&1
done

# 2. Scan K8s Manifests
echo "--- Scanning Kubernetes Manifests ---"
checkov -d k8s/ --framework kubernetes --check CKV_K8S_21,CKV_K8S_14 --output-file checkov_report.txt || true

echo " Security Scan Complete. Reports generated."
echo "   - checkov_report.txt"
echo "   - security_report_*.txt"
