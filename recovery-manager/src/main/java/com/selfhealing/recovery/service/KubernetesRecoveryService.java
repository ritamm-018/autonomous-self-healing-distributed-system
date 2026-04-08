package com.selfhealing.recovery.service;

import io.fabric8.kubernetes.api.model.Pod;
import io.fabric8.kubernetes.client.KubernetesClient;
import io.fabric8.kubernetes.client.KubernetesClientBuilder;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;

@Service
public class KubernetesRecoveryService {

    private static final Logger logger = LoggerFactory.getLogger(KubernetesRecoveryService.class);

    private final KubernetesClient kubernetesClient;
    private final String namespace;

    public KubernetesRecoveryService(@Value("${kubernetes.namespace:self-healing-prod}") String namespace) {
        this.namespace = namespace;
        // Initialize Kubernetes client - automatically uses in-cluster config
        this.kubernetesClient = new KubernetesClientBuilder().build();
        logger.info("Kubernetes Recovery Service initialized for namespace: {}", namespace);
    }

    /**
     * Recover a failed service by deleting the unhealthy pod
     * Kubernetes Deployment controller will automatically create a new pod
     */
    public boolean recoverService(String serviceName) {
        try {
            logger.info("Starting recovery for service: {}", serviceName);

            // Find pods for the service
            List<Pod> pods = kubernetesClient.pods()
                    .inNamespace(namespace)
                    .withLabel("app", serviceName)
                    .list()
                    .getItems();

            if (pods.isEmpty()) {
                logger.warn("No pods found for service: {}", serviceName);
                return false;
            }

            // Find unhealthy pods
            for (Pod pod : pods) {
                String podName = pod.getMetadata().getName();
                String phase = pod.getStatus().getPhase();

                logger.info("Checking pod: {} - Phase: {}", podName, phase);

                // Delete pod if it's not running or ready
                if (!"Running".equals(phase) || !isPodReady(pod)) {
                    logger.warn("Pod {} is unhealthy (Phase: {}). Deleting...", podName, phase);

                    kubernetesClient.pods()
                            .inNamespace(namespace)
                            .withName(podName)
                            .delete();

                    logger.info("Successfully deleted pod: {}. Kubernetes will create a new pod.", podName);

                    // Create event for audit trail
                    createRecoveryEvent(serviceName, podName);

                    return true;
                }
            }

            logger.info("All pods for service {} are healthy. No recovery needed.", serviceName);
            return true;

        } catch (Exception e) {
            logger.error("Error recovering service {}: {}", serviceName, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Check if a pod is ready
     */
    private boolean isPodReady(Pod pod) {
        if (pod.getStatus() == null || pod.getStatus().getConditions() == null) {
            return false;
        }

        return pod.getStatus().getConditions().stream()
                .anyMatch(condition -> "Ready".equals(condition.getType()) &&
                        "True".equals(condition.getStatus()));
    }

    /**
     * Create a Kubernetes event for recovery action
     */
    private void createRecoveryEvent(String serviceName, String podName) {
        try {
            logger.info("Creating recovery event for service: {}, pod: {}", serviceName, podName);
            // Event creation logic here if needed
        } catch (Exception e) {
            logger.error("Failed to create recovery event: {}", e.getMessage());
        }
    }

    /**
     * Get pod status for a service
     */
    public String getServiceStatus(String serviceName) {
        try {
            List<Pod> pods = kubernetesClient.pods()
                    .inNamespace(namespace)
                    .withLabel("app", serviceName)
                    .list()
                    .getItems();

            if (pods.isEmpty()) {
                return "NO_PODS";
            }

            long runningPods = pods.stream()
                    .filter(pod -> "Running".equals(pod.getStatus().getPhase()))
                    .filter(this::isPodReady)
                    .count();

            if (runningPods == pods.size()) {
                return "HEALTHY";
            } else if (runningPods > 0) {
                return "DEGRADED";
            } else {
                return "DOWN";
            }

        } catch (Exception e) {
            logger.error("Error getting service status: {}", e.getMessage());
            return "UNKNOWN";
        }
    }

    /**
     * List all pods in the namespace
     */
    public List<Pod> listAllPods() {
        return kubernetesClient.pods()
                .inNamespace(namespace)
                .list()
                .getItems();
    }

    /**
     * Restart a deployment (alternative recovery method)
     */
    public boolean restartDeployment(String deploymentName) {
        try {
            logger.info("Restarting deployment: {}", deploymentName);

            // Trigger a rollout restart by updating an annotation
            kubernetesClient.apps().deployments()
                    .inNamespace(namespace)
                    .withName(deploymentName)
                    .rolling()
                    .restart();

            logger.info("Successfully triggered restart for deployment: {}", deploymentName);
            return true;

        } catch (Exception e) {
            logger.error("Error restarting deployment {}: {}", deploymentName, e.getMessage(), e);
            return false;
        }
    }
}
