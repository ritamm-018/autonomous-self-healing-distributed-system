import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    SERVICE_NAME: str = "anomaly-detector"
    HOST: str = "0.0.0.0"
    PORT: int = 8090
    
    # Prometheus Configuration
    PROMETHEUS_URL: str = os.getenv(
        "PROMETHEUS_URL",
        "http://prometheus-kube-prometheus-prometheus.self-healing-monitoring:9090"
    )
    
    # Recovery Manager Configuration
    RECOVERY_MANAGER_URL: str = os.getenv(
        "RECOVERY_MANAGER_URL",
        "http://recovery-manager-service:8084"
    )
    
    # Services to Monitor
    MONITORED_SERVICES: List[str] = [
        "gateway-service",
        "auth-service",
        "data-service",
        "health-monitor-service",
        "recovery-manager-service",
        "logging-service",
        "notification-service"
    ]
    
    # Metrics Collection
    METRICS_SCRAPE_INTERVAL: int = 15  # seconds
    METRICS_WINDOW_SIZES: List[str] = ["5m", "15m", "1h"]
    
    # ML Model Configuration
    ISOLATION_FOREST_CONTAMINATION: float = 0.1
    ISOLATION_FOREST_N_ESTIMATORS: int = 100
    
    LSTM_SEQUENCE_LENGTH: int = 60  # 15 minutes at 15s intervals
    LSTM_PREDICTION_STEPS: int = 4  # 1 minute ahead
    
    # Anomaly Thresholds
    THRESHOLD_WARNING: float = 0.3
    THRESHOLD_CRITICAL: float = 0.6
    THRESHOLD_EMERGENCY: float = 0.8
    
    # Model Paths
    MODEL_DIR: str = "models"
    ISOLATION_FOREST_MODEL_PATH: str = f"{MODEL_DIR}/isolation_forest.joblib"
    LSTM_MODEL_PATH: str = f"{MODEL_DIR}/lstm_model.h5"
    SCALER_PATH: str = f"{MODEL_DIR}/scaler.joblib"
    
    # Redis Configuration (for caching)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = 0
    
    # Feature Configuration
    FEATURE_NAMES: List[str] = [
        "request_rate",
        "request_rate_change",
        "latency_p50",
        "latency_p95",
        "latency_p99",
        "error_rate",
        "cpu_usage",
        "cpu_spike",
        "memory_usage",
        "memory_growth_rate",
        "gc_pause_time",
        "gc_frequency"
    ]
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
