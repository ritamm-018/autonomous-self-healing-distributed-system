package com.selfhealing.logging.controller;

import com.selfhealing.logging.model.LogEntry;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/logs")
public class LoggingController {

    @PostMapping
    public String ingestLog(@RequestBody LogEntry entry) {
        // In a real system, we would save this to a database or file.
        // For now, we print it to the console so we can see it happening.
        System.out.println(" LOG RECEIVED: " + entry.toString());
        return "Log received";
    }
}
