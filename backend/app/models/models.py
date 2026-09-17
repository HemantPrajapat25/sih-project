"""
NumberGuard — Full Database Models (Phase 2)
All 22 normalized entities for the number lifecycle management platform.
"""
import uuid
import json
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey,
    Text, Float, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from app.db.session import Base


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def utcnow():
    return datetime.now(timezone.utc)


def gen_uuid():
    return str(uuid.uuid4())


# ===========================================================================
# IDENTITY & RBAC
# ===========================================================================

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(128), nullable=False, unique=True)
    # PLATFORM, TELECOM, BANK, FINTECH, ECOMMERCE, MOBILITY, OTHER_SERVICE_PROVIDER, AUDITOR_ORGANIZATION
    org_type = Column(String(32), nullable=False)
    status = Column(String(32), default="ACTIVE")  # ACTIVE, SUSPENDED
    is_active = Column(Boolean, default=True)
    country_code = Column(String(8), default="IN")
    contact_email = Column(String(128), nullable=True)
    domain = Column(String(128), nullable=True)
    primary_contact = Column(String(128), nullable=True)
    allowed_modules = Column(Text, nullable=True)  # JSON string or comma-separated list
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    users = relationship("User", back_populates="organization")
    api_keys = relationship("ApiKey", back_populates="organization")
    organization_users = relationship("OrganizationUser", back_populates="organization")


class Role(Base):
    """Named roles in the system (normalised from the inline `role` string)."""
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(64), unique=True, nullable=False)  # SUPER_ADMIN, etc.
    display_name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    is_system_role = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    user_roles = relationship("UserRole", back_populates="role")
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")


class Permission(Base):
    """Granular permissions (NUMBERS_READ, PROVIDERS_WRITE, etc.)."""
    __tablename__ = "permissions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(64), unique=True, nullable=False)
    category = Column(String(32), nullable=False)  # NUMBERS, PROVIDERS, RISK, ADMIN
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    role_permissions = relationship("RolePermission", back_populates="permission")


class RolePermission(Base):
    """M2M: Role ↔ Permission."""
    __tablename__ = "role_permissions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(String(36), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
    granted_at = Column(DateTime, default=utcnow)

    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)

    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    email = Column(String(128), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(128), nullable=False)
    # Inline role string kept for backward compat with existing RBAC dep
    role = Column(String(32), nullable=False)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    organization = relationship("Organization", back_populates="users")
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    organization_users = relationship("OrganizationUser", back_populates="user")


class UserRole(Base):
    """M2M: User ↔ Role (normalized role assignments)."""
    __tablename__ = "user_roles"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime, default=utcnow)
    assigned_by = Column(String(36), nullable=True)  # user_id of assigner

    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")


class OrganizationUser(Base):
    """M2M join table with membership metadata."""
    __tablename__ = "organization_users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    membership_role = Column(String(32), default="MEMBER")  # OWNER, ADMIN, MEMBER
    joined_at = Column(DateTime, default=utcnow)
    is_primary = Column(Boolean, default=True)

    __table_args__ = (UniqueConstraint("organization_id", "user_id", name="uq_org_user"),)

    organization = relationship("Organization", back_populates="organization_users")
    user = relationship("User", back_populates="organization_users")


# ===========================================================================
# MOBILE NUMBER REGISTRY
# ===========================================================================

