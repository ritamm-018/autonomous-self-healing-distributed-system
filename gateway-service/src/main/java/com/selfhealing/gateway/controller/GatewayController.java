package com.selfhealing.gateway.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

/**
 * GATEWAY CONTROLLER
 * 
 * TEACHER NOTE:
 * This controller provides a simple "Home Page" for our Gateway.
 * The actual ROUTING (forwarding traffic) is handled by Spring Cloud Gateway
 * configuration in 'application.yml'.
 * 
 * We use 'Mono<String>' here because Gateway is built on "Reactive" Java
 * (WebFlux).
 */
@RestController
@RequestMapping("/api")
public class GatewayController {

    @GetMapping
    public Mono<String> welcome() {
        return Mono.just("""
                {
                    "service": "Gateway Service",
                    "status": "active",
                    "message": "Welcome to the Self-Healing System Gateway. Routing is active.",
                    "routes": {
                        "auth": "/auth/**",
                        "data": "/data/**"
                    }
                }
                """);
    }
}
