#!/bin/bash
# Multi-Cloud Deployment Script
# Usage: ./deploy-platform.sh --cloud <aws|azure|gcp> --action <apply|destroy>

set -e

CLOUD=""
ACTION=""

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --cloud) CLOUD="$2"; shift ;;
        --action) ACTION="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

if [[ -z "$CLOUD" || -z "$ACTION" ]]; then
    echo "Usage: ./deploy-platform.sh --cloud <aws|azure|gcp> --action <apply|destroy>"
    exit 1
fi

echo " Starting ${ACTION} for ${CLOUD} infrastructure..."

cd terraform

# Initialize Terraform
terraform init

# Apply or Destroy
if [[ "$ACTION" == "apply" ]]; then
    echo "Creating Kubernetes Cluster on ${CLOUD}..."
    terraform apply -var="cloud_provider=${CLOUD}" -auto-approve
    
    # Configure kubectl based on output
    if [[ "$CLOUD" == "aws" ]]; then
        aws eks update-kubeconfig --name autonomous-aws --region us-east-1
    elif [[ "$CLOUD" == "azure" ]]; then
        az aks get-credentials --resource-group autonomous-azure-rg --name autonomous-azure
    elif [[ "$CLOUD" == "gcp" ]]; then
        gcloud container clusters get-credentials autonomous-gcp --region us-central1
    fi
    
    echo " Infrastructure Ready!"
    echo "deploying Application Stack..."
    
    cd ..
    ./scripts/deploy-all.sh
    
elif [[ "$ACTION" == "destroy" ]]; then
    echo "  Destroying all resources on ${CLOUD}..."
    terraform destroy -var="cloud_provider=${CLOUD}" -auto-approve
    echo " Infrastructure destroyed."
fi
