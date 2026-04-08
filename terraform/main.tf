terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

variable "cloud_provider" {
  description = "Target Cloud Provider (aws, azure, gcp)"
  type        = string
}

# AWS Module
module "aws_cluster" {
  source = "./modules/aws"
  count  = var.cloud_provider == "aws" ? 1 : 0
  
  region       = "us-east-1"
  cluster_name = "autonomous-aws"
}

# Azure Module
module "azure_cluster" {
  source = "./modules/azure"
  count  = var.cloud_provider == "azure" ? 1 : 0
  
  location     = "East US"
  cluster_name = "autonomous-azure"
}

# GCP Module
module "gcp_cluster" {
  source = "./modules/gcp"
  count  = var.cloud_provider == "gcp" ? 1 : 0
  
  project_id   = "my-gcp-project-id" # user would replace this
  region       = "us-central1"
  cluster_name = "autonomous-gcp"
}

output "aws_kubeconfig" {
  value = length(module.aws_cluster) > 0 ? module.aws_cluster[0].kubectl_config : null
}

output "azure_kubeconfig" {
  value     = length(module.azure_cluster) > 0 ? module.azure_cluster[0].kube_config : null
  sensitive = true
}

output "gcp_command" {
  value = length(module.gcp_cluster) > 0 ? module.gcp_cluster[0].kube_config : null
}
