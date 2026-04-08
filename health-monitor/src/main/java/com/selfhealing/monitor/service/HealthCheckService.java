package com.selfhealing.monitor.service;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;
import org.springframework.beans.factory.annotation.Value;

/**
 * TEACHER NOTE:
 * This is "The Doctor".
 * It visits every patient (service) every 5 seconds.
 */
@Service
public class HealthCheckService {

    private final RestTemplate restTemplate = new RestTemplate();

    // TEACHER NOTE:
    // We inject the configuration from application.yml
    // In Docker, these will be "http://gateway-service:..." etc.
    @Value("${monitor.target-urls}")
    private String[] services; // Spring automatically splits the comma-separated string!

    @Value("${monitor.recovery-url}")
    private String recoveryUrl;

    @Value("${monitor.gateway-url}")
    private String gatewayUrl;

    @Scheduled(fixedRate = 2000) // Faster polling for demo
    public void checkHealth() {
        // System.out.println("--- Starting Health Check ---");

        if (services == null)
            return;

        for (String url : services) {
            checkServiceBox(url);
        }
    }

    private void checkServiceBox(String url) {
        String serviceName = extractServiceName(url);
        try {
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);

            if (response.getStatusCode() == HttpStatus.OK) {
                // Only log/event if it was previously dead? For demo, maybe pulse "ALIVE" is
                // good.
                // Let's send a heartbeat event every time for the visual pulse effect.
                sendEvent("HEALTH-MONITOR", "HEARTBEAT", "Service " + serviceName + " is HEALTHY");
                // System.out.println(" HEALTHY: " + url);
            } else {
                System.out.println(" UNHEALTHY (Status " + response.getStatusCode() + "): " + url);
                sendEvent("HEALTH-MONITOR", "FAILURE_DETECTED",
                        "Service " + serviceName + " is UNHEALTHY (Status " + response.getStatusCode() + ")");
                triggerRecovery(serviceName);
            }
        } catch (Exception e) {
            System.out.println(" CRITICAL FAILURE detecting for: " + url);
            sendEvent("HEALTH-MONITOR", "CRITICAL_FAILURE",
                    "Service " + serviceName + " is DOWN! (" + e.getMessage() + ")");
            triggerRecovery(serviceName);
        }
    }

    private void triggerRecovery(String serviceName) {
        if (!serviceName.equals("unknown")) {
            System.out.println(" Calling Recovery Manager for: " + serviceName);

            // Notify Dashboard
            sendEvent("HEALTH-MONITOR", "TRIGGERING_RECOVERY", "Requesting Recovery Manager to fix " + serviceName);

            try {
                restTemplate.postForObject(recoveryUrl + "/" + serviceName, null, String.class);
            } catch (Exception recoveryError) {
                System.out.println("Failed to contact Recovery Manager: " + recoveryError.getMessage());
                sendEvent("HEALTH-MONITOR", "RECOVERY_FAILED", "Could not contact Recovery Manager!");
            }
        }
    }

    private String extractServiceName(String url) {
        if (url.contains("8081") || url.contains("auth-service"))
            return "auth-service";
        if (url.contains("8082") || url.contains("data-service"))
            return "data-service";
        return "unknown";
    }

    // New Event Class for sending JSON
    static class Event {
        public String source;
        public String type;
        public String message;

        public Event(String s, String t, String m) {
            source = s;
            type = t;
            message = m;
        }
    }

    private void sendEvent(String source, String type, String message) {
        try {
            // Gateway is at http://gateway-service:8080/api/events
            // But we need to make sure we have the URL configured.
            // For now, I'll hardcode the internal docker DNS for simplicity if config is
            // missing,
            // or use the injected value.
            String target = (gatewayUrl != null && !gatewayUrl.isEmpty()) ? gatewayUrl
                    : "http://gateway-service:8080/api/events";

            restTemplate.postForObject(target, new Event(source, type, message), String.class);
        } catch (Exception e) {
            // Silent failure if dashboard is down, don't break the monitor
            // System.err.println("Failed to send event to dashboard: " + e.getMessage());
        }
    }
}
