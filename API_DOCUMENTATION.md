#  API Documentation
## Autonomous Self-Healing System

Complete REST API reference for all microservices.

---

## Table of Contents
1. [Gateway Service API](#gateway-service-api)
2. [Auth Service API](#auth-service-api)
3. [Data Service API](#data-service-api)
4. [Health Monitor API](#health-monitor-api)
5. [Recovery Manager API](#recovery-manager-api)
6. [Logging Service API](#logging-service-api)
7. [Notification Service API](#notification-service-api)
8. [Common Patterns](#common-patterns)

---

## Gateway Service API

**Base URL**: `http://localhost:8080`

### Endpoints

#### GET /
Homepage with system overview

**Response**: HTML page

---

#### GET /dashboard.html
Live monitoring dashboard

**Response**: HTML page with real-time visualization

---

#### GET /actuator/health
Service health check

**Response**:
```json
{
  "status": "UP"
}
```

---

## Auth Service API

**Base URL**: `http://localhost:8081`

### Endpoints

#### POST /auth/login
User authentication

**Request**:
```json
{
  "username": "admin",
  "password": "password123"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Login successful",
  "userId": "user-123"
}
```

**Status Codes**:
- `200 OK` - Login successful
- `401 Unauthorized` - Invalid credentials

---

#### POST /auth/token
Generate authentication token

**Request**:
```json
{
  "userId": "user-123"
}
```

**Response**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": 3600
}
```

---

## Data Service API

**Base URL**: `http://localhost:8082`

### Endpoints

#### GET /data/items
Retrieve all items

**Response**:
```json
{
  "items": [
    {
      "id": 1,
      "name": "Item 1",
      "value": "Value 1"
    },
    {
      "id": 2,
      "name": "Item 2",
      "value": "Value 2"
    }
  ]
}
```

---

#### POST /data/items
Create new item

**Request**:
```json
{
  "name": "New Item",
  "value": "New Value"
}
```

**Response**:
```json
{
  "id": 3,
  "name": "New Item",
  "value": "New Value",
  "created": "2026-02-11T09:00:00Z"
}
```

**Status Codes**:
- `201 Created` - Item created successfully
- `400 Bad Request` - Invalid input

---

#### GET /data/kill
** Chaos Engineering Endpoint**

Intentionally crashes the service for testing

**Response**: Service terminates (no response)

**Purpose**: Demonstrates self-healing capability

---

#### GET /data/latency?ms=5000
** Chaos Engineering Endpoint**

Adds artificial latency to responses

**Query Parameters**:
- `ms` - Milliseconds of delay (default: 5000)

**Response**:
```json
{
  "message": "Response delayed by 5000ms",
  "timestamp": "2026-02-11T09:00:05Z"
}
```

---

## Health Monitor API

**Base URL**: `http://localhost:8083`

### Endpoints

#### GET /health/status
Get current health status of all monitored services

**Response**:
```json
{
  "timestamp": "2026-02-11T09:00:00Z",
  "services": [
    {
      "name": "gateway-service",
      "url": "http://gateway-service:8080/actuator/health",
      "status": "HEALTHY",
      "lastCheck": "2026-02-11T09:00:00Z",
      "responseTime": 45
    },
    {
      "name": "auth-service",
      "url": "http://auth-service:8081/actuator/health",
      "status": "HEALTHY",
      "lastCheck": "2026-02-11T09:00:00Z",
      "responseTime": 32
    },
    {
      "name": "data-service",
      "url": "http://data-service:8082/actuator/health",
      "status": "UNHEALTHY",
      "lastCheck": "2026-02-11T09:00:05Z",
      "error": "Connection timeout"
    }
  ],
  "summary": {
    "total": 7,
    "healthy": 6,
    "unhealthy": 1
  }
}
```

---

#### GET /health/history
Get health check history

**Query Parameters**:
- `service` - Filter by service name (optional)
- `limit` - Number of records (default: 100)

**Response**:
```json
{
  "history": [
    {
      "timestamp": "2026-02-11T09:00:00Z",
      "service": "data-service",
      "status": "HEALTHY"
    },
    {
      "timestamp": "2026-02-11T09:00:05Z",
      "service": "data-service",
      "status": "UNHEALTHY",
      "error": "Connection timeout"
    }
  ]
}
```

---

## Recovery Manager API

**Base URL**: `http://localhost:8084`

### Endpoints

#### POST /recover
Trigger recovery for a failed service

**Request**:
```json
{
  "serviceUrl": "http://data-service:8082",
  "serviceName": "data-service",
  "failureReason": "Health check timeout",
  "severity": "CRITICAL"
}
```

**Response**:
```json
{
  "status": "SUCCESS",
  "message": "Container data-service restarted successfully",
  "containerName": "data-service",
  "recoveryStartTime": "2026-02-11T09:00:10Z",
  "recoveryEndTime": "2026-02-11T09:00:18Z",
  "recoveryDuration": "8.5s",
  "actions": [
    "Identified container: data-service",
    "Executed: docker restart data-service",
    "Verified container status: running",
    "Sent notification to team"
  ]
}
```

**Status Codes**:
- `200 OK` - Recovery successful
- `500 Internal Server Error` - Recovery failed

---

#### GET /recover/stats
Get recovery statistics

**Response**:
```json
{
  "totalRecoveries": 42,
  "successfulRecoveries": 41,
  "failedRecoveries": 1,
  "successRate": 97.6,
  "averageRecoveryTime": "12.3s",
  "lastRecovery": {
    "service": "data-service",
    "timestamp": "2026-02-11T09:00:18Z",
    "duration": "8.5s",
    "status": "SUCCESS"
  },
  "recoveryByService": {
    "data-service": 15,
    "auth-service": 12,
    "gateway-service": 8,
    "logging-service": 7
  }
}
```

---

#### GET /recover/history
Get recovery history

**Query Parameters**:
- `service` - Filter by service name (optional)
- `status` - Filter by status (SUCCESS/FAILED) (optional)
- `limit` - Number of records (default: 50)

**Response**:
```json
{
  "recoveries": [
    {
      "id": "rec-123",
      "service": "data-service",
      "timestamp": "2026-02-11T09:00:18Z",
      "duration": "8.5s",
      "status": "SUCCESS",
      "failureReason": "Health check timeout",
      "actions": ["docker restart data-service"]
    }
  ]
}
```

---

## Logging Service API

**Base URL**: `http://localhost:8085`

### Endpoints

#### POST /logs
Submit log entry

**Request**:
```json
{
  "service": "data-service",
  "level": "ERROR",
  "message": "Service crashed unexpectedly",
  "timestamp": "2026-02-11T09:00:05Z",
  "metadata": {
    "errorCode": "ERR_500",
    "stackTrace": "..."
  }
}
```

**Response**:
```json
{
  "id": "log-456",
  "status": "STORED",
  "timestamp": "2026-02-11T09:00:05Z"
}
```

---

#### GET /logs
Query logs

**Query Parameters**:
- `service` - Filter by service name
- `level` - Filter by log level (INFO, WARN, ERROR)
- `from` - Start timestamp (ISO 8601)
- `to` - End timestamp (ISO 8601)
- `limit` - Number of records (default: 100)

**Response**:
```json
{
  "logs": [
    {
      "id": "log-456",
      "service": "data-service",
      "level": "ERROR",
      "message": "Service crashed unexpectedly",
      "timestamp": "2026-02-11T09:00:05Z"
    }
  ],
  "total": 1,
  "page": 1
}
```

---

#### GET /logs/service/{serviceName}
Get logs for specific service

**Path Parameters**:
- `serviceName` - Name of the service

**Response**: Same as GET /logs

---

## Notification Service API

**Base URL**: `http://localhost:8086`

### Endpoints

#### POST /notify
Send notification to all configured channels

**Request**:
```json
{
  "subject": "Service Recovery Alert",
  "message": "data-service has been recovered successfully",
  "severity": "CRITICAL",
  "channels": ["email", "slack", "sms"],
  "metadata": {
    "service": "data-service",
    "recoveryTime": "8.5s"
  }
}
```

**Response**:
```json
{
  "status": "SENT",
  "notificationId": "notif-789",
  "timestamp": "2026-02-11T09:00:20Z",
  "channelResults": {
    "email": "SUCCESS",
    "slack": "SUCCESS",
    "sms": "SUCCESS"
  }
}
```

---

#### POST /notify/email
Send email notification

**Request**:
```json
{
  "to": ["team@company.com"],
  "subject": "Service Recovery Alert",
  "body": "data-service has been recovered",
  "priority": "HIGH"
}
```

**Response**:
```json
{
  "status": "SENT",
  "messageId": "email-123",
  "timestamp": "2026-02-11T09:00:20Z"
}
```

---

#### POST /notify/slack
Send Slack notification

**Request**:
```json
{
  "channel": "#alerts",
  "message": " data-service recovered successfully",
  "username": "Self-Healing Bot",
  "iconEmoji": ":robot_face:"
}
```

**Response**:
```json
{
  "status": "SENT",
  "timestamp": "2026-02-11T09:00:20Z",
  "slackResponse": {
    "ok": true,
    "ts": "1644577220.000100"
  }
}
```

---

## Common Patterns

### Error Response Format

All services use consistent error response format:

```json
{
  "error": {
    "code": "ERR_SERVICE_UNAVAILABLE",
    "message": "Service is currently unavailable",
    "timestamp": "2026-02-11T09:00:00Z",
    "path": "/data/items",
    "details": {
      "reason": "Connection timeout",
      "retryAfter": 30
    }
  }
}
```

### Common HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful request |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Authentication required |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service down |

### Pagination

For endpoints returning lists:

**Request**:
```
GET /logs?page=2&size=50
```

**Response**:
```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "size": 50,
    "total": 500,
    "totalPages": 10
  }
}
```

### Authentication (Future Enhancement)

All endpoints will support JWT authentication:

**Header**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Testing APIs

### Using cURL

```bash
# Health check
curl http://localhost:8080/actuator/health

# Get all items
curl http://localhost:8082/data/items

# Create item
curl -X POST http://localhost:8082/data/items \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","value":"123"}'

# Trigger recovery
curl -X POST http://localhost:8084/recover \
  -H "Content-Type: application/json" \
  -d '{"serviceUrl":"http://data-service:8082","serviceName":"data-service"}'
```

### Using Postman

Import this collection:

```json
{
  "info": {
    "name": "Self-Healing System API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "http://localhost:8080/actuator/health"
      }
    },
    {
      "name": "Get Items",
      "request": {
        "method": "GET",
        "url": "http://localhost:8082/data/items"
      }
    }
  ]
}
```

---

## Rate Limits

Currently no rate limits implemented. For production:

- Health checks: 1 request per second
- Recovery triggers: 10 requests per minute
- Notifications: 100 requests per hour

---

## Webhooks

Services can send webhooks for events:

**Webhook Payload**:
```json
{
  "event": "service.recovered",
  "timestamp": "2026-02-11T09:00:20Z",
  "data": {
    "service": "data-service",
    "duration": "8.5s",
    "status": "SUCCESS"
  }
}
```

**Configure in application.yml**:
```yaml
webhooks:
  enabled: true
  urls:
    - https://your-system.com/api/webhooks
```

---

**For integration examples, see [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)**
