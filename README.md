#  Autonomous Self-Healing Distributed System

> **A Production-Grade Microservices Architecture that detects its own failures and fixes them automatically.**

![Status](https://img.shields.io/badge/Status-Complete-green)
![Tech](https://img.shields.io/badge/Stack-Java%20%7C%20Python%20%7C%20K8s%20%7C%20React-blue)

##  Project Overview
This is not just a set of microservices; it is a **Self-Driving Infrastructure**.
The system continuously monitors itself using Prometheus & AI, detects anomalies (like high latency or service crashes), and autonomously performs recovery actions (scaling, restarting, rolling back) via Kubernetes APIs.

It features a **3D Cyber Command Center** for real-time visualization and an **Executive Dashboard** for business metrics.

---

##  Architecture

### The "Brain" (Control Plane)
1.  **Anomaly Detector**: ML models (Isolation Forest) analyzing real-time metrics.
2.  **Decision Engine**: Reinforcement Learning agent selecting the best recovery strategy.
3.  **Recovery Manager**: Executes `kubectl` commands to heal the cluster.

### The "Body" (Data Plane)
*   **7 Microservices**: Gateway, Auth, Data, Logging, Notification, etc. (Java Spring Boot).
*   **Service Mesh**: Istio for mTLS, Traffic Splitting, and Circuit Breaking.

### The "Face" (Frontend)
*   **Cyber Command Center**: React + Three.js 3D Dashboard.
*   **Executive Dashboard**: Grafana panels for ROI and SLA tracking.

---

##  How to Run

### Prerequisites
1.  **Docker Desktop**: Enable **Kubernetes** in settings.
2.  **Kubectl**: Installed and configured to point to Docker Desktop (`kubectl config use-context docker-desktop`).
3.  **Python 3.9+**: For AI services and scripts.
4.  **Git Bash / WSL**: To run automation scripts on Windows.

### Step 1: Deployment 
We have a master script that deploys everything (Namespaces, Databases, Apps, UI, Monitoring).

```bash
# Open Git Bash or WSL
./scripts/deploy-all.sh
```
*This may take 5-10 minutes to pull images and start all pods.*

### Step 2: Accessing the System 

####  Cyber Command Center (3D UI)
The UI runs on Port 80 inside the cluster.
```bash
# Port Forward to localhost
kubectl port-forward svc/cyber-command-center 3000:80 -n self-healing-prod
```
> **Open**: [http://localhost:3000](http://localhost:3000)

####  Grafana Dashboards
```bash
# Port Forward Prometheus/Grafana stack
kubectl port-forward svc/prometheus-grafana 3001:80 -n self-healing-monitoring
```
> **Open**: [http://localhost:3001](http://localhost:3001) (User: `admin`, Pass: `prom-operator`) or similar default.

####  API Gateway
```bash
kubectl port-forward svc/gateway-service 8080:8080 -n self-healing-prod
```
> **Health Check**: [http://localhost:8080/actuator/health](http://localhost:8080/actuator/health)

---

##  Running Scenarios

### Option A: Via Command Center UI
1.  Navigate to [http://localhost:3000](http://localhost:3000).
2.  Click the **"SIMULATE ATTACK"** button in the HUD.
3.  Watch the 3D nodes turn RED and then GREEN as the system heals itself.

### Option B: Manual Chaos
Kill a pod manually and watch the logs:
```bash
kubectl delete pod -l app=auth-service -n self-healing-prod
```
*The Recovery Manager will detect the drop in `Ready` pods and restart it immediately.*

---

##  Project Structure
*   `k8s/`: All Kubernetes manifests (Deployments, Services, Istio Configs).
*   `terraform/`: Infrastructure as Code for AWS, Azure, GCP.
*   `ui/`: React Three Fiber frontend application.
*   `scripts/`: Automation scripts (`deploy-all.sh`, `scan-security.sh`).
*   `anomaly-detector/`: Python-based AI service.
