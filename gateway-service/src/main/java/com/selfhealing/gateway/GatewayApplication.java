package com.selfhealing.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * TEACHER NOTE:
 * This is the 'Main Entry Point'. Every Spring Boot application starts here.
 * The @SpringBootApplication annotation triggers a lot of "magic":
 * 1. It scans for configuration files.
 * 2. It sets up the web server (Netty).
 * 3. It links all our components together.
 */
@SpringBootApplication
public class GatewayApplication {

    public static void main(String[] args) {
        SpringApplication.run(GatewayApplication.class, args);
        System.out.println("=========================================");
        System.out.println("GATEWAY SERVICE STARTED ON PORT 8080");
        System.out.println("=========================================");
    }

}
