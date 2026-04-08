package com.selfhealing.common.tracing;

import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.trace.propagation.W3CTraceContextPropagator;
import io.opentelemetry.context.propagation.ContextPropagators;
import io.opentelemetry.exporter.jaeger.JaegerGrpcSpanExporter;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.resources.Resource;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.BatchSpanProcessor;
import io.opentelemetry.sdk.trace.samplers.Sampler;
import io.opentelemetry.semconv.resource.attributes.ResourceAttributes;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * OpenTelemetry configuration for distributed tracing
 */
@Configuration
public class TracingConfiguration implements WebMvcConfigurer {

    @Value("${spring.application.name}")
    private String serviceName;

    @Value("${otel.exporter.jaeger.endpoint:http://jaeger-collector.self-healing-monitoring:14250}")
    private String jaegerEndpoint;

    @Value("${otel.traces.sampler.probability:0.1}")
    private double samplingProbability;

    @Bean
    public OpenTelemetry openTelemetry() {
        // Create resource with service name
        Resource resource = Resource.getDefault()
                .merge(Resource.create(
                        Attributes.of(
                                ResourceAttributes.SERVICE_NAME, serviceName,
                                ResourceAttributes.SERVICE_NAMESPACE, "self-healing-prod",
                                ResourceAttributes.SERVICE_VERSION, "1.0.0")));

        // Configure Jaeger exporter
        JaegerGrpcSpanExporter jaegerExporter = JaegerGrpcSpanExporter.builder()
                .setEndpoint(jaegerEndpoint)
                .build();

        // Configure tracer provider
        SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
                .setResource(resource)
                .addSpanProcessor(BatchSpanProcessor.builder(jaegerExporter).build())
                .setSampler(Sampler.traceIdRatioBased(samplingProbability))
                .build();

        // Build OpenTelemetry SDK
        return OpenTelemetrySdk.builder()
                .setTracerProvider(tracerProvider)
                .setPropagators(ContextPropagators.create(
                        W3CTraceContextPropagator.getInstance()))
                .buildAndRegisterGlobal();
    }

    @Bean
    public TracingInterceptor tracingInterceptor(OpenTelemetry openTelemetry) {
        return new TracingInterceptor(openTelemetry);
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(tracingInterceptor(openTelemetry()));
    }
}
