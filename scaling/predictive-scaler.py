#!/usr/bin/env python3
"""
Predictive Scaler - ML-based proactive scaling
Scales services based on predicted load and anomaly scores
"""

import os
import math
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
from prometheus_api_client import PrometheusConnect
from kubernetes import client, config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PredictiveScaler:
    """
    Predictive scaling service that uses ML anomaly scores
    and historical patterns to proactively scale services
    """
    
    def __init__(self):
        # Load Kubernetes config
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        
        self.apps_v1 = client.AppsV1Api()
        
        # Prometheus connection
        self.prometheus_url = os.getenv(
            'PROMETHEUS_URL',
            'http://prometheus-kube-prometheus-prometheus.self-healing-monitoring:9090'
        )
        self.prom = PrometheusConnect(url=self.prometheus_url, disable_ssl=True)
        
        # Anomaly detector connection
        self.anomaly_url = os.getenv(
            'ANOMALY_DETECTOR_URL',
            'http://anomaly-detector-service.self-healing-prod:8090'
        )
        
        # Scaling configuration
        self.namespace = os.getenv('NAMESPACE', 'self-healing-prod')
        self.services = [
            'gateway-service',
            'auth-service',
            'data-service',
            'health-monitor-service',
            'recovery-manager-service',
            'logging-service',
            'notification-service'
        ]
        
        # Scaling parameters
        self.rps_per_pod = 100  # Target RPS per pod
        self.prediction_horizon_minutes = 15
        
        logger.info("Predictive Scaler initialized")
    
    def get_current_replicas(self, service: str) -> int:
        """Get current replica count for a service"""
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=service,
                namespace=self.namespace
            )
            return deployment.spec.replicas
        except Exception as e:
            logger.error(f"Error getting replicas for {service}: {e}")
            return 3  # Default
    
    def get_request_rate(self, service: str) -> float:
        """Get current request rate for a service"""
        query = f'sum(rate(http_requests_total{{app="{service}"}}[5m]))'
        try:
            result = self.prom.custom_query(query=query)
            if result:
                return float(result[0]['value'][1])
            return 0.0
        except Exception as e:
            logger.error(f"Error getting request rate for {service}: {e}")
            return 0.0
    
    def get_anomaly_score(self, service: str) -> float:
        """Get current anomaly score for a service"""
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.anomaly_url}/api/anomaly/score/{service}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get('anomaly_score', 0.0)
        except Exception as e:
            logger.error(f"Error getting anomaly score for {service}: {e}")
        
        return 0.0
    
    def predict_load(self, service: str, horizon_minutes: int = 15) -> float:
        """
        Predict future load based on historical patterns
        Uses simple time-series analysis
        """
        # Query historical data
        query = f'sum(rate(http_requests_total{{app="{service}"}}[1h]))'
        try:
            result = self.prom.custom_query_range(
                query=query,
                start_time=datetime.now() - timedelta(hours=2),
                end_time=datetime.now(),
                step='1m'
            )
            
            if not result or not result[0]['values']:
                return self.get_request_rate(service)
            
            # Extract values
            values = [float(v[1]) for v in result[0]['values']]
            
            # Simple prediction: average of last 15 minutes + trend
            recent_avg = sum(values[-15:]) / 15
            older_avg = sum(values[-30:-15]) / 15
            trend = recent_avg - older_avg
            
            # Predict future load
            predicted = recent_avg + (trend * (horizon_minutes / 15))
            
            return max(0, predicted)
        
        except Exception as e:
            logger.error(f"Error predicting load for {service}: {e}")
            return self.get_request_rate(service)
    
    def calculate_desired_replicas(self, service: str) -> int:
        """
        Calculate desired replica count based on:
        - Predicted load
        - Anomaly score
        - Current performance
        """
        # Get current metrics
        current_rps = self.get_request_rate(service)
        anomaly_score = self.get_anomaly_score(service)
        
        # Get predicted load
        predicted_rps = self.predict_load(
            service,
            horizon_minutes=self.prediction_horizon_minutes
        )
        
        logger.info(
            f"{service}: current_rps={current_rps:.2f}, "
            f"predicted_rps={predicted_rps:.2f}, "
            f"anomaly_score={anomaly_score:.3f}"
        )
        
        # Use the higher of current or predicted
        target_rps = max(current_rps, predicted_rps)
        
        # Calculate base replicas needed
        base_replicas = math.ceil(target_rps / self.rps_per_pod)
        
        # Adjust for anomaly score
        if anomaly_score > 0.8:
            # Emergency - add 100% buffer
            buffer_multiplier = 2.0
            logger.warning(
                f"{service}: Emergency anomaly score {anomaly_score:.3f}, "
                f"applying 100% buffer"
            )
        elif anomaly_score > 0.6:
            # Critical - add 50% buffer
            buffer_multiplier = 1.5
            logger.warning(
                f"{service}: Critical anomaly score {anomaly_score:.3f}, "
                f"applying 50% buffer"
            )
        elif anomaly_score > 0.3:
            # Warning - add 25% buffer
            buffer_multiplier = 1.25
            logger.info(
                f"{service}: Warning anomaly score {anomaly_score:.3f}, "
                f"applying 25% buffer"
            )
        else:
            # Normal - add 10% buffer
            buffer_multiplier = 1.1
        
        desired_replicas = int(base_replicas * buffer_multiplier)
        
        # Apply constraints based on service
        min_replicas, max_replicas = self.get_replica_limits(service)
        
        final_replicas = max(min_replicas, min(desired_replicas, max_replicas))
        
        logger.info(
            f"{service}: base={base_replicas}, "
            f"desired={desired_replicas}, "
            f"final={final_replicas} "
            f"(min={min_replicas}, max={max_replicas})"
        )
        
        return final_replicas
    
    def get_replica_limits(self, service: str) -> tuple:
        """Get min/max replica limits for a service"""
        limits = {
            'gateway-service': (3, 50),
            'auth-service': (2, 30),
            'data-service': (3, 40),
            'health-monitor-service': (2, 10),
            'recovery-manager-service': (2, 10),
            'logging-service': (2, 15),
            'notification-service': (2, 15),
        }
        return limits.get(service, (2, 20))
    
    def scale_deployment(self, service: str, replicas: int) -> bool:
        """Scale a deployment to the desired replica count"""
        try:
            # Get current deployment
            deployment = self.apps_v1.read_namespaced_deployment(
                name=service,
                namespace=self.namespace
            )
            
            current_replicas = deployment.spec.replicas
            
            if current_replicas == replicas:
                logger.info(f"{service}: Already at {replicas} replicas")
                return True
            
            # Update replica count
            deployment.spec.replicas = replicas
            
            self.apps_v1.patch_namespaced_deployment(
                name=service,
                namespace=self.namespace,
                body=deployment
            )
            
            logger.info(
                f"{service}: Scaled from {current_replicas} to {replicas} replicas"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error scaling {service}: {e}")
            return False
    
    def run_scaling_cycle(self):
        """Run one scaling cycle for all services"""
        logger.info("=" * 60)
        logger.info("Starting scaling cycle")
        logger.info("=" * 60)
        
        for service in self.services:
            try:
                desired_replicas = self.calculate_desired_replicas(service)
                self.scale_deployment(service, desired_replicas)
            except Exception as e:
                logger.error(f"Error processing {service}: {e}")
        
        logger.info("=" * 60)
        logger.info("Scaling cycle completed")
        logger.info("=" * 60)
    
    def run(self, interval_seconds: int = 300):
        """
        Run the predictive scaler continuously
        
        Args:
            interval_seconds: Time between scaling cycles (default: 5 minutes)
        """
        logger.info(f"Starting predictive scaler (interval: {interval_seconds}s)")
        
        while True:
            try:
                self.run_scaling_cycle()
            except Exception as e:
                logger.error(f"Error in scaling cycle: {e}")
            
            logger.info(f"Sleeping for {interval_seconds} seconds...")
            time.sleep(interval_seconds)


if __name__ == '__main__':
    scaler = PredictiveScaler()
    
    # Run every 5 minutes
    interval = int(os.getenv('SCALING_INTERVAL_SECONDS', '300'))
    scaler.run(interval_seconds=interval)
