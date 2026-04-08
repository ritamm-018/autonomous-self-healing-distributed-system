package com.selfhealing.monitor;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * TEACHER NOTE:
 * We add @EnableScheduling here.
 * This tells Spring Boot: "Look for any method marked with @Scheduled and run
 * it automatically."
 * Without this, our health checks would never run.
 */
@SpringBootApplication
@EnableScheduling
public class HealthMonitorApplication {

    public static void main(String[] args) {
        SpringApplication.run(HealthMonitorApplication.class, args);
        System.out.println("=========================================");
        System.out.println("HEALTH MONITOR STARTED ON PORT 8083");
        System.out.println("=========================================");
    }

}
