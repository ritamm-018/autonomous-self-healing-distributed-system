# Kubernetes Architecture Diagram - Self-Healing Distributed System

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          INTERNET / EXTERNAL USERS                          │
│                              (100k+ concurrent)                             │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 │ HTTPS (443)
                                 │
┌────────────────────────────────▼────────────────────────────────────────────┐
│                         ISTIO INGRESS GATEWAY                               │
│                    (LoadBalancer Service + TLS)                             │
│                  - Traffic Management                                       │
│                  - TLS Termination                                          │
│                  - Rate Limiting                                            │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │   ISTIO VIRTUAL SERVICE │
                    │   - Routing Rules       │
                    │   - Canary Deployments  │
                    │   - Traffic Splitting   │
                    └────────────┬────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER (self-healing-prod)                   │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      ISTIO SERVICE MESH LAYER                         │ │
│  │  - Mutual TLS (mTLS) between all services                            │ │
│  │  - Circuit Breakers & Retries                                        │ │
│  │  - Distributed Tracing (Jaeger)                                      │ │
│  │  - Metrics Collection (Prometheus)                                   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    GATEWAY SERVICE (Deployment)                     │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ... ┌──────┐                          │   │
│  │  │ Pod  │ │ Pod  │ │ Pod  │     │ Pod  │  (HPA: 3-20 replicas)   │   │
│  │  │:8080 │ │:8080 │ │:8080 │     │:8080 │                          │   │
│  │  └──────┘ └──────┘ └──────┘     └──────┘                          │   │
│  │  Resources: 500m CPU, 512Mi RAM | Limits: 1 CPU, 1Gi RAM          │   │
│  └────────────────────┬────────────────────────────────────────────────┘   │
│                       │                                                     │
│         ┌─────────────┼─────────────┐                                      │
│         │             │             │                                      │
│  ┌──────▼──────┐ ┌───▼──────┐ ┌───▼──────┐                               │
│  │AUTH SERVICE │ │   DATA   │ │  HEALTH  │                               │
│  │ (Deployment)│ │  SERVICE │ │ MONITOR  │                               │
│  │             │ │(Deployment)│(Deployment)│                              │
│  │ ┌────┐┌────┐│ │┌────┐┌────┐│ │┌────┐┌────┐│                          │
│  │ │Pod ││Pod ││ ││Pod ││Pod ││ ││Pod ││Pod ││                          │
│  │ │8081││8081││ ││8082││8082││ ││8083││8083││                          │
│  │ └────┘└────┘│ │└────┘└────┘│ │└────┘└────┘│                          │
│  │ HPA: 2-15   │ │ HPA: 3-25  │ │ HPA: 2-5   │                          │
│  │ 300m/384Mi  │ │ 500m/512Mi │ │ 200m/256Mi │                          │
│  └─────────────┘ └────────────┘ └──────┬─────┘                          │
│                                         │                                  │
│                                         │ Health Checks                    │
│                                         │ (every 5s)                       │
│                                         │                                  │
│  ┌──────────────────────────────────────▼─────────────────────────────┐   │
│  │              RECOVERY MANAGER (Deployment)                         │   │
│  │  ┌──────┐ ┌──────┐                                                │   │
│  │  │ Pod  │ │ Pod  │  (HPA: 2-5 replicas)                          │   │
│  │  │:8084 │ │:8084 │                                                │   │
│  │  └───┬──┘ └──────┘                                                │   │
│  │      │                                                             │   │
│  │      │ Kubernetes API                                             │   │
│  │      │ (Pod Restart)                                              │   │
│  │      │                                                             │   │
│  │  ┌───▼────────────────────────────────────┐                       │   │
│  │  │ ServiceAccount + RBAC                  │                       │   │
│  │  │ - pods/get, pods/list, pods/delete     │                       │   │
│  │  │ - deployments/get, deployments/patch   │                       │   │
│  │  └────────────────────────────────────────┘                       │   │
│  │  Resources: 300m CPU, 384Mi RAM                                   │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              SUPPORTING SERVICES                                    │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐                               │   │
│  │  │   LOGGING    │  │ NOTIFICATION │                               │   │
│  │  │   SERVICE    │  │   SERVICE    │                               │   │
│  │  │              │  │              │                               │   │
│  │  │ ┌────┐┌────┐ │  │ ┌────┐┌────┐ │                               │   │
│  │  │ │Pod ││Pod │ │  │ │Pod ││Pod │ │                               │   │
│  │  │ │8085││8085│ │  │ │8086││8086│ │                               │   │
│  │  │ └────┘└────┘ │  │ └────┘└────┘ │                               │   │
│  │  │ HPA: 2-10    │  │ HPA: 2-8     │                               │   │
│  │  │ 200m/512Mi   │  │ 200m/256Mi   │                               │   │
│  │  │              │  │              │                               │   │
│  │  │ ┌──────────┐ │  │              │                               │   │
│  │  │ │   PVC    │ │  │              │                               │   │
│  │  │ │ (Logs)   │ │  │              │                               │   │
│  │  │ └──────────┘ │  │              │                               │   │
│  │  └──────────────┘  └──────────────┘                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY & MONITORING STACK                         │
│                      (self-healing-monitoring namespace)                    │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                     │
│  │  PROMETHEUS  │  │   GRAFANA    │  │    JAEGER    │                     │
│  │   (Metrics)  │  │ (Dashboards) │  │  (Tracing)   │                     │
│  └──────────────┘  └──────────────┘  └──────────────┘                     │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐                                        │
│  │     KIALI    │  │ ELASTICSEARCH│                                        │
│  │(Service Mesh)│  │   (Logs)     │                                        │
│  └──────────────┘  └──────────────┘                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Namespace Structure

