import logging
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import async_engine, Base, AsyncSessionLocal
from app.models.models import (
    Organization, User, ServiceProvider, CoolingRule,
    RiskRule, NotificationTemplate, SystemSetting, DecommissionedNumber,
    Role as RoleModel, Permission as PermissionModel,
)
from app.core.security import get_password_hash
from app.api.v1.endpoints.auth import DEMO_ACCOUNTS
from app.services.lifecycle import ingest_decommissioned_number

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("numberguard")

DEFAULT_ORGANIZATIONS = [
    {
        "name": "NumberGuard Platform",
        "org_type": "PLATFORM",
        "domain": "numberguard.internal",
        "primary_contact": "platform.ops@numberguard.internal",
        "allowed_modules": ["*"],
    },
    {
        "name": "DemoTel Telecom",
        "org_type": "TELECOM",
        "domain": "demotel.carrier",
        "primary_contact": "noc.admin@demotel.carrier",
        "allowed_modules": ["NUMBERS", "DECOMMISSIONING", "COOLING", "ALLOCATION", "RISK"],
    },
    {
        "name": "SecureBank",
        "org_type": "BANK",
        "domain": "securebank.fin",
        "primary_contact": "infosec@securebank.fin",
        "allowed_modules": ["PROVIDER_PORTAL", "WEBHOOKS", "CASES", "REMEDIATION"],
    },
    {
        "name": "PayFlow Fintech",
        "org_type": "FINTECH",
        "domain": "payflow.io",
        "primary_contact": "secops@payflow.io",
        "allowed_modules": ["PROVIDER_PORTAL", "WEBHOOKS", "CASES", "REMEDIATION"],
    },
    {
        "name": "ShopKart E-Commerce",
        "org_type": "ECOMMERCE",
        "domain": "shopkart.market",
        "primary_contact": "trust-safety@shopkart.market",
        "allowed_modules": ["PROVIDER_PORTAL", "WEBHOOKS"],
    },
    {
        "name": "MobilityGo Transit",
        "org_type": "MOBILITY",
        "domain": "mobilitygo.app",
        "primary_contact": "security@mobilitygo.app",
        "allowed_modules": ["PROVIDER_PORTAL", "WEBHOOKS"],
    },
    {
        "name": "Telecom Regulatory Authority",
        "org_type": "REGULATOR",
        "domain": "trai.gov.in",
        "primary_contact": "compliance-audit@trai.gov.in",
        "allowed_modules": ["AUDIT", "COMPLIANCE", "ANALYTICS", "REPORTS"],
    },
]

DEFAULT_PROVIDERS = [
    {"name": "SecureBank", "code": "SECUREBANK", "category": "BANKING", "avg_sla_hours": 12.0, "webhook_url": "https://api.sandbox.securebank.fin/v1/telco/lifecycle", "org_name": "SecureBank"},
    {"name": "PayFlow Fintech", "code": "PAYFLOW", "category": "FINTECH", "avg_sla_hours": 6.0, "webhook_url": "https://api.sandbox.payflow.io/webhook/carrier-events", "org_name": "PayFlow Fintech"},
    {"name": "ShopKart E-Commerce", "code": "SHOPKART", "category": "ECOMMERCE", "avg_sla_hours": 24.0, "webhook_url": "https://api.sandbox.shopkart.market/auth/decommission-notify", "org_name": "ShopKart E-Commerce"},
    {"name": "MobilityGo Transit", "code": "MOBILITYGO", "category": "MOBILITY", "avg_sla_hours": 14.0, "webhook_url": "https://api.sandbox.mobilitygo.app/v1/recycle-notify", "org_name": "MobilityGo Transit"},
    {"name": "HDFC Bank Ltd", "code": "HDFC", "category": "BANKING", "avg_sla_hours": 12.0, "webhook_url": "https://api.sandbox.hdfcbank.com/v1/telco/lifecycle", "org_name": None},
    {"name": "State Bank of India", "code": "SBI", "category": "BANKING", "avg_sla_hours": 18.0, "webhook_url": "https://api.sandbox.sbi.co.in/telco/unlinking", "org_name": None},
    {"name": "Paytm Payments Bank", "code": "PAYTM", "category": "FINTECH", "avg_sla_hours": 6.0, "webhook_url": "https://api.sandbox.paytm.com/webhook/carrier-events", "org_name": None},
    {"name": "WhatsApp / Meta", "code": "WHATSAPP", "category": "SOCIAL", "avg_sla_hours": 12.0, "webhook_url": "https://graph.sandbox.whatsapp.com/v18.0/telco/recycled", "org_name": None},
]

