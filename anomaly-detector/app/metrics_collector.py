import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import httpx
from loguru import logger
from prometheus_api_client import PrometheusConnect

from app.config import settings


class MetricsCollector:
    """Collects metrics from Prometheus for anomaly detection"""
    
    def __init__(self):
        self.prometheus = PrometheusConnect(
            url=settings.PROMETHEUS_URL,
            disable_ssl=True
        )
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info(f"MetricsCollector initialized with Prometheus: {settings.PROMETHEUS_URL}")
    
    async def get_service_metrics(self, service_name: str) -> Optional[Dict]:
        """
        Collect all metrics for a specific service
        
        Args:
            service_name: Name of the service (e.g., 'gateway-service')
            
        Returns:
            Dictionary of metrics or None if collection fails
        """
        try:
            metrics = {}
            
            # Request Rate (requests per second)
            request_rate = await self._query_metric(
                f'rate(http_requests_total{{app="{service_name}"}}[5m])'
            )
            metrics['request_rate'] = request_rate or 0.0
            
            # Request Rate Change (derivative)
            request_rate_change = await self._query_metric(
                f'deriv(http_requests_total{{app="{service_name}"}}[5m])'
            )
            metrics['request_rate_change'] = request_rate_change or 0.0
            
            # Latency Percentiles
            metrics['latency_p50'] = await self._query_percentile(service_name, 0.5)
            metrics['latency_p95'] = await self._query_percentile(service_name, 0.95)
            metrics['latency_p99'] = await self._query_percentile(service_name, 0.99)
            
            # Error Rate
            error_rate = await self._query_metric(
                f'rate(http_requests_errors_total{{app="{service_name}"}}[5m])'
            )
            total_rate = metrics['request_rate']
            metrics['error_rate'] = (error_rate / total_rate) if total_rate > 0 else 0.0
            
            # CPU Usage
            cpu_usage = await self._query_metric(
                f'rate(process_cpu_seconds_total{{app="{service_name}"}}[5m])'
            )
            metrics['cpu_usage'] = min(cpu_usage or 0.0, 1.0)
            
            # CPU Spike Detection (compare to 1h average)
            cpu_1h_avg = await self._query_metric(
                f'avg_over_time(rate(process_cpu_seconds_total{{app="{service_name}"}}[5m])[1h:])'
            )
            metrics['cpu_spike'] = (metrics['cpu_usage'] - (cpu_1h_avg or 0.0)) if cpu_1h_avg else 0.0
            
            # Memory Usage
            memory_used = await self._query_metric(
                f'jvm_memory_used_bytes{{app="{service_name}",area="heap"}}'
            )
            memory_max = await self._query_metric(
                f'jvm_memory_max_bytes{{app="{service_name}",area="heap"}}'
            )
            metrics['memory_usage'] = (memory_used / memory_max) if memory_max and memory_max > 0 else 0.0
            
            # Memory Growth Rate
            memory_growth = await self._query_metric(
                f'deriv(jvm_memory_used_bytes{{app="{service_name}",area="heap"}}[15m])'
            )
            metrics['memory_growth_rate'] = memory_growth or 0.0
            
            # GC Pause Time
            gc_pause = await self._query_metric(
                f'rate(jvm_gc_pause_seconds_sum{{app="{service_name}"}}[5m])'
            )
            metrics['gc_pause_time'] = gc_pause or 0.0
            
            # GC Frequency
            gc_frequency = await self._query_metric(
                f'rate(jvm_gc_pause_seconds_count{{app="{service_name}"}}[5m])'
            )
            metrics['gc_frequency'] = gc_frequency or 0.0
            
            metrics['timestamp'] = datetime.utcnow().isoformat()
            metrics['service'] = service_name
            
            logger.debug(f"Collected metrics for {service_name}: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting metrics for {service_name}: {e}")
            return None
    
    async def _query_metric(self, query: str) -> Optional[float]:
        """Execute a Prometheus query and return the value"""
        try:
            result = self.prometheus.custom_query(query=query)
            if result and len(result) > 0:
                return float(result[0]['value'][1])
            return None
        except Exception as e:
            logger.warning(f"Query failed: {query} - {e}")
            return None
    
    async def _query_percentile(self, service_name: str, percentile: float) -> float:
        """Query latency percentile"""
        query = f'histogram_quantile({percentile}, rate(http_request_duration_seconds_bucket{{app="{service_name}"}}[5m]))'
        result = await self._query_metric(query)
        return result or 0.0
    
    async def get_time_series(
        self,
        service_name: str,
        duration_minutes: int = 15
    ) -> List[Dict]:
        """
        Get time-series metrics for LSTM model
        
        Args:
            service_name: Service to query
            duration_minutes: How far back to look
            
        Returns:
            List of metric dictionaries ordered by time
        """
        try:
            time_series = []
            end_time = datetime.utcnow()
            
            # Collect metrics at 15-second intervals
            for i in range(duration_minutes * 4):  # 4 samples per minute
                timestamp = end_time - timedelta(seconds=i * 15)
                
                # Query metrics at this timestamp
                metrics = await self.get_service_metrics(service_name)
                if metrics:
                    metrics['timestamp'] = timestamp.isoformat()
                    time_series.insert(0, metrics)  # Insert at beginning to maintain order
                
                await asyncio.sleep(0.1)  # Small delay to avoid overwhelming Prometheus
            
            return time_series
            
        except Exception as e:
            logger.error(f"Error collecting time series for {service_name}: {e}")
            return []
    
    async def get_all_services_metrics(self) -> Dict[str, Dict]:
        """Collect metrics for all monitored services"""
        results = {}
        
        tasks = [
            self.get_service_metrics(service)
            for service in settings.MONITORED_SERVICES
        ]
        
        metrics_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        for service, metrics in zip(settings.MONITORED_SERVICES, metrics_list):
            if isinstance(metrics, Exception):
                logger.error(f"Failed to collect metrics for {service}: {metrics}")
                results[service] = None
            else:
                results[service] = metrics
        
        return results
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