```
Kubernetes Cluster
│
├── self-healing-prod (Production Environment)
│   ├── gateway-service (3-20 pods)
│   ├── auth-service (2-15 pods)
│   ├── data-service (3-25 pods)
│   ├── health-monitor (2-5 pods)
│   ├── recovery-manager (2-5 pods)
│   ├── logging-service (2-10 pods)
│   └── notification-service (2-8 pods)
│
├── self-healing-staging (Staging Environment)
│   └── [Same services with reduced replicas]
│
├── self-healing-monitoring (Observability)
│   ├── prometheus
│   ├── grafana
│   ├── jaeger
│   ├── kiali
│   └── elasticsearch
│
└── istio-system (Service Mesh)
    ├── istio-ingressgateway
    ├── istiod
    └── istio-egressgateway
```

## Traffic Flow

```
1. External Request
   ↓
2. Istio Ingress Gateway (TLS Termination)
   ↓
3. Virtual Service (Routing Rules)
   ↓
4. Gateway Service (Load Balanced across pods)
   ↓
5. Internal Services (Auth, Data, etc.)
   ↓
6. Response (with Istio sidecar metrics)
```

## Self-Healing Flow

```
1. Health Monitor (polls every 5s)
   ↓
2. Detects Pod Failure
   ↓
3. Calls Recovery Manager API
   ↓
4. Recovery Manager uses Kubernetes API
   ↓
5. Deletes failed pod
   ↓
6. Kubernetes creates new pod (Deployment controller)
   ↓
7. New pod passes readiness probe
   ↓
8. Service routes traffic to new pod
   ↓
9. Notification Service alerts team
   ↓
10. Logging Service records event
```

## Istio Service Mesh Components

```
┌─────────────────────────────────────────────────────────────┐
│                    ISTIO CONTROL PLANE                      │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                      ISTIOD                          │  │
│  │  - Service Discovery                                 │  │
│  │  - Configuration Distribution                        │  │
│  │  - Certificate Management (mTLS)                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Configuration
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    DATA PLANE (Envoy Sidecars)              │
│                                                             │
│  Each Pod has an Envoy sidecar that:                       │
│  - Intercepts all network traffic                          │
│  - Enforces mTLS                                           │
│  - Collects metrics                                        │
│  - Implements circuit breakers                             │
│  - Handles retries and timeouts                            │
│  - Performs load balancing                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Autoscaling Strategy

```
┌─────────────────────────────────────────────────────────────┐
│            HORIZONTAL POD AUTOSCALER (HPA)                  │
│                                                             │
│  Metrics Monitored:                                        │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 1. CPU Utilization (Target: 70%)                    │  │
│  │ 2. Memory Utilization (Target: 80%)                 │  │
│  │ 3. Custom: HTTP Requests/sec (Optional)             │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Scaling Behavior:                                         │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Scale Up:   Add 100% pods every 15s (aggressive)    │  │
│  │ Scale Down: Remove 10% pods every 5m (conservative) │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Service-Specific Limits:                                  │
│  - Gateway: 3-20 pods                                      │
│  - Auth: 2-15 pods                                         │
│  - Data: 3-25 pods (critical service)                      │
│  - Health Monitor: 2-5 pods                                │
│  - Recovery Manager: 2-5 pods                              │
│  - Logging: 2-10 pods                                      │
│  - Notification: 2-8 pods                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Resource Allocation for 100k Users

