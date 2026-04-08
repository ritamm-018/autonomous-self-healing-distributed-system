package com.selfhealing.logging.model;

import java.time.LocalDateTime;

/**
 * TEACHER NOTE:
 * A 'Model' is just a container for data.
 * This class represents one line in our log book.
 */
public class LogEntry {
    private String serviceName;
    private String message;
    private String level; // INFO, ERROR, WARN
    private LocalDateTime timestamp;

    public LogEntry() {
        this.timestamp = LocalDateTime.now();
    }

    public LogEntry(String serviceName, String message, String level) {
        this.serviceName = serviceName;
        this.message = message;
        this.level = level;
        this.timestamp = LocalDateTime.now();
    }

    public String getServiceName() {
        return serviceName;
    }

    public void setServiceName(String serviceName) {
        this.serviceName = serviceName;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public String getLevel() {
        return level;
    }

    public void setLevel(String level) {
        this.level = level;
    }

    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(LocalDateTime timestamp) {
        this.timestamp = timestamp;
    }

    @Override
    public String toString() {
        return "[" + timestamp + "] [" + level + "] [" + serviceName + "]: " + message;
    }
}
