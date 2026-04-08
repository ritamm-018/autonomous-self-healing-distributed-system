#  Gateway Service

## What is This Service?

The **Gateway Service** is the **entry point** for all incoming requests to our distributed system. Think of it as the front door of a building - everyone enters through here, and then gets directed to the right department.

##  Purpose

### In Simple Terms:
- **Receives** all client requests
- **Routes** them to the correct backend service
- **Returns** the response back to the client

### Real-World Analogy:
Like a hotel reception desk:
- Guest (client) arrives at front desk (gateway)
- Receptionist (gateway) checks which department they need
- Receptionist directs them to the right place (backend service)
- Guest gets what they need and leaves

##  How It Works

### Request Flow:
```
Client Request
    ↓
Gateway Service (Port 8080)
    ↓
    ├─ /api/auth/* → Auth Service
    └─ /api/data/* → Data Service
    ↓
Backend Service Response
    ↓
Gateway Service
    ↓
Client Response
```

### Example:
1. Client sends: `GET http://localhost:8080/api/auth/login`
2. Gateway receives the request
3. Gateway sees `/api/auth/*` and routes to Auth Service
4. Gateway forwards: `GET http://auth-service:8081/login`
5. Auth Service responds
6. Gateway returns response to client

##  Code Structure

```
gateway-service/
├── src/main/java/com/selfhealing/gateway/
│   ├── GatewayServiceApplication.java  # Main application class
│   ├── controller/
│   │   ├── GatewayController.java     # Handles incoming requests
│   │   └── HealthController.java      # Health check endpoint
│   └── service/
│       └── RoutingService.java        # Forwards requests to backend
├── src/main/resources/
│   └── application.properties         # Configuration
├── Dockerfile                          # Container definition
└── pom.xml                             # Maven configuration
```

##  Key Components

### 1. GatewayController
- **What**: Receives all HTTP requests
- **How**: Uses `@RestController` and `@RequestMapping`
- **Why**: Single entry point for all traffic

### 2. RoutingService
- **What**: Forwards requests to backend services
- **How**: Uses Spring's `RestTemplate` to make HTTP calls
- **Why**: Decouples clients from backend services

### 3. HealthController
- **What**: Provides health check endpoint
- **How**: Simple GET endpoint returning status
- **Why**: Allows monitoring systems to check if service is alive

##  Endpoints

### Public Endpoints:
- `GET /api` - Welcome message
- `GET /api/auth/*` - Routes to Auth Service
- `GET /api/data/*` - Routes to Data Service
- `GET /health` - Health check
- `GET /actuator/health` - Spring Boot health (detailed)
- `GET /actuator/metrics` - Performance metrics
- `GET /actuator/prometheus` - Prometheus metrics

##  Configuration

### application.properties:
- `server.port=8080` - Port the service runs on
- `auth.service.url` - URL of Auth Service
- `data.service.url` - URL of Data Service
- `gateway.timeout.read=10000` - Request timeout (10 seconds)

### Environment Variables:
- `AUTH_SERVICE_URL` - Override Auth Service URL
- `DATA_SERVICE_URL` - Override Data Service URL

##  Docker

### Build:
```bash
docker build -t gateway-service .
```

### Run:
```bash
docker run -p 8080:8080 gateway-service
```

### With Docker Compose:
The service is automatically built and started when you run:
```bash
docker-compose up
```

##  Testing

### Test Health Endpoint:
```bash
curl http://localhost:8080/health
```

### Test Routing to Auth:
```bash
curl http://localhost:8080/api/auth/health
```

### Test Routing to Data:
```bash
curl http://localhost:8080/api/data/health
```

##  How It Fails

### Failure Scenarios:
1. **Backend Service Down**: Gateway returns 503 (Service Unavailable)
2. **Timeout**: If backend doesn't respond in 10 seconds
3. **Network Error**: Connection refused errors

### How It Recovers:
- Gateway itself doesn't crash (it's resilient)
- It returns error messages to clients
- Health Monitor detects if Gateway is down
- Recovery Manager restarts Gateway if needed

##  Monitoring

### Metrics Exposed:
- Request count
- Response time
- Error rate
- Active connections

### Health Checks:
- `/health` - Simple health check
- `/actuator/health` - Detailed health (includes dependencies)

##  Learning Points

### What You'll Learn:
1. **API Gateway Pattern**: Industry-standard pattern used by Netflix, Amazon
2. **Request Routing**: How to forward HTTP requests
3. **Error Handling**: Graceful handling of backend failures
4. **Service Discovery**: How services find each other

### Real-World Usage:
- **Netflix**: Uses Zuul API Gateway (similar concept)
- **Amazon**: API Gateway for AWS services
- **Google**: Cloud Endpoints (API gateway)

##  Next Steps

After understanding Gateway Service:
1. Build Auth Service (receives requests from Gateway)
2. Build Data Service (receives requests from Gateway)
3. See how Gateway routes between them

---

**This service is the foundation of our distributed system!**