class MobileNumber(Base):
    """
    Canonical mobile number registry — the authoritative number record.
    DecommissionedNumber is kept as the operational table for lifecycle management.
    MobileNumber tracks the full history across multiple lifecycle cycles.
    """
    __tablename__ = "mobile_numbers"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    phone_hash = Column(String(64), unique=True, index=True, nullable=False)  # HMAC-SHA256
    masked_number = Column(String(32), nullable=False)
    # National format: +91 country prefix, 10-digit MSISDN
    country_code = Column(String(8), default="+91")
    carrier = Column(String(32), nullable=False)
    circle = Column(String(64), nullable=True)  # Telecom circle: Mumbai, Delhi, etc.
    number_type = Column(String(16), default="POSTPAID")  # PREPAID, POSTPAID, M2M

    # Current lifecycle state
    # ACTIVE, DECOMMISSIONED, COOLING_HOLD, NOTIFYING_PROVIDERS, MANUAL_REVIEW,
    # ELIGIBLE, REALLOCATED, BLOCKED, DISPUTED
    lifecycle_status = Column(String(32), default="ACTIVE")
    total_recycling_count = Column(Integer, default=0)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)

    first_seen_at = Column(DateTime, default=utcnow)
    last_decommissioned_at = Column(DateTime, nullable=True)
    last_reallocated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_mobile_numbers_carrier", "carrier"),
        Index("ix_mobile_numbers_lifecycle_status", "lifecycle_status"),
        Index("ix_mobile_numbers_org", "organization_id"),
    )

    organization = relationship("Organization")
    lifecycle_events = relationship("NumberLifecycleEvent", back_populates="mobile_number", cascade="all, delete-orphan")
    status_history = relationship("NumberStatusHistory", back_populates="mobile_number", cascade="all, delete-orphan")
    decommissioning_cases = relationship("DecommissioningCase", back_populates="mobile_number", cascade="all, delete-orphan")
    cooling_periods = relationship("CoolingPeriod", back_populates="mobile_number", cascade="all, delete-orphan")
    allocation_decisions = relationship("AllocationDecision", back_populates="mobile_number", cascade="all, delete-orphan")
    provider_associations = relationship("ProviderNumberAssociation", back_populates="mobile_number", cascade="all, delete-orphan")


# ===========================================================================
# LIFECYCLE EVENT SOURCING
# ===========================================================================

class NumberLifecycleEvent(Base):
    """
    Immutable event log: every state transition for every number.
    Implements event-sourcing pattern for the number lifecycle state machine.
    """
    __tablename__ = "number_lifecycle_events"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    mobile_number_id = Column(String(36), ForeignKey("mobile_numbers.id", ondelete="CASCADE"), nullable=False, index=True)

    # Event type codes:
    # NUMBER_DECOMMISSIONED, COOLING_STARTED, PROVIDER_NOTIFIED, PROVIDER_ACKNOWLEDGED,
    # PROVIDER_REMEDIATED, COOLING_EXTENDED, COOLING_COMPLETED, MANUAL_REVIEW_TRIGGERED,
    # MANUAL_REVIEW_RESOLVED, ALLOCATION_APPROVED, ALLOCATION_BLOCKED,
    # NUMBER_REALLOCATED, RISK_SCORE_UPDATED, CASE_OPENED, CASE_CLOSED
    event_type = Column(String(64), nullable=False, index=True)
    from_status = Column(String(32), nullable=True)
    to_status = Column(String(32), nullable=False)

    triggered_by = Column(String(64), nullable=False)  # email or "SYSTEM"
    triggered_by_role = Column(String(32), nullable=True)
    correlation_id = Column(String(64), nullable=False, index=True)
    payload = Column(Text, nullable=True)  # JSON blob with context
    notes = Column(Text, nullable=True)

    occurred_at = Column(DateTime, default=utcnow, index=True)

    mobile_number = relationship("MobileNumber", back_populates="lifecycle_events")

    __table_args__ = (
        Index("ix_nle_mobile_number_occurred", "mobile_number_id", "occurred_at"),
    )


