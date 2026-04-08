package com.selfhealing.recovery.controller;

import com.selfhealing.recovery.service.KubernetesRecoveryService;
import io.fabric8.kubernetes.api.model.Pod;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/recovery")
public class RecoveryController {

    @Autowired
    private KubernetesRecoveryService recoveryService;

    /**
     * Recover a failed service
     * POST /api/recovery/recover
     */
    @PostMapping("/recover")
    public ResponseEntity<Map<String, Object>> recoverService(@RequestBody Map<String, String> request) {
        String serviceName = request.get("serviceName");

        if (serviceName == null || serviceName.isEmpty()) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "serviceName is required"));
        }

        boolean success = recoveryService.recoverService(serviceName);

        Map<String, Object> response = new HashMap<>();
        response.put("serviceName", serviceName);
        response.put("success", success);
        response.put("message", success ? "Recovery initiated successfully" : "Recovery failed");
        response.put("timestamp", System.currentTimeMillis());

        return ResponseEntity.ok(response);
    }

    /**
     * Get service status
     * GET /api/recovery/status/{serviceName}
     */
    @GetMapping("/status/{serviceName}")
    public ResponseEntity<Map<String, Object>> getServiceStatus(@PathVariable String serviceName) {
        String status = recoveryService.getServiceStatus(serviceName);

        Map<String, Object> response = new HashMap<>();
        response.put("serviceName", serviceName);
        response.put("status", status);
        response.put("timestamp", System.currentTimeMillis());

        return ResponseEntity.ok(response);
    }

    /**
     * List all pods
     * GET /api/recovery/pods
     */
    @GetMapping("/pods")
    public ResponseEntity<Map<String, Object>> listPods() {
        List<Pod> pods = recoveryService.listAllPods();

        List<Map<String, String>> podInfo = pods.stream()
                .map(pod -> {
                    Map<String, String> info = new HashMap<>();
                    info.put("name", pod.getMetadata().getName());
                    info.put("phase", pod.getStatus().getPhase());
                    info.put("app", pod.getMetadata().getLabels().get("app"));
                    return info;
                })
                .collect(Collectors.toList());

        Map<String, Object> response = new HashMap<>();
        response.put("totalPods", pods.size());
        response.put("pods", podInfo);
        response.put("timestamp", System.currentTimeMillis());

        return ResponseEntity.ok(response);
    }

    /**
     * Restart a deployment
     * POST /api/recovery/restart
     */
    @PostMapping("/restart")
    public ResponseEntity<Map<String, Object>> restartDeployment(@RequestBody Map<String, String> request) {
        String deploymentName = request.get("deploymentName");

        if (deploymentName == null || deploymentName.isEmpty()) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "deploymentName is required"));
        }

        boolean success = recoveryService.restartDeployment(deploymentName);

        Map<String, Object> response = new HashMap<>();
        response.put("deploymentName", deploymentName);
        response.put("success", success);
        response.put("message", success ? "Deployment restart initiated" : "Deployment restart failed");
        response.put("timestamp", System.currentTimeMillis());

        return ResponseEntity.ok(response);
    }

    /**
     * Health check endpoint
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        return ResponseEntity.ok(Map.of(
                "status", "UP",
                "service", "recovery-manager",
                "mode", "kubernetes"));
    }
}
