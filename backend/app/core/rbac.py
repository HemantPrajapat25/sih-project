"""
NumberGuard — Role-Based Access Control (RBAC) & Multi-Tenant Permission System
Defines granular permissions and role-to-permission mappings.
"""
from enum import Enum
from typing import Set, Dict, List


class Role(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    TELECOM_ADMIN = "TELECOM_ADMIN"
    TELECOM_OPERATOR = "TELECOM_OPERATOR"
    SERVICE_PROVIDER_ADMIN = "SERVICE_PROVIDER_ADMIN"
    SERVICE_PROVIDER_OPERATOR = "SERVICE_PROVIDER_OPERATOR"
    AUDITOR = "AUDITOR"
    ANALYST = "ANALYST"


class Permission(str, Enum):
    # Number management
    NUMBERS_READ = "numbers.read"
    NUMBERS_IMPORT = "numbers.import"
    NUMBERS_UPDATE = "numbers.update"
    NUMBERS_DECOMMISSION = "numbers.decommission"
    NUMBERS_REALLOCATE = "numbers.reallocate"
    NUMBERS_RELEASE = "numbers.release"       # Final allocation decision

    # Risk Engine
    RISK_READ = "risk.read"
    RISK_OVERRIDE = "risk.override"

    # Cooling Periods
    COOLING_READ = "cooling.read"
    COOLING_UPDATE = "cooling.update"

    # Service Providers
    PROVIDERS_READ = "providers.read"
    PROVIDERS_WRITE = "providers.write"
    PROVIDERS_MANAGE = "providers.manage"

    # Notifications & Remediation
    NOTIFICATIONS_READ = "notifications.read"
    NOTIFICATIONS_SEND = "notifications.send"
    NOTIFICATIONS_ACKNOWLEDGE = "notifications.acknowledge"
    REMEDIATION_UPDATE = "remediation.update"

    # Analytics & Audit
    ANALYTICS_READ = "analytics.read"
    AUDIT_READ = "audit.read"

    # Integrations
    INTEGRATIONS_MANAGE = "integrations.manage"

    # Users & Roles
    USERS_READ = "users.read"
    USERS_MANAGE = "users.manage"

    # Organization & Settings
    ORGANIZATION_MANAGE = "organization.manage"
    SETTINGS_MANAGE = "settings.manage"
    ADMIN_SETTINGS = "admin.settings"
    GLOBAL_SETTINGS_MANAGE = "global_settings.manage"
    API_KEYS_MANAGE = "api_keys.manage"


# ---------------------------------------------------------------------------
# Explicit role → permission mappings
# ---------------------------------------------------------------------------
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.SUPER_ADMIN: {
        Permission.NUMBERS_READ,
        Permission.NUMBERS_IMPORT,
        Permission.NUMBERS_UPDATE,
        Permission.NUMBERS_DECOMMISSION,
        Permission.NUMBERS_REALLOCATE,
        Permission.NUMBERS_RELEASE,
        Permission.RISK_READ,
        Permission.RISK_OVERRIDE,
        Permission.COOLING_READ,
        Permission.COOLING_UPDATE,
        Permission.PROVIDERS_READ,
        Permission.PROVIDERS_WRITE,
        Permission.PROVIDERS_MANAGE,
        Permission.NOTIFICATIONS_READ,
        Permission.NOTIFICATIONS_SEND,
        Permission.NOTIFICATIONS_ACKNOWLEDGE,
        Permission.REMEDIATION_UPDATE,
        Permission.ANALYTICS_READ,
        Permission.AUDIT_READ,
        Permission.INTEGRATIONS_MANAGE,
        Permission.USERS_READ,
        Permission.USERS_MANAGE,
        Permission.ORGANIZATION_MANAGE,
        Permission.SETTINGS_MANAGE,
        Permission.ADMIN_SETTINGS,
        Permission.GLOBAL_SETTINGS_MANAGE,
        Permission.API_KEYS_MANAGE,
    },
    Role.TELECOM_ADMIN: {
        Permission.NUMBERS_READ,
        Permission.NUMBERS_IMPORT,
        Permission.NUMBERS_UPDATE,
        Permission.NUMBERS_DECOMMISSION,
        Permission.NUMBERS_REALLOCATE,
        Permission.NUMBERS_RELEASE,
        Permission.RISK_READ,
        Permission.RISK_OVERRIDE,
        Permission.COOLING_READ,
        Permission.COOLING_UPDATE,
        Permission.PROVIDERS_READ,
        Permission.PROVIDERS_WRITE,
        Permission.PROVIDERS_MANAGE,
        Permission.NOTIFICATIONS_READ,
        Permission.NOTIFICATIONS_SEND,
        Permission.REMEDIATION_UPDATE,
        Permission.ANALYTICS_READ,
        Permission.AUDIT_READ,
        Permission.INTEGRATIONS_MANAGE,
        Permission.USERS_READ,
        Permission.USERS_MANAGE,
        Permission.SETTINGS_MANAGE,
        Permission.API_KEYS_MANAGE,
    },
    Role.TELECOM_OPERATOR: {
        Permission.NUMBERS_READ,
        Permission.NUMBERS_IMPORT,
        Permission.NUMBERS_UPDATE,
        Permission.NUMBERS_DECOMMISSION,
        Permission.RISK_READ,
        Permission.COOLING_READ,
        Permission.PROVIDERS_READ,
        Permission.NOTIFICATIONS_READ,
        Permission.NOTIFICATIONS_SEND,
        Permission.AUDIT_READ,
    },
    Role.SERVICE_PROVIDER_ADMIN: {
        Permission.NUMBERS_READ,
        Permission.PROVIDERS_READ,
        Permission.PROVIDERS_WRITE,
        Permission.PROVIDERS_MANAGE,
        Permission.NOTIFICATIONS_READ,
        Permission.NOTIFICATIONS_ACKNOWLEDGE,
        Permission.REMEDIATION_UPDATE,
        Permission.ANALYTICS_READ,
        Permission.AUDIT_READ,
        Permission.INTEGRATIONS_MANAGE,
        Permission.USERS_READ,
        Permission.USERS_MANAGE,
        Permission.SETTINGS_MANAGE,
        Permission.API_KEYS_MANAGE,
    },
    Role.SERVICE_PROVIDER_OPERATOR: {
        Permission.NUMBERS_READ,
        Permission.PROVIDERS_READ,
        Permission.NOTIFICATIONS_READ,
        Permission.NOTIFICATIONS_ACKNOWLEDGE,
        Permission.REMEDIATION_UPDATE,
        Permission.AUDIT_READ,
    },
    Role.AUDITOR: {
        Permission.NUMBERS_READ,
        Permission.RISK_READ,
        Permission.COOLING_READ,
        Permission.PROVIDERS_READ,
        Permission.NOTIFICATIONS_READ,
        Permission.ANALYTICS_READ,
        Permission.AUDIT_READ,
        Permission.USERS_READ,
    },
    Role.ANALYST: {
        Permission.NUMBERS_READ,
        Permission.RISK_READ,
        Permission.COOLING_READ,
        Permission.PROVIDERS_READ,
        Permission.NOTIFICATIONS_READ,
        Permission.ANALYTICS_READ,
        Permission.AUDIT_READ,
    },
}


def has_permission(role_str: str, required_permission: Permission) -> bool:
    try:
        role = Role(role_str)
        return required_permission in ROLE_PERMISSIONS.get(role, set())
    except ValueError:
        return False


def get_role_permissions(role_str: str) -> List[str]:
    try:
        role = Role(role_str)
        return [p.value for p in ROLE_PERMISSIONS.get(role, set())]
    except ValueError:
        return []
