package com.selfhealing.recovery.service;

import org.springframework.stereotype.Service;
import java.io.BufferedReader;
import java.io.InputStreamReader;

/**
 * TEACHER NOTE:
 * This is the 'Hand' that fixes the problem.
 * It uses Java's 'ProcessBuilder' to run terminal commands.
 * We will execute "docker restart <service_name>" here.
 */
@Service
public class DockerRecoveryService {

    private final org.springframework.web.client.RestTemplate restTemplate = new org.springframework.web.client.RestTemplate();

    // Gateway URL for events - hardcoded for demo or could use @Value
    private final String GATEWAY_EVENT_URL = "http://gateway-service:8080/api/events";

    public String restartContainer(String serviceName) {
        System.out.println(" ATTEMPTING TO RECOVER: " + serviceName);
        sendEvent("RECOVERY-MANAGER", "RECOVERY_STARTED", "Initiating Docker restart for container: " + serviceName);

        try {
            // TEACHER NOTE:
            // This is the actual command we would type in terminal.
            // On Windows/Mac/Linux with Docker installed, this restarts the container.
            ProcessBuilder processBuilder = new ProcessBuilder();
            processBuilder.command("docker", "restart", serviceName);

            Process process = processBuilder.start();

            // Read the output
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String line;
            StringBuilder output = new StringBuilder();
            while ((line = reader.readLine()) != null) {
                output.append(line + "\n");
            }

            int exitCode = process.waitFor();

            if (exitCode == 0) {
                System.out.println(" RECOVERY SUCCESSFUL for: " + serviceName);
                sendEvent("RECOVERY-MANAGER", "RECOVERY_COMPLETED",
                        "Successfully restarted " + serviceName + ". System healing complete.");
                return "Success: " + serviceName + " was restarted.";
            } else {
                System.err.println(" RECOVERY FAILED. Exit code: " + exitCode);
                sendEvent("RECOVERY-MANAGER", "RECOVERY_FAILED",
                        "Failed to restart " + serviceName + ". Exit code: " + exitCode);
                return "Failed to restart " + serviceName;
            }

        } catch (Exception e) {
            e.printStackTrace();
            sendEvent("RECOVERY-MANAGER", "RECOVERY_ERROR", "Error during recovery: " + e.getMessage());
            return "Error during recovery: " + e.getMessage();
        }
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
            restTemplate.postForObject(GATEWAY_EVENT_URL, new Event(source, type, message), String.class);
        } catch (Exception e) {
            // Silent failure
        }
    }
}
