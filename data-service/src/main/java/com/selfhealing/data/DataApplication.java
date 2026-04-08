package com.selfhealing.data;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class DataApplication {

    public static void main(String[] args) {
        SpringApplication.run(DataApplication.class, args);
        System.out.println("=========================================");
        System.out.println("DATA SERVICE STARTED ON PORT 8082");
        System.out.println("=========================================");
    }

}
