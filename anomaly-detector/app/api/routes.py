from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional
from pydantic import BaseModel
from loguru import logger
import asyncio

from app.metrics_collector import MetricsCollector
from app.feature_extractor import FeatureExtractor
from app.models.ensemble import EnsembleModel
from app.config import settings


router = APIRouter(prefix="/api/anomaly", tags=["anomaly"])

# Global instances
metrics_collector = MetricsCollector()
feature_extractor = FeatureExtractor()
ensemble_model = EnsembleModel()


# Request/Response Models
class PredictRequest(BaseModel):
    service: str
    metrics: Optional[Dict] = None


class AnomalyResponse(BaseModel):
    service: str
    timestamp: str
    anomaly_score: float
    status: str
    anomaly_type: str
    confidence: float
    predicted_crash_time_minutes: Optional[int]
    recommendation: str
    metrics: Optional[Dict] = None
    model_scores: Optional[Dict] = None


class StatusResponse(BaseModel):
    timestamp: str
    services: List[Dict]


@router.get("/score/{service_name}", response_model=AnomalyResponse)
async def get_anomaly_score(service_name: str):
    """
    Get current anomaly score for a service
    
    Args:
        service_name: Name of the service to check
        
    Returns:
        Anomaly detection results
    """
    try:
        # Collect current metrics
        metrics = await metrics_collector.get_service_metrics(service_name)
        
        if metrics is None:
            raise HTTPException(
                status_code=404,
                detail=f"Could not collect metrics for service: {service_name}"
            )
        
        # Extract features
        features = feature_extractor.extract_features(metrics)
        
        if features is None:
            raise HTTPException(
                status_code=500,
                detail="Feature extraction failed"
            )
        
        # Normalize features
        features_normalized = feature_extractor.normalize_features(features)
        
        # Get time series for LSTM (if available)
        time_series = None
        try:
            time_series_data = await metrics_collector.get_time_series(
                service_name,
                duration_minutes=15
            )
            if len(time_series_data) >= settings.LSTM_SEQUENCE_LENGTH:
                time_series = feature_extractor.extract_time_series_features(
                    time_series_data
                )
        except Exception as e:
            logger.warning(f"Could not get time series: {e}")
        
        # Get prediction
        prediction = ensemble_model.predict(
            features_normalized,
            time_series,
            metrics
        )
        
        # Add metrics to response
        prediction['service'] = service_name
        prediction['timestamp'] = metrics.get('timestamp')
        prediction['metrics'] = {
            'memory_usage': metrics.get('memory_usage'),
            'cpu_usage': metrics.get('cpu_usage'),
            'error_rate': metrics.get('error_rate'),
            'latency_p95': metrics.get('latency_p95')
        }
        
        return prediction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting anomaly score: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect/{service_name}", response_model=AnomalyResponse)
async def detect_and_act(service_name: str):
    """
    Detect anomalies and trigger decision engine if needed
    
    Args:
        service_name: Name of the service to check
        
    Returns:
        Anomaly detection results with decision info
    """
    try:
        # Collect current metrics
        metrics = await metrics_collector.get_service_metrics(service_name)
        
        if metrics is None:
            raise HTTPException(
                status_code=404,
                detail=f"Could not collect metrics for service: {service_name}"
            )
        
        # Extract features
        features = feature_extractor.extract_features(metrics)
        
        if features is None:
            raise HTTPException(
                status_code=500,
                detail="Feature extraction failed"
            )
        
        # Normalize features
        features_normalized = feature_extractor.normalize_features(features)
        
        # Get time series for LSTM (if available)
        time_series = None
        try:
            time_series_data = await metrics_collector.get_time_series(
                service_name,
                duration_minutes=15
            )
            if len(time_series_data) >= settings.LSTM_SEQUENCE_LENGTH:
                time_series = feature_extractor.extract_time_series_features(
                    time_series_data
                )
        except Exception as e:
            logger.warning(f"Could not get time series: {e}")
        
        # Get prediction
        prediction = ensemble_model.predict(
            features_normalized,
            time_series,
            metrics
        )
        
        # Add metrics to response
        prediction['service'] = service_name
        prediction['timestamp'] = metrics.get('timestamp')
        prediction['metrics'] = {
            'memory_usage': metrics.get('memory_usage'),
            'cpu_usage': metrics.get('cpu_usage'),
            'error_rate': metrics.get('error_rate'),
            'latency_p95': metrics.get('latency_p95')
        }

        # TRIGGER DECISION ENGINE IF ANOMALY DETECTED
        if prediction['anomaly_score'] > 0.7:
            try:
                import httpx
                import os
                
                decision_engine_url = os.getenv(
                    "DECISION_ENGINE_URL", 
                    "http://decision-engine-service:8095"
                )
                
                logger.info(f"Anomaly detected (score: {prediction['anomaly_score']}), triggering decision engine")
                
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.post(
                        f"{decision_engine_url}/api/decision/decide-and-execute",
                        json={
                            "service": service_name,
                            "anomaly_score": prediction['anomaly_score'],
                            "error_rate": metrics.get('error_rate', 0),
                            "p95_latency": metrics.get('latency_p95', 0),
                            "cpu_usage": metrics.get('cpu_usage', 0),
                            "memory_usage": metrics.get('memory_usage', 0),
                            "request_rate": metrics.get('request_rate', 0),
                            "current_replicas": metrics.get('replicas', 0),
                            "service_health": "unhealthy" if prediction['status'] == 'anomaly' else "healthy"
                        }
                    )
                    
                    if response.status_code == 200:
                        decision_result = response.json()
                        prediction['decision'] = decision_result
                        logger.info(f"Decision engine executed: {decision_result.get('strategy')}")
                    else:
                        logger.error(f"Decision engine returned error: {response.status_code}")
            
            except Exception as e:
                logger.error(f"Failed to trigger decision engine: {e}")
        
        return prediction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in detect_and_act: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/status", response_model=StatusResponse)
