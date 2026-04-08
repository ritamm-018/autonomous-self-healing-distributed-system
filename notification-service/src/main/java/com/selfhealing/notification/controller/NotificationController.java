package com.selfhealing.notification.controller;

import com.selfhealing.notification.model.NotificationRequest;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/notify")
public class NotificationController {

    @PostMapping("/send")
    public String sendNotification(@RequestBody NotificationRequest request) {
        // TEACHER NOTE:
        // In a real production app, we would use JavaMailSender here to actually send
        // an email.
        // Or call the Slack API.
        // For this demo, we will simulate it by printing a "LOUD" message to the logs.

        System.out.println("\n\n#############################################################");
        System.out.println("    INCIDENT ALERT SENT    ");
        System.out.println("-------------------------------------------------------------");
        System.out.println(request.toString());
        System.out.println("#############################################################\n\n");

        return "Notification sent successfully";
    }
}
