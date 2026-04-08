package com.selfhealing.data.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import java.util.Arrays;
import java.util.List;
import java.util.Random;

/**
 * TEACHER NOTE:
 * This is the 'Victim'. It has endpoints designed to break things.
 * This is called "Chaos Engineering" - testing resilience by breaking things on
 * purpose.
 */
@RestController
@RequestMapping("/data")
public class DataController {

    private final Random random = new Random();

    // 1. Standard Endpoint (Happy Path)
    @GetMapping("/items")
    public List<String> getItems() {
        return Arrays.asList("Item A", "Item B", "Item C", "Item D");
    }

    // 2. Latency Injection (Delays)
    // Simulates a slow database or network.
    @GetMapping("/with-delay")
    public List<String> getItemsWithDelay() throws InterruptedException {
        int delay = 500 + random.nextInt(2000); // 0.5s to 2.5s delay
        System.out.println("Simulating lag... waiting " + delay + "ms");
        Thread.sleep(delay);
        return Arrays.asList("Delayed Item A", "Delayed Item B");
    }

    // 3. Exception Injection (Random Errors)
    // Simulates 500 Internal Server Errors.
    @GetMapping("/random-error")
    public String randomError() {
        if (random.nextBoolean()) {
            System.out.println("Simulating CRITICAL ERROR...");
            throw new RuntimeException("Chaos Monkey struck this service!");
        }
        return "You got lucky! No error this time.";
    }

    // 4. THE KILL SIGNAL (Crash the Service)
    // This is the most important one. It kills the Java process.
    // Our 'Recovery Manager' must detect this and restart Docker.
    @GetMapping("/kill")
    public void killProcess() {
        System.out.println("KILL COMMAND RECEIVED. SHUTTING DOWN...");
        System.exit(1); // Exits the JVM with error status
    }
}