async def get_all_services_status():
    """Get anomaly status for all monitored services"""
    try:
        from datetime import datetime
        
        # Collect metrics for all services
        all_metrics = await metrics_collector.get_all_services_metrics()
        
        services_status = []
        
        for service_name, metrics in all_metrics.items():
            if metrics is None:
                services_status.append({
                    "name": service_name,
                    "anomaly_score": None,
                    "status": "unavailable"
                })
                continue
            
            try:
                # Extract and normalize features
                features = feature_extractor.extract_features(metrics)
                if features is not None:
                    features_normalized = feature_extractor.normalize_features(features)
                    
                    # Get prediction
                    prediction = ensemble_model.predict(
                        features_normalized,
                        None,  # Skip time series for bulk status
                        metrics
                    )
                    
                    services_status.append({
                        "name": service_name,
                        "anomaly_score": prediction['anomaly_score'],
                        "status": prediction['status'],
                        "anomaly_type": prediction.get('anomaly_type')
                    })
                else:
                    services_status.append({
                        "name": service_name,
                        "anomaly_score": None,
                        "status": "error"
                    })
                    
            except Exception as e:
                logger.error(f"Error processing {service_name}: {e}")
                services_status.append({
                    "name": service_name,
                    "anomaly_score": None,
                    "status": "error"
                })
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "services": services_status
        }
        
    except Exception as e:
        logger.error(f"Error getting services status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict")
async def manual_prediction(request: PredictRequest):
    """
    Trigger manual prediction with provided metrics
    
    Args:
        request: Service name and metrics
        
    Returns:
        Anomaly prediction
    """
    try:
        if request.metrics is None:
            # Collect metrics
            metrics = await metrics_collector.get_service_metrics(request.service)
        else:
            metrics = request.metrics
        
        if metrics is None:
            raise HTTPException(
                status_code=400,
                detail="Metrics required for prediction"
            )
        
        # Extract features
        features = feature_extractor.extract_features(metrics)
        if features is None:
            raise HTTPException(status_code=500, detail="Feature extraction failed")
        
        # Normalize
        features_normalized = feature_extractor.normalize_features(features)
        
        # Predict
        prediction = ensemble_model.predict(features_normalized, None, metrics)
        
        return prediction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/status")
async def get_models_status():
    """Get status of ML models"""
    return ensemble_model.get_model_status()


@router.post("/models/retrain")
async def retrain_models(background_tasks: BackgroundTasks):
    """
    Trigger model retraining (background task)
    
    Note: This is a placeholder. In production, retraining should be
    done offline with proper data collection and validation.
    """
    try:
        from datetime import datetime, timedelta
        
        background_tasks.add_task(_retrain_models_task)
        
        return {
            "status": "training_started",
            "estimated_completion": (
                datetime.utcnow() + timedelta(minutes=30)
            ).isoformat(),
            "message": "Model retraining started in background"
        }
        
    except Exception as e:
        logger.error(f"Failed to start retraining: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _retrain_models_task():
    """Background task for model retraining"""
    try:
        logger.info("Starting model retraining task")
        
        # This is a placeholder - in production, you would:
        # 1. Collect historical data from Prometheus
        # 2. Label data (normal vs anomaly)
        # 3. Train models
        # 4. Validate performance
        # 5. Deploy new models
        
        await asyncio.sleep(5)  # Simulate training
        
        logger.info("Model retraining completed")
        
    except Exception as e:
        logger.error(f"Retraining task failed: {e}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Prometheus connectivity
        prometheus_ok = False
        try:
            test_metrics = await metrics_collector.get_service_metrics("gateway-service")
            prometheus_ok = test_metrics is not None
        except:
            pass
        
        return {
            "status": "healthy" if ensemble_model.is_ready() else "degraded",
            "models_loaded": ensemble_model.is_ready(),
            "prometheus_connected": prometheus_ok,
            "isolation_forest_trained": ensemble_model.isolation_forest.is_trained,
            "lstm_trained": ensemble_model.lstm.is_trained
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
