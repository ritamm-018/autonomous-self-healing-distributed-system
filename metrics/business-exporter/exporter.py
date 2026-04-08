#!/usr/bin/env python3
"""
Business Metrics Exporter
Translates technical metrics into business KPIs (Revenue, Cost, SLA, User Satisfaction)
"""

import time
import logging
import os
import random
from prometheus_client import start_http_server, Gauge, Counter, REGISTRY
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus-kube-prometheus-prometheus.self-healing-monitoring:9090")
SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", "15"))
HOURLY_NODE_COST = float(os.getenv("HOURLY_NODE_COST", "0.04")) # e.g. AWS t3.medium
REVENUE_PER_REQ = float(os.getenv("REVENUE_PER_REQ", "0.05")) # $0.05 per successful Transaction

# --- Prometheus Metrics ---

# Financials
REVENUE_RATE = Gauge('business_revenue_rate_hourly', 'Estimated hourly revenue based on throughput')
COST_RATE = Gauge('business_cost_rate_hourly', 'Estimated hourly cloud cost based on active resources')
PROFIT_MARGIN = Gauge('business_profit_margin_percent', 'Real-time profit margin')
SAVINGS_RATE = Gauge('business_autoscaling_savings_hourly', 'Estimated savings from autoscaling vs static provisioning')

# User Experience
USER_SATISFACTION = Gauge('business_user_satisfaction_score', 'Apdex-like score (0-100) based on latency')
ACTIVE_SESSIONS = Gauge('business_active_user_sessions', 'Estimated number of active users')

# SLA / Compliance
SLA_UPTIME = Gauge('business_sla_uptime_24h', 'Rolling 24h availability percentage')
MTTR_LAST_INCIDENT = Gauge('business_mttr_minutes', 'Mean Time To Recovery for the last resolved incident')
INCIDENTS_OPEN = Gauge('business_incidents_open', 'Number of currently active critical incidents')

def fetch_prometheus_metric(query):
    """Fetch a single vector value from Prometheus"""
    try:
        response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={'query': query})
        data = response.json()
        if data['status'] == 'success' and len(data['data']['result']) > 0:
            return float(data['data']['result'][0]['value'][1])
    except Exception as e:
        logger.debug(f"Failed to fetch metric {query}: {e}")
    return 0.0

def calculate_financials():
    """Calculate Revenue and Cost"""
    # Revenue: Based on successful HTTP requests (mocked correlation)
    # Query: successful requests per second * 3600 * value per req
    rps = fetch_prometheus_metric('sum(rate(http_requests_total{status=~"2.."}[5m]))')
    hourly_revenue = rps * 3600 * REVENUE_PER_REQ
    REVENUE_RATE.set(hourly_revenue)

    # Cost: Active Nodes * Hourly Rate
    # Start with base 3 nodes if metric missing for demo
    nodes = fetch_prometheus_metric('count(kube_node_info)') or 3
    hourly_cost = nodes * HOURLY_NODE_COST
    COST_RATE.set(hourly_cost)

    # Savings: Assuming a static provision of Max Nodes (e.g. 10)
    static_cost = 10 * HOURLY_NODE_COST
    savings = static_cost - hourly_cost
    SAVINGS_RATE.set(savings)

    # Margin
    if hourly_revenue > 0:
        margin = ((hourly_revenue - hourly_cost) / hourly_revenue) * 100
        PROFIT_MARGIN.set(margin)
    else:
        PROFIT_MARGIN.set(0)

def calculate_ux():
    """Calculate User Satisfaction (Apdex Proxy)"""
    # P95 Latency of Gateway
    latency = fetch_prometheus_metric('histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{app="gateway-service"}[5m])) by (le))')
    
    # Simple Formula: < 0.2s = 100, > 2.0s = 0
    if latency <= 0.2:
        score = 100
    elif latency >= 2.0:
        score = 0
    else:
        # Linear degradation
        score = 100 - ((latency - 0.2) / 1.8 * 100)
    
    USER_SATISFACTION.set(score)
    
    # Active Users (Mocked correlation with RPS)
    rps = fetch_prometheus_metric('sum(rate(http_requests_total[5m]))')
    active_users = rps * 50 # Assume 1 req/sec = 50 active users
    ACTIVE_SESSIONS.set(int(active_users))

def calculate_sla():
    """Calculate SLA/SLO Metrics"""
    # Mocking Uptime for now based on recent error rate
    error_rate = fetch_prometheus_metric('sum(rate(http_requests_total{status=~"5.."}[1h])) / sum(rate(http_requests_total[1h]))')
    uptime = (1 - error_rate) * 100
    SLA_UPTIME.set(uptime)

    # Incidents from Decision Engine (Mocked logic)
    # Using 'unhealthy' pods count
    unhealthy = fetch_prometheus_metric('sum(kube_pod_status_phase{phase!="Running"})') 
    INCIDENTS_OPEN.set(unhealthy)
    
    if unhealthy == 0:
        MTTR_LAST_INCIDENT.set(random.uniform(2, 15)) # Demo value

def main():
    logger.info("Starting Business Metrics Exporter on port 9100")
    start_http_server(9100)
    
    while True:
        try:
            calculate_financials()
            calculate_ux()
            calculate_sla()
        except Exception as e:
            logger.error(f"Error collection metrics: {e}")
        
        time.sleep(SCRAPE_INTERVAL)

if __name__ == '__main__':
    main()