```
┌─────────────────────────────────────────────────────────────┐
│              CLUSTER RESOURCE REQUIREMENTS                  │
│                                                             │
│  Baseline (Minimum Replicas):                              │
│  - Total Pods: ~20                                         │
│  - Total CPU: ~6 cores                                     │
│  - Total Memory: ~8 GB                                     │
│                                                             │
│  Peak Load (Maximum Replicas):                             │
│  - Total Pods: ~90                                         │
│  - Total CPU: ~50 cores                                    │
│  - Total Memory: ~60 GB                                    │
│                                                             │
│  Recommended Cluster:                                       │
│  - Nodes: 5-10 (auto-scaling node group)                  │
│  - Node Size: 8 vCPU, 16 GB RAM each                      │
│  - Total Capacity: 40-80 vCPU, 80-160 GB RAM              │
│                                                             │
│  Additional Overhead:                                       │
│  - Istio sidecars: ~10% CPU, ~50 MB RAM per pod           │
│  - Monitoring stack: 4 vCPU, 8 GB RAM                     │
│  - Kubernetes system: 2 vCPU, 4 GB RAM                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                          │
│                                                             │
│  1. Network Policies                                       │
│     - Default deny all ingress                             │
│     - Explicit allow rules per service                     │
│     - Namespace isolation                                  │
│                                                             │
│  2. RBAC (Role-Based Access Control)                       │
│     - ServiceAccounts per service                          │
│     - Least privilege principle                            │
│     - Recovery Manager: pod management only                │
│                                                             │
│  3. Pod Security Policies                                  │
│     - Run as non-root                                      │
│     - Read-only root filesystem                            │
│     - No privilege escalation                              │
│     - Drop all capabilities                                │
│                                                             │
│  4. Istio mTLS                                             │
│     - Automatic mutual TLS between services                │
│     - Certificate rotation                                 │
│     - Zero-trust networking                                │
│                                                             │
│  5. Secrets Management                                     │
│     - Kubernetes Secrets (encrypted at rest)               │
│     - External secrets operator (optional)                 │
│     - Vault integration (recommended for prod)             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                 ROLLING UPDATE STRATEGY                     │
│                                                             │
│  Configuration:                                            │
│  - maxSurge: 1 (create 1 extra pod during update)         │
│  - maxUnavailable: 0 (zero downtime)                      │
│                                                             │
│  Process:                                                  │
│  1. Create new pod with updated image                     │
│  2. Wait for readiness probe to pass                      │
│  3. Add new pod to service endpoints                      │
│  4. Remove old pod from service endpoints                 │
│  5. Terminate old pod                                     │
│  6. Repeat for next pod                                   │
│                                                             │
│  Rollback:                                                 │
│  - Automatic rollback on failure                          │
│  - Manual rollback: kubectl rollout undo                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## High Availability

```
┌─────────────────────────────────────────────────────────────┐
│              HIGH AVAILABILITY FEATURES                     │
│                                                             │
│  1. Multi-Replica Deployments                              │
│     - Minimum 2 replicas for all services                  │
│     - Spread across availability zones                     │
│                                                             │
│  2. Pod Disruption Budgets                                 │
│     - Minimum 50% pods available during disruptions        │
│     - Prevents complete service outage                     │
│                                                             │
│  3. Health Probes                                          │
│     - Liveness: Restart unhealthy pods                     │
│     - Readiness: Remove from service until healthy         │
│     - Startup: Allow slow-starting apps                    │
│                                                             │
│  4. Anti-Affinity Rules                                    │
│     - Spread pods across nodes                             │
│     - Avoid single point of failure                        │
│                                                             │
│  5. Circuit Breakers (Istio)                               │
│     - Prevent cascade failures                             │
│     - Automatic traffic rerouting                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Monitoring & Observability

```
┌─────────────────────────────────────────────────────────────┐
│                  OBSERVABILITY STACK                        │
│                                                             │
│  Metrics (Prometheus)                                      │
│  ├── Service metrics (RED: Rate, Errors, Duration)        │
│  ├── Infrastructure metrics (CPU, Memory, Disk)           │
│  ├── HPA metrics (scaling events)                         │
│  └── Custom business metrics                              │
│                                                             │
│  Dashboards (Grafana)                                      │
│  ├── Service health overview                              │
│  ├── Request latency percentiles (p50, p95, p99)          │
│  ├── Error rate trends                                    │
│  └── Resource utilization                                 │
│                                                             │
│  Tracing (Jaeger)                                          │
│  ├── Distributed request tracing                          │
│  ├── Service dependency graph                             │
│  └── Performance bottleneck identification                │
│                                                             │
│  Logs (Elasticsearch + Fluentd)                            │
│  ├── Centralized log aggregation                          │
│  ├── Structured logging                                   │
│  └── Log-based alerting                                   │
│                                                             │
│  Service Mesh Visualization (Kiali)                        │
│  ├── Real-time traffic flow                               │
│  ├── Service topology                                     │
│  └── Configuration validation                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Disaster Recovery

```
┌─────────────────────────────────────────────────────────────┐
│              DISASTER RECOVERY STRATEGY                     │
│                                                             │
│  1. Backup Strategy                                        │
│     - Velero for cluster backups                           │
│     - Daily snapshots of PVCs                              │
│     - Configuration stored in Git                          │
│                                                             │
│  2. Multi-Region Deployment (Optional)                     │
│     - Active-Active across regions                         │
│     - Global load balancer                                 │
│     - Cross-region replication                             │
│                                                             │
│  3. Recovery Time Objectives                               │
│     - RTO: < 15 minutes                                    │
│     - RPO: < 5 minutes                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
