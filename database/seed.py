import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import async_engine, Base, AsyncSessionLocal
from app.models.models import Organization, User, ServiceProvider, DecommissionedNumber, ProviderNotification, CoolingRule, AuditLog, RiskEvaluation
from app.core.security import get_password_hash
from app.core.privacy import compute_phone_hash, mask_phone_number, generate_pseudonym_ref
from app.services.risk_engine import calculate_risk

SEED_NUMBERS = [
    {"phone": "+919820123456", "carrier": "Jio", "days_ago": 10, "cooling_days": 60, "providers": ["HDFC", "PAYTM", "AMAZON"], "ack_status": {"HDFC": "SENT", "PAYTM": "ACKNOWLEDGED", "AMAZON": "REMEDIATED"}, "notes": "Corporate post-paid disconnection (Mumbai Circle)"},
    {"phone": "+919811234567", "carrier": "Airtel", "days_ago": 70, "cooling_days": 60, "providers": ["SBI", "PHONEPE", "WHATSAPP"], "ack_status": {"SBI": "REMEDIATED", "PHONEPE": "REMEDIATED", "WHATSAPP": "REMEDIATED"}, "notes": "Prepaid inactive 90 days - cooling complete (Delhi Circle)"},
    {"phone": "+919845012345", "carrier": "Vi", "days_ago": 45, "cooling_days": 90, "providers": ["HDFC", "SBI", "GOOGLE"], "ack_status": {"HDFC": "SENT", "SBI": "SENT", "GOOGLE": "REMEDIATED"}, "notes": "High net-worth account - multi-bank linkage (Karnataka Circle)"},
    {"phone": "+919447123456", "carrier": "BSNL", "days_ago": 25, "cooling_days": 60, "providers": ["FLIPKART", "WHATSAPP"], "ack_status": {"FLIPKART": "ACKNOWLEDGED", "WHATSAPP": "SENT"}, "notes": "Rural subscriber migration (Kerala Circle)"},
    {"phone": "+919830123456", "carrier": "Jio", "days_ago": 80, "cooling_days": 60, "providers": ["PAYTM", "AMAZON"], "ack_status": {"PAYTM": "REMEDIATED", "AMAZON": "REMEDIATED"}, "notes": "Standard recycling candidate (Kolkata Circle)"},
    {"phone": "+919890123456", "carrier": "Airtel", "days_ago": 5, "cooling_days": 60, "providers": ["HDFC", "PHONEPE"], "ack_status": {"HDFC": "SENT", "PHONEPE": "SENT"}, "notes": "Fresh disconnection yesterday (Maharashtra Circle)"},
    {"phone": "+919920123456", "carrier": "Jio", "days_ago": 15, "cooling_days": 90, "providers": ["SBI", "HDFC", "PAYTM", "AMAZON"], "ack_status": {"SBI": "SENT", "HDFC": "SENT", "PAYTM": "SENT", "AMAZON": "SENT"}, "notes": "Disputed ownership notice received (Mumbai Circle)"},
    {"phone": "+919810123456", "carrier": "Vi", "days_ago": 95, "cooling_days": 60, "providers": ["GOOGLE"], "ack_status": {"GOOGLE": "REMEDIATED"}, "notes": "Ready for carrier release pool (Delhi Circle)"},
    {"phone": "+919840123456", "carrier": "Airtel", "days_ago": 30, "cooling_days": 60, "providers": ["FLIPKART", "PHONEPE"], "ack_status": {"FLIPKART": "REMEDIATED", "PHONEPE": "ACKNOWLEDGED"}, "notes": "Standard cooling halfway (Chennai Circle)"},
    {"phone": "+919711123456", "carrier": "Jio", "days_ago": 62, "cooling_days": 60, "providers": ["HDFC"], "ack_status": {"HDFC": "SENT"}, "notes": "Cooling elapsed but banking ack pending (UP West Circle)"},
]

