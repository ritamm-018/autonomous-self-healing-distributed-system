package com.selfhealing.common.tracing;

import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.SpanKind;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Context;
import io.opentelemetry.context.Scope;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/**
 * HTTP interceptor for distributed tracing
 * Automatically creates spans for HTTP requests
 */
@Component
public class TracingInterceptor implements HandlerInterceptor {

    private final Tracer tracer;

    public TracingInterceptor(OpenTelemetry openTelemetry) {
        this.tracer = openTelemetry.getTracer("self-healing-system", "1.0.0");
    }

    @Override
    public boolean preHandle(HttpServletRequest request,
            HttpServletResponse response,
            Object handler) {
        // Create span for this request
        Span span = tracer.spanBuilder("HTTP " + request.getMethod())
                .setSpanKind(SpanKind.SERVER)
                .startSpan();

        // Add attributes
        span.setAttribute("http.method", request.getMethod());
        span.setAttribute("http.url", request.getRequestURI());
        span.setAttribute("http.scheme", request.getScheme());
        span.setAttribute("http.host", request.getServerName());

        // Add query parameters
        if (request.getQueryString() != null) {
            span.setAttribute("http.query", request.getQueryString());
        }

        // Add user agent
        String userAgent = request.getHeader("User-Agent");
        if (userAgent != null) {
            span.setAttribute("http.user_agent", userAgent);
        }

        // Store span in request for later use
        request.setAttribute("otel.span", span);
        request.setAttribute("otel.scope", span.makeCurrent());

        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request,
            HttpServletResponse response,
            Object handler,
            Exception ex) {
        Span span = (Span) request.getAttribute("otel.span");
        Scope scope = (Scope) request.getAttribute("otel.scope");

        if (span != null) {
            // Add response attributes
            span.setAttribute("http.status_code", response.getStatus());

            // Mark as error if status >= 400
            if (response.getStatus() >= 400) {
                span.recordException(
                        new Exception("HTTP " + response.getStatus()));
            }

            // Add exception if present
            if (ex != null) {
                span.recordException(ex);
            }

            // End span
            span.end();
        }

        // Close scope
        if (scope != null) {
            scope.close();
        }
    }
}
