# Multi-Cloud Deployment Guide

## Overview
The Autonomous Self-Healing System supports **write once, deploy anywhere**. We use Terraform to abstract the underlying cloud provider (AWS, Azure, GCP) and deliver a standardized Kubernetes environment.

## Prerequisites
1.  **Terraform** (v1.0+)
2.  **Cloud CLI Tools**:
    *   `aws` CLI (for AWS)
    *   `az` CLI (for Azure)
    *   `gcloud` CLI (for GCP)
3.  **kubectl**

## Directory Structure
```
terraform/
├── main.tf          # Unified entry point
├── modules/
│   ├── aws/         # EKS implementation
│   ├── azure/       # AKS implementation
│   └── gcp/         # GKE implementation
```

## How to Deploy

### 1. Configure Credentials
Ensure you are logged in to your target cloud:
```bash
# AWS
aws configure

# Azure
az login

# GCP
gcloud auth login
```

### 2. Run Deployment Script
Use the unified script to provision infrastructure and deploy the application stack:

**Deploy to AWS:**
```bash
./scripts/deploy-platform.sh --cloud aws --action apply
```

**Deploy to Azure:**
```bash
./scripts/deploy-platform.sh --cloud azure --action apply
```

**Deploy to GCP:**
```bash
./scripts/deploy-platform.sh --cloud gcp --action apply
```

## Infrastructure Details

### AWS (EKS)
*   **VPC**: Public/Private subnets across 3 AZs.
*   **Cluster**: Managed EKS (v1.27) with OIDC.
*   **Nodes**: Managed Node Group (t3.medium, auto-scaling 1-5 nodes).

### Azure (AKS)
*   **Network**: Kubenet networking with Load Balancer SKU Standard.
*   **Cluster**: Managed AKS with System-Assigned Identity.
*   **Nodes**: Standard_DS2_v2 instances.

### GCP (GKE)
*   **Network**: VPC native cluster.
*   **Cluster**: Regional GKE cluster.
*   **Nodes**: Preemptible e2-medium nodes for cost optimization.

## Teardown
To destroy all resources and stop billing:
```bash
./scripts/deploy-platform.sh --cloud <provider> --action destroy
```
