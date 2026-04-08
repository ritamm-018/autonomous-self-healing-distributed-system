#  Integration Guide
## Autonomous Self-Healing System

This guide explains how to integrate the self-healing system with external platforms, including Zoho services, cloud providers, and monitoring tools.

---

## Table of Contents
1. [Zoho Integration](#zoho-integration)
2. [Cloud Platform Integration](#cloud-platform-integration)
3. [Monitoring Tools Integration](#monitoring-tools-integration)
4. [Custom Integrations](#custom-integrations)
5. [API Reference](#api-reference)

---

## Zoho Integration

### Overview
While this system is **standalone** and doesn't require Zoho, you can integrate it with Zoho services for enhanced functionality:

### 1. Zoho Cliq (Team Messaging)

**Purpose**: Send real-time alerts to your Zoho Cliq channels

**Setup**:
1. Create a Zoho Cliq webhook:
   - Go to Zoho Cliq → Bots & Tools → Webhooks
   - Create new webhook
   - Copy the webhook URL

2. Configure Notification Service:
```yaml
# notification-service/src/main/resources/application.yml
zoho:
  cliq:
    webhook-url: https://cliq.zoho.com/api/v2/channelsbyname/YOUR_CHANNEL/message
    enabled: true
```

3. Update NotificationService.java:
```java
@Service
public class NotificationService {
    @Value("${zoho.cliq.webhook-url}")
    private String cliqWebhook;
    
    public void sendZohoCliqAlert(String message) {
        RestTemplate restTemplate = new RestTemplate();
        
        Map<String, Object> payload = new HashMap<>();
        payload.put("text", message);
        payload.put("card", Map.of(
            "title", " System Alert",
            "theme", "modern-inline"
        ));
        
        restTemplate.postForEntity(cliqWebhook, payload, String.class);
    }
}
```

---

### 2. Zoho Desk (Support Ticketing)

**Purpose**: Automatically create support tickets for critical failures

**Setup**:
1. Get Zoho Desk API credentials:
   - Go to Zoho Desk → Setup → API → OAuth
   - Create OAuth client
   - Note: Client ID, Client Secret, Refresh Token

2. Add dependency to `notification-service/pom.xml`:
```xml
<dependency>
    <groupId>com.squareup.okhttp3</groupId>
    <artifactId>okhttp</artifactId>
    <version>4.12.0</version>
</dependency>
```

3. Create ZohoDeskService.java:
```java
@Service
public class ZohoDeskService {
    private static final String ZOHO_DESK_API = "https://desk.zoho.com/api/v1";
    
    @Value("${zoho.desk.org-id}")
    private String orgId;
    
    @Value("${zoho.desk.access-token}")
    private String accessToken;
    
    public void createTicket(String subject, String description, String priority) {
        OkHttpClient client = new OkHttpClient();
        
        JSONObject ticket = new JSONObject();
        ticket.put("subject", subject);
        ticket.put("description", description);
        ticket.put("priority", priority);
        ticket.put("status", "Open");
        ticket.put("departmentId", "YOUR_DEPARTMENT_ID");
        
        RequestBody body = RequestBody.create(
            ticket.toString(),
            MediaType.parse("application/json")
        );
        
        Request request = new Request.Builder()
            .url(ZOHO_DESK_API + "/tickets")
            .addHeader("Authorization", "Zoho-oauthtoken " + accessToken)
            .addHeader("orgId", orgId)
            .post(body)
            .build();
        
        try (Response response = client.newCall(request).execute()) {
            System.out.println("Ticket created: " + response.body().string());
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
```

4. Configure in application.yml:
```yaml
zoho:
  desk:
    org-id: YOUR_ORG_ID
    access-token: YOUR_ACCESS_TOKEN
```

5. Use in Recovery Manager:
```java
@Autowired
private ZohoDeskService zohoDeskService;

public void handleCriticalFailure(String serviceName) {
    // Create ticket for critical failures
    zohoDeskService.createTicket(
        "Critical: " + serviceName + " Failed",
        "Service " + serviceName + " has crashed and recovery was attempted.",
        "High"
    );
}
```

---

### 3. Zoho Analytics (Reporting)

**Purpose**: Send system metrics and recovery statistics to Zoho Analytics

**Setup**:
1. Create Zoho Analytics workspace and table

2. Add to Logging Service:
```java
@Service
public class ZohoAnalyticsService {
    private static final String ANALYTICS_API = "https://analyticsapi.zoho.com/api";
    
    public void sendMetrics(Map<String, Object> metrics) {
        // Format: service_name, timestamp, status, recovery_time
        RestTemplate restTemplate = new RestTemplate();
        
        HttpHeaders headers = new HttpHeaders();
        headers.set("Authorization", "Zoho-oauthtoken " + accessToken);
        
        HttpEntity<Map<String, Object>> request = new HttpEntity<>(metrics, headers);
        
        restTemplate.postForEntity(
            ANALYTICS_API + "/YOUR_WORKSPACE/YOUR_TABLE",
            request,
            String.class
        );
    }
}
```

---

### 4. Zoho Mail (Email Alerts)

**Purpose**: Send detailed email reports via Zoho Mail

**Setup**:
1. Configure SMTP in notification-service:
```yaml
spring:
  mail:
    host: smtp.zoho.com
    port: 587
    username: your-email@zohomail.com
    password: your-app-password
    properties:
      mail:
        smtp:
          auth: true
          starttls:
            enable: true
```

2. Add dependency:
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-mail</artifactId>
</dependency>
```

3. Create EmailService:
```java
@Service
public class EmailService {
    @Autowired
    private JavaMailSender mailSender;
    
    public void sendRecoveryAlert(String serviceName, String details) {
        SimpleMailMessage message = new SimpleMailMessage();
        message.setFrom("alerts@yourdomain.com");
        message.setTo("team@yourdomain.com");
        message.setSubject(" Service Recovery: " + serviceName);
        message.setText(
            "Service: " + serviceName + "\n" +
            "Status: Recovered\n" +
            "Details: " + details + "\n\n" +
            "View Dashboard: http://your-domain.com/dashboard"
        );
        
        mailSender.send(message);
    }
}
```

---

## Cloud Platform Integration

### AWS Integration

#### 1. AWS CloudWatch (Monitoring)

**Purpose**: Send metrics to CloudWatch for centralized monitoring

**Setup**:
```xml
<!-- Add to pom.xml -->
<dependency>
    <groupId>software.amazon.awssdk</groupId>
    <artifactId>cloudwatch</artifactId>
    <version>2.20.0</version>
</dependency>
```

```java
@Service
public class CloudWatchService {
    private final CloudWatchClient cloudWatch;
    
    public CloudWatchService() {
        this.cloudWatch = CloudWatchClient.builder()
            .region(Region.US_EAST_1)
            .build();
    }
    
    public void sendMetric(String metricName, double value) {
        MetricDatum datum = MetricDatum.builder()
            .metricName(metricName)
            .value(value)
            .unit(StandardUnit.COUNT)
            .timestamp(Instant.now())
            .build();
        
        PutMetricDataRequest request = PutMetricDataRequest.builder()
            .namespace("SelfHealingSystem")
            .metricData(datum)
            .build();
        
        cloudWatch.putMetricData(request);
    }
}
```

#### 2. AWS SNS (Notifications)

**Purpose**: Send alerts via AWS SNS to multiple channels

```java
@Service
public class SNSService {
    private final SnsClient snsClient;
    
    @Value("${aws.sns.topic-arn}")
    private String topicArn;
    
    public void sendAlert(String message) {
        PublishRequest request = PublishRequest.builder()
            .topicArn(topicArn)
            .message(message)
            .subject("Self-Healing System Alert")
            .build();
        
        snsClient.publish(request);
    }
}
```

#### 3. AWS ECS/EKS Deployment

**Convert to ECS Task Definition**:
```json
{
  "family": "self-healing-system",
  "containerDefinitions": [
    {
      "name": "gateway-service",
      "image": "your-ecr-repo/gateway-service:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/actuator/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

---

### Azure Integration

#### 1. Azure Application Insights

**Purpose**: Advanced monitoring and diagnostics

```xml
<dependency>
    <groupId>com.microsoft.azure</groupId>
    <artifactId>applicationinsights-spring-boot-starter</artifactId>
    <version>3.4.0</version>
</dependency>
```

```yaml
azure:
  application-insights:
    instrumentation-key: YOUR_INSTRUMENTATION_KEY
```

#### 2. Azure Service Bus (Messaging)

**Purpose**: Reliable message queue for recovery events

```java
@Service
public class AzureServiceBusService {
    private final ServiceBusSenderClient sender;
    
    public void sendRecoveryEvent(RecoveryEvent event) {
        ServiceBusMessage message = new ServiceBusMessage(
            new ObjectMapper().writeValueAsString(event)
        );
        sender.sendMessage(message);
    }
}
```

---

### Google Cloud Platform Integration

#### 1. Google Cloud Monitoring (Stackdriver)

```xml
<dependency>
    <groupId>com.google.cloud</groupId>
    <artifactId>google-cloud-monitoring</artifactId>
    <version>3.4.0</version>
</dependency>
```

#### 2. Google Kubernetes Engine (GKE)

**Convert to Kubernetes Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gateway
  template:
    metadata:
      labels:
        app: gateway
    spec:
      containers:
      - name: gateway
        image: gcr.io/your-project/gateway-service:latest
        ports:
        - containerPort: 8080
        livenessProbe:
          httpGet:
            path: /actuator/health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /actuator/health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## Monitoring Tools Integration

### 1. Prometheus + Grafana

**Purpose**: Metrics collection and visualization

**Setup**:
1. Add Micrometer dependency:
```xml
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-registry-prometheus</artifactId>
</dependency>
```

2. Configure in application.yml:
```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,prometheus
  metrics:
    export:
      prometheus:
        enabled: true
```

3. Create prometheus.yml:
```yaml
scrape_configs:
  - job_name: 'self-healing-system'
    static_configs:
      - targets: 
        - 'gateway-service:8080'
        - 'auth-service:8081'
        - 'data-service:8082'
        - 'health-monitor:8083'
        - 'recovery-manager:8084'
```

---

### 2. ELK Stack (Elasticsearch, Logstash, Kibana)

**Purpose**: Centralized logging and analysis

**Setup**:
1. Add Logstash Logback Encoder:
```xml
<dependency>
    <groupId>net.logstash.logback</groupId>
    <artifactId>logstash-logback-encoder</artifactId>
    <version>7.3</version>
</dependency>
```

2. Configure logback-spring.xml:
```xml
<appender name="LOGSTASH" class="net.logstash.logback.appender.LogstashTcpSocketAppender">
    <destination>logstash:5000</destination>
    <encoder class="net.logstash.logback.encoder.LogstashEncoder"/>
</appender>
```

---

### 3. PagerDuty Integration

**Purpose**: Incident management and on-call alerts

```java
@Service
public class PagerDutyService {
    private static final String PAGERDUTY_API = "https://events.pagerduty.com/v2/enqueue";
    
    @Value("${pagerduty.integration-key}")
    private String integrationKey;
    
    public void triggerIncident(String summary, String severity) {
        RestTemplate restTemplate = new RestTemplate();
        
        Map<String, Object> event = Map.of(
            "routing_key", integrationKey,
            "event_action", "trigger",
            "payload", Map.of(
                "summary", summary,
                "severity", severity,
                "source", "self-healing-system"
            )
        );
        
        restTemplate.postForEntity(PAGERDUTY_API, event, String.class);
    }
}
```

---

## Custom Integrations

### Webhook Support

**Purpose**: Allow any external system to receive alerts

**Implementation**:
```java
@Service
public class WebhookService {
    private final RestTemplate restTemplate = new RestTemplate();
    
    @Value("${webhooks.urls}")
    private List<String> webhookUrls;
    
    public void sendWebhook(WebhookEvent event) {
        for (String url : webhookUrls) {
            try {
                restTemplate.postForEntity(url, event, String.class);
            } catch (Exception e) {
                log.error("Failed to send webhook to: " + url, e);
            }
        }
    }
}
```

**Configuration**:
```yaml
webhooks:
  urls:
    - https://your-system.com/api/alerts
    - https://another-system.com/webhooks/incidents
```

---

## API Reference

### Health Monitor API

#### GET /health/status
Get current health status of all services

**Response**:
```json
{
  "services": [
    {
      "name": "gateway-service",
      "url": "http://gateway-service:8080",
      "status": "HEALTHY",
      "lastCheck": "2026-02-11T09:00:00Z"
    },
    {
      "name": "data-service",
      "url": "http://data-service:8082",
      "status": "UNHEALTHY",
      "lastCheck": "2026-02-11T09:00:05Z"
    }
  ]
}
```

---

### Recovery Manager API

#### POST /recover
Trigger recovery for a failed service

**Request**:
```json
{
  "serviceUrl": "http://data-service:8082",
  "serviceName": "data-service",
  "failureReason": "Health check timeout"
}
```

**Response**:
```json
{
  "status": "SUCCESS",
  "message": "Container data-service restarted successfully",
  "recoveryTime": "8.5s"
}
```

---

### Notification Service API

#### POST /notify
Send notification to all configured channels

**Request**:
```json
{
  "subject": "Service Recovery",
  "message": "data-service has been recovered",
  "severity": "CRITICAL",
  "channels": ["email", "slack", "sms"]
}
```

---

## Environment Variables

### Required for Zoho Integration
```bash
ZOHO_CLIQ_WEBHOOK=https://cliq.zoho.com/api/v2/channelsbyname/YOUR_CHANNEL/message
ZOHO_DESK_ORG_ID=your-org-id
ZOHO_DESK_ACCESS_TOKEN=your-access-token
ZOHO_MAIL_USERNAME=your-email@zohomail.com
ZOHO_MAIL_PASSWORD=your-app-password
```

### Required for AWS Integration
```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789:self-healing-alerts
```

### Required for Azure Integration
```bash
AZURE_APPLICATION_INSIGHTS_KEY=your-instrumentation-key
AZURE_SERVICE_BUS_CONNECTION_STRING=your-connection-string
```

---

## Deployment Checklist

- [ ] Configure notification channels (Email, Slack, etc.)
- [ ] Set up cloud monitoring (CloudWatch, Application Insights, etc.)
- [ ] Configure webhook endpoints
- [ ] Test Zoho integrations (if using)
- [ ] Set up Prometheus/Grafana (optional)
- [ ] Configure PagerDuty/OpsGenie (optional)
- [ ] Test end-to-end recovery flow
- [ ] Document custom integrations

---

**Need Help?** Check the [PROJECT_GUIDE.md](PROJECT_GUIDE.md) for system architecture details.
