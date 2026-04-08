package com.selfhealing.auth.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.UUID;

/**
 * TEACHER NOTE:
 * This is a 'Controller'. It handles incoming HTTP requests.
 * We are simulating a login system.
 */
@RestController
@RequestMapping("/auth")
public class AuthController {

    // Simulates a login endpoint
    // Call this at: http://localhost:8081/auth/login or via Gateway
    // http://localhost:8080/auth/login
    @GetMapping("/login")
    public String login() {
        // In a real app, we would check username/password here.
        // For simulation, we just return a fake token.
        String token = UUID.randomUUID().toString();
        System.out.println("Login request received. Generated token: " + token);
        return "Access Granted. Token: " + token;
    }

    // A simple endpoint to check if the service is responsive
    @GetMapping("/")
    public String home() {
        return "Auth Service is running!";
    }
}
