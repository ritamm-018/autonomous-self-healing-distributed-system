variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "cluster_name" {
  description = "GKE Cluster Name"
  type        = string
  default     = "self-healing-cluster"
}

variable "machine_type" {
  description = "Node Machine Type"
  type        = string
  default     = "e2-medium"
}

variable "node_count" {
  description = "Nodes per zone"
  type        = number
  default     = 1
}
