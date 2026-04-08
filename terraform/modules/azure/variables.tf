variable "location" {
  description = "Azure Region"
  type        = string
  default     = "East US"
}

variable "cluster_name" {
  description = "AKS Cluster Name"
  type        = string
  default     = "self-healing-cluster"
}

variable "node_vm_size" {
  description = "Example: Standard_DS2_v2"
  type        = string
  default     = "Standard_DS2_v2"
}

variable "node_count" {
  description = "Number of worker nodes"
  type        = number
  default     = 3
}
