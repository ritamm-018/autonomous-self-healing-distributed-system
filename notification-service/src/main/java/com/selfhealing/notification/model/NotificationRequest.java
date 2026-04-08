package com.selfhealing.notification.model;

/**
 * TEACHER NOTE:
 * This model defines what a "Call for Help" looks like.
 */
public class NotificationRequest {
    private String recipient;
    private String subject;
    private String body;

    public NotificationRequest() {
    }

    public NotificationRequest(String recipient, String subject, String body) {
        this.recipient = recipient;
        this.subject = subject;
        this.body = body;
    }

    public String getRecipient() {
        return recipient;
    }

    public void setRecipient(String recipient) {
        this.recipient = recipient;
    }

    public String getSubject() {
        return subject;
    }

    public void setSubject(String subject) {
        this.subject = subject;
    }

    public String getBody() {
        return body;
    }

    public void setBody(String body) {
        this.body = body;
    }

    @Override
    public String toString() {
        return "To: " + recipient + " | Subject: " + subject + " | Body: " + body;
    }
}
