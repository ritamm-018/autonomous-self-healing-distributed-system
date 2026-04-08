package com.selfhealing.logging;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class LoggingApplication {

    public static void main(String[] args) {
        SpringApplication.run(LoggingApplication.class, args);
        System.out.println("=========================================");
        System.out.println("LOGGING SERVICE STARTED ON PORT 8085");
        System.out.println("=========================================");
    }

}
