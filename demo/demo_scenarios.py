import asyncio
import logging
import httpx
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DemoScenarios:
    
    def __init__(self):
        self.gateway_url = "http://localhost:8080" # External access
    
    async def scenario_1_high_load(self):
        """Simulate high load to trigger auto-scaling"""
        logger.info(" SCENARIO 1: High Load Auto-Scaling")
        print("Generating traffic spike...")
        
        # Mocking load generation logic
        # In a real demo, this would call K6 or similar
        logger.info("Increasing RPS to 5000...")
        await asyncio.sleep(2)
        logger.info("Anomaly Detector triggered (high traffic anomaly)")
        await asyncio.sleep(1)
        logger.info("Decision Engine: Scaling UP to 5 replicas")
        await asyncio.sleep(2)
        logger.info(" Scenario Complete: System scaled to handle load")

    async def scenario_2_recovery(self):
        """Simulate a crash and recovery"""
        logger.info(" SCENARIO 2: Service Failure Recovery")
        print("Injecting failure in Auth Service...")
        
        # Mocking injection
        logger.info("Auth Service Health: UNHEALTHY")
        await asyncio.sleep(1)
        logger.info("Anomaly Score: 0.95 (Critical)")
        await asyncio.sleep(1)
        logger.info("Decision Engine: RESTART POD strategy selected")
        await asyncio.sleep(2)
        logger.info("Recovery Manager: Restarting auth-service pod...")
        await asyncio.sleep(3)
        logger.info(" Scenario Complete: Service recovered successfully")

    async def scenario_3_chaos(self):
        """Simulate chaos resilience"""
        logger.info(" SCENARIO 3: Chaos Resilience")
        print("Unleashing Chaos Monkey...")
        
        logger.info("Randomly killing pods in Data Service...")
        await asyncio.sleep(2)
        logger.info("Circuit Breaker TRIPPED")
        logger.info("Traffic diverted to fallback")
        await asyncio.sleep(2)
        logger.info("Self-Healing mechanism activated")
        await asyncio.sleep(2)
        logger.info(" Scenario Complete: Zero downtime achieved")

    async def run_all(self):
        print("\n=== STARTING AUTOMOUS SYSTEM DEMO ===\n")
        await self.scenario_1_high_load()
        print("\n-----------------------------------\n")
        await self.scenario_2_recovery()
        print("\n-----------------------------------\n")
        await self.scenario_3_chaos()
        print("\n=== DEMO COMPLETED ===")

if __name__ == "__main__":
    demo = DemoScenarios()
    asyncio.run(demo.run_all())
