from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser
import random
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SelfHealingUser(FastHttpUser):
    """
    Simulates realistic user behavior for the self-healing system
    """
    
    # Wait time between tasks (1-5 seconds)
    wait_time = between(1, 5)
    
    # User session data
    token = None
    user_id = None
    
    def on_start(self):
        """Called when a user starts"""
        self.user_id = random.randint(1, 10000)
        logger.info(f"User {self.user_id} started")
        
        # Authenticate on start
        self.login()
    
    def on_stop(self):
        """Called when a user stops"""
        logger.info(f"User {self.user_id} stopped")
    
    @task(1)
    def health_check(self):
        """Health check endpoint (10% of traffic)"""
        with self.client.get(
            "/api/health",
            catch_response=True,
            name="Health Check"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(2)
    def login(self):
        """User authentication (20% of traffic)"""
        payload = {
            "username": f"user{self.user_id}",
            "password": "password123"
        }
        
        with self.client.post(
            "/api/auth/login",
            json=payload,
            catch_response=True,
            name="Login"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.token = data.get('token')
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Login failed with status {response.status_code}")
    
    @task(5)
    def get_data(self):
        """Fetch data (50% of traffic)"""
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        with self.client.get(
            "/api/data",
            headers=headers,
            catch_response=True,
            name="Get Data"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                # Token expired, re-login
                self.login()
                response.failure("Token expired")
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(2)
    def create_data(self):
        """Create new data (20% of traffic)"""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        payload = {
            "data": f"test-data-{random.randint(1, 1000000)}",
            "value": random.random() * 100,
            "timestamp": "2026-02-17T10:00:00Z"
        }
        
        with self.client.post(
            "/api/data",
            json=payload,
            headers=headers,
            catch_response=True,
            name="Create Data"
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 401:
                self.login()
                response.failure("Token expired")
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(2)
    def check_anomaly(self):
        """Check anomaly scores (20% of traffic)"""
        services = [
            "gateway-service",
            "auth-service",
            "data-service",
            "health-monitor-service",
            "recovery-manager-service"
        ]
        
        service = random.choice(services)
        
        with self.client.get(
            f"/api/anomaly/score/{service}",
            catch_response=True,
            name="Check Anomaly"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    score = data.get('anomaly_score', 0)
                    
                    # Log high anomaly scores
                    if score > 0.6:
                        logger.warning(
                            f"High anomaly score for {service}: {score}"
                        )
                    
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(1)
    def get_all_anomalies(self):
        """Get anomaly status for all services (10% of traffic)"""
        with self.client.get(
            "/api/anomaly/status",
            catch_response=True,
            name="Get All Anomalies"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    services = data.get('services', [])
                    
                    # Count critical services
                    critical_count = sum(
                        1 for s in services
                        if s.get('status') == 'critical'
                    )
                    
                    if critical_count > 0:
                        logger.warning(
                            f"{critical_count} services in critical state"
                        )
                    
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Got status {response.status_code}")


# Event listeners for custom reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    logger.info("=" * 60)
    logger.info("Load test starting...")
    logger.info(f"Host: {environment.host}")
    logger.info("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    logger.info("=" * 60)
    logger.info("Load test completed")
    logger.info(f"Total requests: {environment.stats.total.num_requests}")
    logger.info(f"Total failures: {environment.stats.total.num_failures}")
    logger.info(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    logger.info(f"RPS: {environment.stats.total.total_rps:.2f}")
    logger.info("=" * 60)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Called for each request"""
    # Log slow requests
    if response_time > 1000:
        logger.warning(
            f"Slow request: {name} took {response_time:.2f}ms"
        )
