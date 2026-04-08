package com.selfhealing.auth;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class AuthApplication {

    public static void main(String[] args) {
        SpringApplication.run(AuthApplication.class, args);
        System.out.println("=========================================");
        System.out.println("AUTH SERVICE STARTED ON PORT 8081");
        System.out.println("=========================================");
    }

}
