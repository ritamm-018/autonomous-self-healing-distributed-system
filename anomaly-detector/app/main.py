from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app, Gauge, Counter
from loguru import logger
import sys

from app.api.routes import router
from app.config import settings

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL
)

# Create FastAPI app
app = FastAPI(
    title="Anomaly Detection Service",
    description="AI-powered predictive anomaly detection for self-healing system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Prometheus metrics
anomaly_score_gauge = Gauge(
    'anomaly_score',
    'Current anomaly score for service',
    ['service']
)

predictions_total = Counter(
    'anomaly_predictions_total',
    'Total number of predictions made',
    ['service', 'severity']
)

model_inference_time = Gauge(
    'anomaly_model_inference_seconds',
    'Time taken for model inference'
)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("=" * 60)
    logger.info(" Anomaly Detection Service Starting")
    logger.info("=" * 60)
    logger.info(f"Service: {settings.SERVICE_NAME}")
    logger.info(f"Host: {settings.HOST}:{settings.PORT}")
    logger.info(f"Prometheus URL: {settings.PROMETHEUS_URL}")
    logger.info(f"Monitored Services: {len(settings.MONITORED_SERVICES)}")
    logger.info(f"Thresholds: Warning={settings.THRESHOLD_WARNING}, "
                f"Critical={settings.THRESHOLD_CRITICAL}, "
                f"Emergency={settings.THRESHOLD_EMERGENCY}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Anomaly Detection Service")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Anomaly Detection Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/api/anomaly/health",
            "metrics": "/metrics",
            "anomaly_score": "/api/anomaly/score/{service_name}",
            "all_status": "/api/anomaly/status"
        }
    }


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