class NumberStatusHistory(Base):
    """
    Flat audit trail of status changes — simpler query target than lifecycle events.
    """
    __tablename__ = "number_status_history"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    mobile_number_id = Column(String(36), ForeignKey("mobile_numbers.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = Column(String(32), nullable=True)
    new_status = Column(String(32), nullable=False)
    change_reason = Column(String(255), nullable=True)
    changed_by = Column(String(64), nullable=False)
    changed_at = Column(DateTime, default=utcnow, index=True)

    mobile_number = relationship("MobileNumber", back_populates="status_history")


# ===========================================================================
# DECOMMISSIONING CASE MANAGEMENT
# ===========================================================================

class DecommissioningCase(Base):
    """
    A case file created when a number is decommissioned.
    Tracks the case lifecycle, assigned case manager, and dispute flags.
    """
    __tablename__ = "decommissioning_cases"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    case_number = Column(String(32), unique=True, nullable=False, index=True)
    mobile_number_id = Column(String(36), ForeignKey("mobile_numbers.id", ondelete="CASCADE"), nullable=False, index=True)

    # OPEN, IN_PROGRESS, PENDING_PROVIDER, PENDING_REVIEW, RESOLVED, CLOSED, DISPUTED
    case_status = Column(String(32), default="OPEN")
    priority = Column(String(16), default="NORMAL")  # LOW, NORMAL, HIGH, CRITICAL
    case_type = Column(String(32), default="STANDARD")  # STANDARD, BANKING, DISPUTED, REGULATORY

    assigned_to = Column(String(64), nullable=True)  # email of case manager
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True)

    dispute_flag = Column(Boolean, default=False)
    dispute_reason = Column(Text, nullable=True)
    dispute_filed_at = Column(DateTime, nullable=True)

    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    sla_due_at = Column(DateTime, nullable=True)  # When case should be resolved

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    mobile_number = relationship("MobileNumber", back_populates="decommissioning_cases")
    remediation_actions = relationship("RemediationAction", back_populates="case", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_decomm_cases_status_priority", "case_status", "priority"),
    )


# ===========================================================================
# COOLING PERIOD MANAGEMENT
# ===========================================================================

class CoolingPeriod(Base):
    """
    Per-number cooling period instance. Each recycling cycle generates one record.
    Separate from CoolingRule (which defines policy templates).
    """
    __tablename__ = "cooling_periods"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    mobile_number_id = Column(String(36), ForeignKey("mobile_numbers.id", ondelete="CASCADE"), nullable=False, index=True)
    cooling_rule_id = Column(String(36), ForeignKey("cooling_rules.id"), nullable=True)

    # ACTIVE, EXTENDED, COMPLETED, BYPASSED
    status = Column(String(16), default="ACTIVE")
    started_at = Column(DateTime, default=utcnow)
    scheduled_end_at = Column(DateTime, nullable=False)
    actual_end_at = Column(DateTime, nullable=True)
    extended_by_days = Column(Integer, default=0)
    extension_reason = Column(Text, nullable=True)
    bypass_reason = Column(Text, nullable=True)
    bypassed_by = Column(String(64), nullable=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    mobile_number = relationship("MobileNumber", back_populates="cooling_periods")
    cooling_rule = relationship("CoolingRule")


# ===========================================================================
# RISK ENGINE
# ===========================================================================

class RiskRule(Base):
    """
    Configurable risk scoring rules. Runtime-adjustable, replaces hard-coded thresholds.
    """
    __tablename__ = "risk_rules"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(128), unique=True, nullable=False)
    code = Column(String(64), unique=True, nullable=False)
    category = Column(String(32), nullable=False)  # BANKING, COOLING, SLA, VELOCITY, REGULATORY
    description = Column(Text, nullable=True)

    # Scoring parameters
    base_weight = Column(Integer, default=10)  # Max points this rule contributes
    multiplier = Column(Float, default=1.0)
    condition_expression = Column(Text, nullable=True)  # JSON DSL for condition

    # Thresholds that trigger this rule
    threshold_value = Column(Float, nullable=True)
    threshold_operator = Column(String(16), default="gte")  # gt, gte, lt, lte, eq

    is_active = Column(Boolean, default=True)
    is_blocking = Column(Boolean, default=False)  # If true, can mark BLOCKED regardless of score
    severity = Column(String(16), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


# ===========================================================================
# SERVICE PROVIDERS & INTEGRATIONS
# ===========================================================================

class ServiceProvider(Base):
    __tablename__ = "service_providers"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
    name = Column(String(128), unique=True, nullable=False)
    code = Column(String(32), unique=True, nullable=False)
    # BANKING, FINTECH, ECOMMERCE, IDENTITY, SOCIAL, TELECOM
    category = Column(String(32), nullable=False)
    # WEBHOOK, REST_API, MOCK
    integration_type = Column(String(32), default="WEBHOOK")
    webhook_url = Column(String(512), nullable=True)
    status = Column(String(32), default="ACTIVE")  # ACTIVE, INACTIVE, DEGRADED
    avg_sla_hours = Column(Float, default=24.0)
    notification_count = Column(Integer, default=0)
    unresolved_count = Column(Integer, default=0)
    last_sync_at = Column(DateTime, default=utcnow)
    created_at = Column(DateTime, default=utcnow)

    organization = relationship("Organization")
    notifications = relationship("ProviderNotification", back_populates="provider")
    integrations = relationship("ProviderIntegration", back_populates="provider", cascade="all, delete-orphan")
    number_associations = relationship("ProviderNumberAssociation", back_populates="provider")


class ProviderIntegration(Base):
    """
    Per-provider integration configuration and credentials.
    Each provider can have multiple integration configurations.
    """
    __tablename__ = "provider_integrations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    provider_id = Column(String(36), ForeignKey("service_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    integration_name = Column(String(128), nullable=False)

    # REST_API, WEBHOOK, SFTP, EMAIL, MOCK
    protocol = Column(String(32), default="WEBHOOK")
    endpoint_url = Column(String(512), nullable=True)
    auth_type = Column(String(32), default="BEARER")  # BEARER, API_KEY, OAUTH2, HMAC, NONE
    # Encrypted credential storage (base64-encoded AES in prod)
    credential_hint = Column(String(64), nullable=True)  # masked hint only
    hashed_secret = Column(String(255), nullable=True)

    timeout_seconds = Column(Integer, default=30)
    max_retries = Column(Integer, default=3)
    retry_backoff_seconds = Column(Integer, default=60)

    is_active = Column(Boolean, default=True)
    last_tested_at = Column(DateTime, nullable=True)
    last_test_result = Column(String(16), nullable=True)  # SUCCESS, FAILURE, TIMEOUT

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    provider = relationship("ServiceProvider", back_populates="integrations")


class ProviderNumberAssociation(Base):
    """
    Tracks which providers have/had a subscription or service tied to a phone number.
    Separate from ProviderNotification — this is the association record, not the notification event.
    """
    __tablename__ = "provider_number_associations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    provider_id = Column(String(36), ForeignKey("service_providers.id"), nullable=False, index=True)
    mobile_number_id = Column(String(36), ForeignKey("mobile_numbers.id", ondelete="CASCADE"), nullable=False, index=True)

    # ACTIVE, UNLINKED, BLOCKED, DISPUTED
    association_status = Column(String(32), default="ACTIVE")
    service_type = Column(String(64), nullable=True)  # e.g. "SAVINGS_ACCOUNT", "UPI", "LOGIN"
    pseudonym_token = Column(String(64), nullable=False, index=True)  # opaque reference given to provider

    linked_at = Column(DateTime, default=utcnow)
    unlinked_at = Column(DateTime, nullable=True)
    unlinked_by = Column(String(64), nullable=True)

    __table_args__ = (
        UniqueConstraint("provider_id", "mobile_number_id", name="uq_provider_number"),
    )

    provider = relationship("ServiceProvider", back_populates="number_associations")
    mobile_number = relationship("MobileNumber", back_populates="provider_associations")


# ===========================================================================
# NOTIFICATIONS & RESPONSES
# ===========================================================================

class ProviderNotification(Base):
    __tablename__ = "provider_notifications"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    number_id = Column(String(36), ForeignKey("decommissioned_numbers.id"), nullable=False, index=True)
    provider_id = Column(String(36), ForeignKey("service_providers.id"), nullable=False)
    pseudonym_ref = Column(String(64), nullable=False, index=True)
    notification_type = Column(String(32), default="DECOMMISSION_ALERT")

    # PENDING, SENT, ACKNOWLEDGED, REMEDIATED, FAILED
    status = Column(String(32), default="SENT")
    sent_at = Column(DateTime, default=utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    remediated_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    response_payload = Column(Text, nullable=True)
    error_message = Column(String(255), nullable=True)

    number = relationship("DecommissionedNumber", back_populates="notifications")
    provider = relationship("ServiceProvider", back_populates="notifications", lazy="joined")
    responses = relationship("ProviderResponse", back_populates="notification", cascade="all, delete-orphan")


class ProviderResponse(Base):
    """
    Individual response payloads from providers for each notification.
    A notification may have multiple responses (initial ack + final remediation).
    """
    __tablename__ = "provider_responses"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    notification_id = Column(String(36), ForeignKey("provider_notifications.id", ondelete="CASCADE"), nullable=False, index=True)

    # ACK, REMEDIATION, REJECTION, ERROR, RETRY_REQUEST
    response_type = Column(String(32), nullable=False)
    status_reported = Column(String(32), nullable=True)  # Provider's own status code
    payload = Column(Text, nullable=True)  # Full JSON response
    http_status_code = Column(Integer, nullable=True)
    responder_id = Column(String(64), nullable=True)  # Provider's internal user/system ID
    notes = Column(Text, nullable=True)

    received_at = Column(DateTime, default=utcnow, index=True)

    notification = relationship("ProviderNotification", back_populates="responses")


class RemediationAction(Base):
    """
    Actions taken by a case manager or system to remediate a decommissioning case.
    """
    __tablename__ = "remediation_actions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    case_id = Column(String(36), ForeignKey("decommissioning_cases.id", ondelete="CASCADE"), nullable=False, index=True)

    # NOTIFICATION_SENT, PROVIDER_CONTACTED, MANUAL_OVERRIDE, COOLING_EXTENDED,
    # BLOCK_APPLIED, DISPUTE_FILED, CASE_ESCALATED, CASE_RESOLVED
    action_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    performed_by = Column(String(64), nullable=False)  # email
    performed_at = Column(DateTime, default=utcnow)
    result = Column(String(16), default="SUCCESS")  # SUCCESS, FAILED, PENDING
    evidence_ref = Column(String(255), nullable=True)  # link/ticket ref

    case = relationship("DecommissioningCase", back_populates="remediation_actions")


# ===========================================================================
# ALLOCATION
# ===========================================================================

class AllocationDecision(Base):
    """
    Final decision record before a number is cleared for reallocation.
    Created by TELECOM_ADMIN or SUPER_ADMIN.
    """
    __tablename__ = "allocation_decisions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    decision_number = Column(String(32), unique=True, nullable=False, index=True)
    mobile_number_id = Column(String(36), ForeignKey("mobile_numbers.id", ondelete="CASCADE"), nullable=False, index=True)

    # APPROVED, BLOCKED, DEFERRED, MANUAL_OVERRIDE_APPROVED, MANUAL_OVERRIDE_REJECTED
    decision = Column(String(32), nullable=False)
    risk_score_at_decision = Column(Integer, nullable=False)
    risk_level_at_decision = Column(String(16), nullable=False)
    cooling_completed = Column(Boolean, default=False)
    banking_cleared = Column(Boolean, default=False)
    all_providers_cleared = Column(Boolean, default=False)

    decided_by = Column(String(64), nullable=False)  # email
    decided_by_role = Column(String(32), nullable=False)
    decision_notes = Column(Text, nullable=True)
    override_justification = Column(Text, nullable=True)  # If manual override

    decided_at = Column(DateTime, default=utcnow)

    mobile_number = relationship("MobileNumber", back_populates="allocation_decisions")


# ===========================================================================
# WEBHOOK EVENT LOG
# ===========================================================================

class WebhookEvent(Base):
    """
    Log of every outbound webhook delivery attempt to provider systems.
    Also logs inbound webhook calls from providers.
    """
    __tablename__ = "webhook_events"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    # OUTBOUND (we send to provider), INBOUND (provider calls us)
    direction = Column(String(16), default="OUTBOUND")
    provider_id = Column(String(36), ForeignKey("service_providers.id"), nullable=True, index=True)
    notification_id = Column(String(36), ForeignKey("provider_notifications.id"), nullable=True)

    event_type = Column(String(64), nullable=False)  # DECOMMISSION_ALERT, ACK_RECEIVED, etc.
    target_url = Column(String(512), nullable=True)
    http_method = Column(String(8), default="POST")

    request_payload = Column(Text, nullable=True)  # JSON
    response_payload = Column(Text, nullable=True)  # JSON
    http_status_code = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)

    # PENDING, DELIVERED, FAILED, TIMED_OUT, RETRYING
    delivery_status = Column(String(16), default="PENDING")
    attempt_number = Column(Integer, default=1)
    next_retry_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    triggered_at = Column(DateTime, default=utcnow, index=True)

    __table_args__ = (
        Index("ix_webhook_events_provider_status", "provider_id", "delivery_status"),
    )


# ===========================================================================
# NOTIFICATION TEMPLATES
# ===========================================================================

class NotificationTemplate(Base):
    """
    SMS / email / webhook payload templates used when notifying providers.
    """
    __tablename__ = "notification_templates"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(128), unique=True, nullable=False)
    code = Column(String(64), unique=True, nullable=False)  # DECOMMISSION_ALERT_BANKING, etc.

    # WEBHOOK_JSON, EMAIL_HTML, EMAIL_TEXT, SMS
    template_type = Column(String(32), nullable=False)
    subject = Column(String(255), nullable=True)  # For email
    body = Column(Text, nullable=False)  # Jinja2 / handlebars template

    # Variables available: {{pseudonym_ref}}, {{carrier}}, {{cooling_end_date}}, etc.
    available_variables = Column(Text, nullable=True)  # JSON array
    category = Column(String(32), default="GENERAL")  # BANKING, GENERAL, REGULATORY

    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


# ===========================================================================
# SYSTEM SETTINGS
# ===========================================================================

class SystemSetting(Base):
    """
    Runtime-configurable K/V settings store.
    Overrides environment-variable defaults without requiring restart.
    """
    __tablename__ = "system_settings"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    key = Column(String(128), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    value_type = Column(String(16), default="string")  # string, int, float, bool, json
    category = Column(String(32), default="GENERAL")  # RISK, COOLING, NOTIFICATIONS, SECURITY
    description = Column(Text, nullable=True)
    is_sensitive = Column(Boolean, default=False)  # If true, mask value in API responses
    is_readonly = Column(Boolean, default=False)  # System-managed, not user-editable
    updated_by = Column(String(64), nullable=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    created_at = Column(DateTime, default=utcnow)


# ===========================================================================
# EXISTING OPERATIONAL MODELS (unchanged — backward compat)
# ===========================================================================

class DecommissionedNumber(Base):
    """
    Operational table for active lifecycle management.
    Kept as the primary target for all existing endpoints.
    Future: linked to MobileNumber.id for cross-cycle tracking.
    """
    __tablename__ = "decommissioned_numbers"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
    phone_hash = Column(String(64), index=True, nullable=False)
    masked_number = Column(String(32), nullable=False)
    carrier = Column(String(32), nullable=False, default="Jio")

    # DECOMMISSIONED, NOTIFYING_PROVIDERS, COOLING_HOLD, MANUAL_REVIEW, ELIGIBLE, REALLOCATED
    status = Column(String(32), nullable=False, default="DECOMMISSIONED")

    decommissioned_at = Column(DateTime, default=utcnow)
    cooling_end_date = Column(DateTime, nullable=False)

    risk_score = Column(Integer, default=50)
    risk_level = Column(String(16), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL

    # ELIGIBLE, COOLING_HOLD, BLOCKED, MANUAL_REVIEW_REQUIRED
    allocation_eligibility = Column(String(32), default="COOLING_HOLD")

    hold_reason = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    organization = relationship("Organization", lazy="joined")
    notifications = relationship("ProviderNotification", back_populates="number", cascade="all, delete-orphan", lazy="selectin")
    risk_evaluations = relationship("RiskEvaluation", back_populates="number", cascade="all, delete-orphan", lazy="selectin")


class CoolingRule(Base):
    __tablename__ = "cooling_rules"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(128), nullable=False)
    carrier = Column(String(32), default="ALL")
    category = Column(String(32), default="STANDARD")  # STANDARD, BANKING_ASSOCIATED, HIGH_RISK
    min_cooling_days = Column(Integer, default=60)
    risk_extension_days = Column(Integer, default=30)
    auto_extend_on_overdue = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    release_condition = Column(String(255), default="Zero high-risk unacknowledged alerts and cooling elapsed")
    created_at = Column(DateTime, default=utcnow)

    cooling_periods = relationship("CoolingPeriod", back_populates="cooling_rule")


class RiskEvaluation(Base):
    __tablename__ = "risk_evaluations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    number_id = Column(String(36), ForeignKey("decommissioned_numbers.id"), nullable=False)
    score = Column(Integer, nullable=False)
    risk_level = Column(String(16), nullable=False)
    factor_banking_weight = Column(Integer, default=0)
    factor_cooling_weight = Column(Integer, default=0)
    factor_sla_weight = Column(Integer, default=0)
    factor_velocity_weight = Column(Integer, default=0)
    details_json = Column(Text, nullable=True)
    evaluated_at = Column(DateTime, default=utcnow)
    evaluated_by = Column(String(64), default="SYSTEM_RISK_ENGINE")

    number = relationship("DecommissionedNumber", back_populates="risk_evaluations")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
    actor_email = Column(String(128), nullable=False)
    actor_role = Column(String(32), nullable=False)
    organization_name = Column(String(128), nullable=False)
    action = Column(String(64), nullable=False)
    entity_type = Column(String(32), nullable=False)
    entity_id = Column(String(64), nullable=False)
    correlation_id = Column(String(64), nullable=False, index=True)
    ip_address = Column(String(45), default="127.0.0.1")
    result = Column(String(16), default="SUCCESS")  # SUCCESS, FAILED, WARNING
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utcnow, index=True)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    key_prefix = Column(String(12), nullable=False)
    hashed_key = Column(String(255), nullable=False)
    name = Column(String(64), nullable=False)
    scopes = Column(String(255), default="numbers:read,providers:write")
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    last_used_at = Column(DateTime, nullable=True)

    organization = relationship("Organization", back_populates="api_keys")
