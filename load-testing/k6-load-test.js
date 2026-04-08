import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const latencyTrend = new Trend('latency');
const requestCounter = new Counter('requests');

// Test configuration
export const options = {
  stages: [
    // Warm-up phase
    { duration: '1m', target: 50 },
    
    // Gradual ramp-up
    { duration: '3m', target: 200 },
    { duration: '2m', target: 200 },
    
    // First spike
    { duration: '1m', target: 500 },
    { duration: '3m', target: 500 },
    
    // Scale down
    { duration: '2m', target: 200 },
    { duration: '2m', target: 200 },
    
    // Major spike
    { duration: '1m', target: 1000 },
    { duration: '5m', target: 1000 },
    
    // Peak load
    { duration: '2m', target: 2000 },
    { duration: '3m', target: 2000 },
    
    // Gradual cool-down
    { duration: '2m', target: 500 },
    { duration: '2m', target: 100 },
    { duration: '2m', target: 0 },
  ],
  
  thresholds: {
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],
    'http_req_failed': ['rate<0.05'],
    'errors': ['rate<0.05'],
  },
  
  // Export results to Prometheus
  ext: {
    loadimpact: {
      projectID: 'self-healing-system',
      name: 'Auto-Scaling Load Test'
    }
  }
};

const BASE_URL = __ENV.BASE_URL || 'http://gateway-service.self-healing-prod';

// Simulate realistic user scenarios
export default function () {
  group('User Journey', function () {
    // Scenario 1: Health check (10% of traffic)
    if (Math.random() < 0.1) {
      healthCheck();
    }
    
    // Scenario 2: Authentication (20% of traffic)
    else if (Math.random() < 0.3) {
      authenticate();
    }
    
    // Scenario 3: Data operations (50% of traffic)
    else if (Math.random() < 0.8) {
      dataOperations();
    }
    
    // Scenario 4: Anomaly check (20% of traffic)
    else {
      checkAnomalies();
    }
  });
  
  // Random think time between 1-5 seconds
  sleep(Math.random() * 4 + 1);
}

function healthCheck() {
  const res = http.get(`${BASE_URL}/api/health`);
  
  requestCounter.add(1);
  latencyTrend.add(res.timings.duration);
  
  const success = check(res, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 100ms': (r) => r.timings.duration < 100,
  });
  
  errorRate.add(!success);
}

function authenticate() {
  const payload = JSON.stringify({
    username: `user${Math.floor(Math.random() * 1000)}`,
    password: 'password123'
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  const res = http.post(`${BASE_URL}/api/auth/login`, payload, params);
  
  requestCounter.add(1);
  latencyTrend.add(res.timings.duration);
  
  const success = check(res, {
    'auth status is 200': (r) => r.status === 200,
    'auth response time < 300ms': (r) => r.timings.duration < 300,
    'auth returns token': (r) => r.json('token') !== undefined,
  });
  
  errorRate.add(!success);
  
  return res.json('token');
}

function dataOperations() {
  // GET data
  let res = http.get(`${BASE_URL}/api/data`);
  
  requestCounter.add(1);
  latencyTrend.add(res.timings.duration);
  
  let success = check(res, {
    'data GET status is 200': (r) => r.status === 200,
    'data GET response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  errorRate.add(!success);
  
  sleep(0.5);
  
  // POST data (30% of data operations)
  if (Math.random() < 0.3) {
    const payload = JSON.stringify({
      data: `test-data-${Date.now()}`,
      value: Math.random() * 100
    });
    
    const params = {
      headers: {
        'Content-Type': 'application/json',
      },
    };
    
    res = http.post(`${BASE_URL}/api/data`, payload, params);
    
    requestCounter.add(1);
    latencyTrend.add(res.timings.duration);
    
    success = check(res, {
      'data POST status is 201': (r) => r.status === 201,
      'data POST response time < 600ms': (r) => r.timings.duration < 600,
    });
    
    errorRate.add(!success);
  }
}

function checkAnomalies() {
  const services = [
    'gateway-service',
    'auth-service',
    'data-service',
    'health-monitor-service',
    'recovery-manager-service'
  ];
  
  const service = services[Math.floor(Math.random() * services.length)];
  
  const res = http.get(`${BASE_URL}/api/anomaly/score/${service}`);
  
  requestCounter.add(1);
  latencyTrend.add(res.timings.duration);
  
  const success = check(res, {
    'anomaly check status is 200': (r) => r.status === 200,
    'anomaly check response time < 400ms': (r) => r.timings.duration < 400,
    'anomaly score is valid': (r) => {
      const score = r.json('anomaly_score');
      return score >= 0 && score <= 1;
    },
  });
  
  errorRate.add(!success);
}

// Setup function (runs once at start)
export function setup() {
  console.log('Starting load test...');
  console.log(`Base URL: ${BASE_URL}`);
  return { startTime: Date.now() };
}

// Teardown function (runs once at end)
export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log(`Load test completed in ${duration} seconds`);
}
