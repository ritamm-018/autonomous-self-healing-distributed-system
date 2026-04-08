package com.selfhealing.notification;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class NotificationApplication {

    public static void main(String[] args) {
        SpringApplication.run(NotificationApplication.class, args);
        System.out.println("=========================================");
        System.out.println("NOTIFICATION SERVICE STARTED ON PORT 8086");
        System.out.println("=========================================");
    }

}
