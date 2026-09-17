import asyncio
import logging
import sys
import os
from datetime import datetime, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import AsyncSessionLocal
from app.models.models import DecommissionedNumber, ProviderNotification, CoolingRule
from app.services.risk_engine import calculate_risk
from app.services.audit import record_audit_log

logging.basicConfig(level=logging.INFO, format="%(asctime)s [WORKER] %(message)s")
logger = logging.getLogger("worker")

async def evaluate_cooling_expiries():
    logger.info("Worker: Scanning for numbers nearing cooling expiry or overdue SLAs...")
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        query = select(DecommissionedNumber).options(
            selectinload(DecommissionedNumber.notifications)
        ).where(DecommissionedNumber.status == "COOLING_HOLD")

        res = await session.execute(query)
        numbers = res.scalars().all()
        now = datetime.now(timezone.utc)

        updated_count = 0
        for num in numbers:
            score, level, eligibility, _ = calculate_risk(
                decommissioned_at=num.decommissioned_at,
                cooling_end_date=num.cooling_end_date,
                notifications=num.notifications,
                historical_recycles=0
            )
            if num.risk_score != score or num.allocation_eligibility != eligibility:
                num.risk_score = score
                num.risk_level = level
                num.allocation_eligibility = eligibility
                if eligibility == "ELIGIBLE":
                    num.status = "ELIGIBLE"
                elif eligibility == "BLOCKED":
                    num.status = "MANUAL_REVIEW"
                updated_count += 1

        if updated_count > 0:
            await session.commit()
            logger.info(f"Worker: Re-evaluated and updated {updated_count} numbers.")

async def worker_loop():
    logger.info("NumberGuard Background Worker active.")
    while True:
        try:
            await evaluate_cooling_expiries()
        except Exception as e:
            logger.error(f"Worker loop error: {str(e)}")
        # Poll every 60 seconds
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(worker_loop())
