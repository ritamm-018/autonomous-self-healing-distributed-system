package com.selfhealing.gateway.controller;

import com.selfhealing.gateway.model.Event;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Sinks;

@RestController
@RequestMapping("/api/events")
@CrossOrigin(origins = "*") // Allow frontend access
public class EventController {

    // A Sink that allows multiple subscribers (multicast) to receive the same
    // events
    private final Sinks.Many<Event> eventSink;

    public EventController() {
        // replay(1) ensures new subscribers get the last event immediately (good for
        // initial state)
        // or multicast().directBestEffort() for purely live events.
        // Let's use multicast() to avoid replaying old stuff for now, or replay(10) for
        // context.
        this.eventSink = Sinks.many().multicast().onBackpressureBuffer();
    }

    /**
     * Internal services call this to publish an event.
     */
    @PostMapping
    public void publishEvent(@RequestBody Event event) {
        System.out.println("Received Event: " + event);
        // Enrich timestamp if missing
        if (event.getTimestamp() == null) {
            event.setTimestamp(java.time.LocalDateTime.now().toString());
        }
        eventSink.tryEmitNext(event);
    }

    /**
     * Frontend subscribes to this stream (Server-Sent Events).
     */
    @GetMapping(path = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<Event> streamEvents() {
        return eventSink.asFlux();
    }
}
