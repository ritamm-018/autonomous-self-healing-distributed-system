import asyncio
import logging
import os
import httpx
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutonomousHealingWorkflow:
    """
    End-to-end autonomous healing workflow orchestrator
    """
    
    def __init__(self):
        self.anomaly_detector_url = os.getenv("ANOMALY_DETECTOR_URL", "http://anomaly-detector-service:8090")
        self.decision_engine_url = os.getenv("DECISION_ENGINE_URL", "http://decision-engine-service:8095")
        self.recovery_manager_url = os.getenv("RECOVERY_MANAGER_URL", "http://recovery-manager-service:8080")
        self.services = [
            "gateway-service",
            "auth-service",
            "data-service", 
            "logging-service",
            "notification-service"
        ]
        
    async def run_cycle(self):
        """Run a full autonomous cycle"""
        logger.info("Starting autonomous healing cycle")
        
        results = []
        for service in self.services:
            result = await self.process_service(service)
            results.append(result)
            
        return results
    
    async def process_service(self, service: str) -> Dict:
        """Process a single service through the healing cycle"""
        try:
            # 1. Detect Anomaly (and implicitly trigger decision engine via webhook)
            # We call the detect_and_act endpoint which does detection AND calls decision engine if needed
            logger.info(f"Checking {service} for anomalies...")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{self.anomaly_detector_url}/api/anomaly/detect/{service}")
                
                if response.status_code != 200:
                    logger.error(f"Failed to check anomaly for {service}: {response.status_code}")
                    return {"service": service, "status": "error", "error": f"HTTP {response.status_code}"}
                
                detection_result = response.json()
                
                # Check if decision was made (it would be in the response if triggered)
                decision = detection_result.get("decision")
                
                if decision:
                    logger.info(f"Managed recovery for {service}: {decision.get('strategy')} " 
                               f"(success: {decision.get('success')})")
                    
                    return {
                        "service": service,
                        "status": "recovered" if decision.get("success") else "recovery_failed",
                        "anomaly_score": detection_result.get("anomaly_score"),
                        "action": decision.get("strategy"),
                        "decision_id": decision.get("decision_id")
                    }
                elif detection_result.get("anomaly_score", 0) > 0.7:
                    # Anomaly detected but no decision in response? 
                    # This might happen if decision engine failed or wasn't triggered for some reason
                    logger.warning(f"High anomaly {detection_result.get('anomaly_score')} for {service} but no decision returned")
                    return {
                        "service": service, 
                        "status": "anomaly_detected_no_action",
                        "anomaly_score": detection_result.get("anomaly_score")
                    }
                else:
                    logger.info(f"Service {service} is healthy (score: {detection_result.get('anomaly_score'):.2f})")
                    return {
                        "service": service,
                        "status": "healthy",
                        "anomaly_score": detection_result.get("anomaly_score")
                    }
                    
        except Exception as e:
            logger.error(f"Error processing {service}: {e}")
            return {"service": service, "status": "error", "error": str(e)}

    async def start_loop(self, interval_seconds: int = 60):
        """Start the workflow loop"""
        logger.info(f"Starting workflow loop (interval: {interval_seconds}s)")
        while True:
            await self.run_cycle()
            await asyncio.sleep(interval_seconds)

if __name__ == "__main__":
    workflow = AutonomousHealingWorkflow()
    asyncio.run(workflow.start_loop())