DEFAULT_COOLING_RULES = [
    {"name": "National Standard Quarantine", "carrier": "ALL", "category": "STANDARD", "min_cooling_days": 60, "risk_extension_days": 30, "release_condition": "Standard cooling elapsed with zero high-risk hold"},
    {"name": "Banking & Fintech Extended Hold", "carrier": "ALL", "category": "BANKING_ASSOCIATED", "min_cooling_days": 90, "risk_extension_days": 45, "release_condition": "Explicit remediation ack from all linked banks"},
    {"name": "High Risk / Disputed Subscriber Quarantine", "carrier": "ALL", "category": "HIGH_RISK", "min_cooling_days": 120, "risk_extension_days": 60, "release_condition": "Manual sign-off from Telecom Operator Admin"},
]

async def seed_initial_defaults():
    """Ensures database has demo organizations, users, providers, cooling rules, and initial numbers."""
    async with AsyncSessionLocal() as session:
        # 1. Seed Organizations
        org_map = {}
        for org_data in DEFAULT_ORGANIZATIONS:
            existing = await session.execute(select(Organization).where(Organization.name == org_data["name"]))
            org = existing.scalars().first()
            if not org:
                org = Organization(
                    name=org_data["name"],
                    org_type=org_data["org_type"],
                    domain=org_data["domain"],
                    primary_contact=org_data["primary_contact"],
                    allowed_modules=json.dumps(org_data["allowed_modules"]),
                    is_active=True
                )
                session.add(org)
                await session.flush()
            org_map[org.name] = org

        # 2. Seed Service Providers linked to Organizations
        for p in DEFAULT_PROVIDERS:
            existing = await session.execute(select(ServiceProvider).where(ServiceProvider.code == p["code"]))
            provider = existing.scalars().first()
            org_id = org_map.get(p.get("org_name")).id if p.get("org_name") and p.get("org_name") in org_map else None
            
            if not provider:
                provider = ServiceProvider(
                    name=p["name"],
                    code=p["code"],
                    category=p["category"],
                    avg_sla_hours=p["avg_sla_hours"],
                    webhook_url=p["webhook_url"],
                    organization_id=org_id,
                    status="ACTIVE"
                )
                session.add(provider)
            else:
                if org_id and not provider.organization_id:
                    provider.organization_id = org_id

        # 3. Seed Cooling Rules
        for r in DEFAULT_COOLING_RULES:
            existing = await session.execute(select(CoolingRule).where(CoolingRule.name == r["name"]))
            if not existing.scalars().first():
                rule = CoolingRule(
                    name=r["name"], carrier=r["carrier"], category=r["category"],
                    min_cooling_days=r["min_cooling_days"], risk_extension_days=r["risk_extension_days"],
                    release_condition=r["release_condition"], is_active=True
                )
                session.add(rule)

        # 4. Seed Demo Users
        for acc in DEMO_ACCOUNTS:
            existing_user = await session.execute(select(User).where(User.email == acc["email"]))
            user = existing_user.scalars().first()
            target_org = org_map.get(acc["org"])
            
            if not user:
                new_u = User(
                    email=acc["email"],
                    hashed_password=get_password_hash("numberguard2026"),
                    full_name=acc["name"],
                    role=acc["role"],
                    organization_id=target_org.id if target_org else None,
                    is_active=True
                )
                session.add(new_u)
            else:
                if target_org and user.organization_id != target_org.id:
                    user.organization_id = target_org.id

        await session.flush()

        # 5. Risk Rules
        DEFAULT_RISK_RULES = [
            {"name": "Unacknowledged Banking Alert", "code": "BANKING_UNACK", "category": "BANKING",
             "description": "Adds risk for each unacknowledged banking/fintech notification", "base_weight": 20,
             "multiplier": 1.0, "threshold_value": 1.0, "threshold_operator": "gte",
             "is_blocking": True, "severity": "CRITICAL"},
            {"name": "Cooling Period Incomplete", "code": "COOLING_INCOMPLETE", "category": "COOLING",
             "description": "Risk decays as cooling period elapses", "base_weight": 30,
             "multiplier": 1.0, "threshold_value": 100.0, "threshold_operator": "lt",
             "is_blocking": False, "severity": "HIGH"},
            {"name": "General Provider SLA Overdue", "code": "SLA_OVERDUE", "category": "SLA",
             "description": "Adds risk for overdue non-banking provider responses", "base_weight": 7,
             "multiplier": 1.0, "threshold_value": 1.0, "threshold_operator": "gte",
             "is_blocking": False, "severity": "MEDIUM"},
            {"name": "High Recycling Velocity", "code": "VELOCITY_HIGH", "category": "VELOCITY",
             "description": "Adds risk if number has been recycled multiple times", "base_weight": 5,
             "multiplier": 1.0, "threshold_value": 2.0, "threshold_operator": "gte",
             "is_blocking": False, "severity": "LOW"},
        ]
        for r in DEFAULT_RISK_RULES:
            existing = await session.execute(select(RiskRule).where(RiskRule.code == r["code"]))
            if not existing.scalars().first():
                session.add(RiskRule(**r))

        # 6. Notification Templates
        DEFAULT_TEMPLATES = [
            {
                "name": "Banking Decommission Alert", "code": "DECOMMISSION_ALERT_BANKING",
                "template_type": "WEBHOOK_JSON", "category": "BANKING",
                "subject": "Number Decommission Alert — Action Required",
                "body": '{"event":"number_decommissioned","ref":"{{pseudonym_ref}}","carrier":"{{carrier}}","cooling_end":"{{cooling_end_date}}","priority":"HIGH","action_required":true}',
                "available_variables": '["pseudonym_ref","carrier","cooling_end_date","notification_id"]',
            },
            {
                "name": "General Decommission Alert", "code": "DECOMMISSION_ALERT_GENERAL",
                "template_type": "WEBHOOK_JSON", "category": "GENERAL",
                "subject": "Number Decommission Notification",
                "body": '{"event":"number_decommissioned","ref":"{{pseudonym_ref}}","carrier":"{{carrier}}","cooling_end":"{{cooling_end_date}}"}',
                "available_variables": '["pseudonym_ref","carrier","cooling_end_date"]',
            },
            {
                "name": "Cooling Completion Notice", "code": "COOLING_COMPLETED",
                "template_type": "WEBHOOK_JSON", "category": "GENERAL",
                "subject": "Number Cleared — Cooling Period Complete",
                "body": '{"event":"cooling_completed","ref":"{{pseudonym_ref}}","status":"ELIGIBLE_FOR_REALLOCATION"}',
                "available_variables": '["pseudonym_ref","cooling_end_date"]',
            },
        ]
        for t in DEFAULT_TEMPLATES:
            existing = await session.execute(select(NotificationTemplate).where(NotificationTemplate.code == t["code"]))
            if not existing.scalars().first():
                session.add(NotificationTemplate(**t))

        # 7. System Settings
        from app.services.settings_service import DEFAULT_SETTINGS
        for s in DEFAULT_SETTINGS:
            existing = await session.execute(select(SystemSetting).where(SystemSetting.key == s["key"]))
            if not existing.scalars().first():
                session.add(SystemSetting(**s))

        await session.commit()

    # 8. Seed sample numbers in fresh session
    async with AsyncSessionLocal() as num_session:
        demotel_res = await num_session.execute(select(Organization).where(Organization.name == "DemoTel Telecom"))
        demotel_org = demotel_res.scalars().first()
        if demotel_org:
            demotel_org_id = demotel_org.id
            num_check = await num_session.execute(select(DecommissionedNumber).limit(1))
            if not num_check.scalars().first():
                sample_numbers = [
                    ("+919876543210", ["SECUREBANK", "PAYFLOW", "WHATSAPP"]),
                    ("+919811223344", ["SECUREBANK", "SHOPKART"]),
                    ("+919700112233", ["PAYFLOW", "MOBILITYGO"]),
                    ("+919655443322", ["SECUREBANK"]),
                    ("+919544332211", ["SHOPKART", "MOBILITYGO"]),
                ]
                for raw, prov_codes in sample_numbers:
                    await ingest_decommissioned_number(
                        db=num_session,
                        raw_phone=raw,
                        carrier="DemoTel",
                        organization_id=demotel_org_id,
                        associated_provider_codes=prov_codes,
                        actor_email="telecom.admin@demotel.demo",
                        actor_role="TELECOM_ADMIN",
                        org_name="DemoTel Telecom"
                    )

    logger.info("Initialized multi-tenant B2B organizations, demo accounts, providers, cooling rules, templates, and settings.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting NumberGuard Backend Engine...")
    # Auto-create tables for seamless development
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified.")
    await seed_initial_defaults()
    yield
    logger.info("Shutting down NumberGuard Backend Engine...")

app = FastAPI(
    title=settings.APP_NAME,
    description="Privacy-preserving B2B platform for mobile number lifecycle management before telecom reallocation.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Error Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected server error occurred. Correlation logged.",
            "path": request.url.path
        }
    )

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "HEALTHY",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "privacy_mode": "ACTIVE_MASKING_HMAC",
        "database": "CONNECTED"
    }

# Mount v1 API
app.include_router(api_router, prefix=settings.API_V1_STR)
