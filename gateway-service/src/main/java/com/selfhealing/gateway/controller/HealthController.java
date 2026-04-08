package com.selfhealing.gateway.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * HEALTH CONTROLLER
 * 
 * WHAT IS THIS?
 * Provides a simple health check endpoint.
 * Other services (like Health Monitor) call this to check if Gateway is alive.
 * 
 * WHY DO WE NEED THIS?
 * - Health Monitor needs to know if Gateway is running
 * - Load balancers check health before routing traffic
 * - Monitoring systems track service availability
 * 
 * REAL-WORLD USAGE:
 * Kubernetes uses health checks to decide if a pod is ready to receive traffic.
 * If health check fails, Kubernetes restarts the pod.
 */
@RestController
@RequestMapping("/health")
public class HealthController {

    private static final Logger logger = LoggerFactory.getLogger(HealthController.class);
    
    /**
     * SIMPLE HEALTH CHECK
     * Returns a simple "OK" status
     * 
     * Try it: http://localhost:8080/health
     */
    @GetMapping
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> health = new HashMap<>();
        health.put("status", "UP");
        health.put("service", "gateway-service");
        health.put("timestamp", LocalDateTime.now().toString());
        health.put("message", "Gateway service is running");
        
        logger.debug("Health check requested - service is UP");
        
        return ResponseEntity.ok(health);
    }
}
