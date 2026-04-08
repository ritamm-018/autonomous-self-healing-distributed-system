package com.selfhealing.gateway.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class Event {
    private String id;
    private String source; // e.g., "HEALTH-MONITOR", "RECOVERY-MANAGER"
    private String type; // e.g., "CRITICAL_FAILURE", "RECOVERY_STARTED"
    private String message;
    private String timestamp;

    public Event(String source, String type, String message) {
        this.id = java.util.UUID.randomUUID().toString();
        this.source = source;
        this.type = type;
        this.message = message;
        this.timestamp = LocalDateTime.now().toString();
    }
}