async def seed_database():
    print("Connecting to database and verifying schema...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from app.main import seed_initial_defaults
    await seed_initial_defaults()

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        # Get existing providers
        prov_res = await session.execute(select(ServiceProvider))
        provider_map = {p.code: p for p in prov_res.scalars().all()}

        if not provider_map:
            print("Providers not found, run app startup first or seed defaults")
            return

        now = datetime.now(timezone.utc)

        print(f"Seeding {len(SEED_NUMBERS)} realistic decommissioned numbers...")
        for item in SEED_NUMBERS:
            phone_h = compute_phone_hash(item["phone"])
            masked = mask_phone_number(item["phone"])

            # Check if already seeded
            existing = await session.execute(select(DecommissionedNumber).where(DecommissionedNumber.phone_hash == phone_h))
            if existing.scalars().first():
                continue

            decom_date = now - timedelta(days=item["days_ago"])
            cooling_end = decom_date + timedelta(days=item["cooling_days"])

            num = DecommissionedNumber(
                phone_hash=phone_h,
                masked_number=masked,
                carrier=item["carrier"],
                status="COOLING_HOLD",
                decommissioned_at=decom_date,
                cooling_end_date=cooling_end,
                notes=item["notes"]
            )
            session.add(num)
            await session.flush()

            # Attach provider notifications
            notifications = []
            for code in item["providers"]:
                p = provider_map.get(code)
                if not p:
                    continue
                ack_st = item["ack_status"].get(code, "SENT")
                pseudonym = generate_pseudonym_ref(f"{num.id}-{p.id}")

                notif = ProviderNotification(
                    number_id=num.id,
                    provider_id=p.id,
                    pseudonym_ref=pseudonym,
                    notification_type="DECOMMISSION_ALERT",
                    status=ack_st,
                    sent_at=decom_date,
                    acknowledged_at=decom_date + timedelta(hours=4) if ack_st in ["ACKNOWLEDGED", "REMEDIATED"] else None,
                    remediated_at=decom_date + timedelta(hours=18) if ack_st == "REMEDIATED" else None,
                    response_payload=f'{{"provider": "{p.name}", "ticket": "TICK-{pseudonym[-6:]}", "action": "Unlinked unverified account sessions"}}'
                )
                session.add(notif)
                notifications.append(notif)
                p.notification_count = (p.notification_count or 0) + 1
                if ack_st != "REMEDIATED":
                    p.unresolved_count = (p.unresolved_count or 0) + 1

            # Compute risk
            score, level, eligibility, factors = calculate_risk(
                decommissioned_at=decom_date,
                cooling_end_date=cooling_end,
                notifications=notifications,
                historical_recycles=0
            )

            num.risk_score = score
            num.risk_level = level
            num.allocation_eligibility = eligibility
            if eligibility == "ELIGIBLE":
                num.status = "ELIGIBLE"
            elif eligibility == "BLOCKED":
                num.status = "MANUAL_REVIEW"
                num.hold_reason = "Unacknowledged banking/fintech alert"
            else:
                num.status = "COOLING_HOLD"

            eval_rec = RiskEvaluation(
                number_id=num.id,
                score=score,
                risk_level=level,
                factor_banking_weight=factors[0]["score_contribution"],
                factor_cooling_weight=factors[1]["score_contribution"],
                factor_sla_weight=factors[2]["score_contribution"],
                factor_velocity_weight=factors[3]["score_contribution"],
                details_json=str(factors),
                evaluated_at=now
            )
            session.add(eval_rec)

            # Audit record
            audit = AuditLog(
                actor_email="telecom.system@carrier.in",
                actor_role="TELECOM_OPERATOR",
                organization_name=item["carrier"],
                action="NUMBER_DECOMMISSIONED",
                entity_type="NUMBER",
                entity_id=num.id,
                correlation_id=f"CORR-SEED-{num.id[:8].upper()}",
                result="SUCCESS",
                details=f"Batch imported {masked} for cooling quarantine ({item['cooling_days']} days)."
            )
            session.add(audit)

        await session.commit()
        print("Database seeded successfully with realistic test records!")

if __name__ == "__main__":
    asyncio.run(seed_database())
