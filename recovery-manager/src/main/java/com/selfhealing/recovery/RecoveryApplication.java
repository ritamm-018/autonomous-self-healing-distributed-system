package com.selfhealing.recovery;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class RecoveryApplication {

    public static void main(String[] args) {
        SpringApplication.run(RecoveryApplication.class, args);
        System.out.println("=========================================");
        System.out.println("RECOVERY MANAGER STARTED ON PORT 8084");
        System.out.println("=========================================");
    }

}
