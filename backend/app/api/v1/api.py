from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    numbers,
    risk,
    providers,
    notifications,
    cooling,
    readiness,
    audit,
    analytics,
    integrations,
    users,
    # Phase 2 new endpoints
    lifecycle_events,
    cases,
    allocation,
    webhooks,
    system_settings,
    # Phase 3 new endpoints
    inbound_webhooks,
    mock_providers,
    api_keys,
    organizations,
)

api_router = APIRouter()

# --- Phase 1 (existing) ---
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(numbers.router, prefix="/numbers", tags=["Numbers Lifecycle"])
api_router.include_router(risk.router, prefix="/risk", tags=["Risk Engine"])
api_router.include_router(providers.router, prefix="/providers", tags=["Service Providers"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(cooling.router, prefix="/cooling", tags=["Cooling Periods"])
api_router.include_router(readiness.router, prefix="/readiness", tags=["Allocation Readiness"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Trail"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics & KPIs"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["Integrations & Sandbox"])
api_router.include_router(users.router, prefix="/users", tags=["Users & RBAC"])

# --- Phase 2 ---
api_router.include_router(lifecycle_events.router, prefix="/lifecycle", tags=["Lifecycle Events & State Machine"])
api_router.include_router(cases.router, prefix="/cases", tags=["Decommissioning Cases"])
api_router.include_router(allocation.router, prefix="/allocation", tags=["Allocation Decisions"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhook Events"])
api_router.include_router(system_settings.router, prefix="/settings", tags=["System Settings"])

# --- Phase 3 & Multi-tenant ---
api_router.include_router(inbound_webhooks.router, prefix="/webhooks", tags=["Inbound Webhooks"])
api_router.include_router(mock_providers.router, prefix="/mock", tags=["Mock Providers"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["API Keys"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
