"""
NumberGuard — Pydantic Schemas (Phase 2)
Complete request/response models for all API endpoints.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ===========================================================================
# Auth & Users
# ===========================================================================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user: "UserOut"


class LoginRequest(BaseModel):
    email: str
    password: str
    remember_me: Optional[bool] = False


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str
    organization_id: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    role: str
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    organization_type: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_active: bool
    created_at: datetime


# ===========================================================================
# Number Registry (legacy operational)
# ===========================================================================

class NumberCreate(BaseModel):
    raw_phone: str = Field(..., description="E.164 phone string e.g. +919876543210")
    carrier: str = "Jio"
    notes: Optional[str] = None
    custom_cooling_days: Optional[int] = None
    associated_provider_codes: Optional[List[str]] = Field(
        default=[], description="List of provider codes, e.g. ['HDFC', 'PAYTM']"
    )


class NumberImportRequest(BaseModel):
    numbers: List[NumberCreate]


class NumberImportResponse(BaseModel):
    total_processed: int
    successful_count: int
    failed_count: int
    errors: List[str] = []


class NumberStatusUpdate(BaseModel):
    status: Optional[str] = None
    allocation_eligibility: Optional[str] = None
    hold_reason: Optional[str] = None
    notes: Optional[str] = None


class NumberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    masked_number: str
    carrier: str
    status: str
    decommissioned_at: datetime
    cooling_end_date: datetime
    risk_score: int
    risk_level: str
    allocation_eligibility: str
    provider_count: int = 0
    remediation_percentage: float = 0.0
    hold_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class NotificationBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider_id: str
    provider_name: str
    provider_category: str
    pseudonym_ref: str
    status: str
    sent_at: datetime
    acknowledged_at: Optional[datetime] = None
    remediated_at: Optional[datetime] = None
    error_message: Optional[str] = None


class RiskFactorBreakdown(BaseModel):
    name: str
    weight: int
    score_contribution: int
    description: str


class NumberDetailOut(NumberOut):
    notifications: List[NotificationBrief] = []
    risk_factors: List[RiskFactorBreakdown] = []
    audit_events: List["AuditLogOut"] = []


# ===========================================================================
# Mobile Number (canonical registry)
# ===========================================================================

class MobileNumberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    phone_hash: str
    masked_number: str
    country_code: str
    carrier: str
    circle: Optional[str] = None
    number_type: str
    lifecycle_status: str
    total_recycling_count: int
    first_seen_at: datetime
    last_decommissioned_at: Optional[datetime] = None
    last_reallocated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class MobileNumberCreate(BaseModel):
    raw_phone: str = Field(..., description="E.164 phone number e.g. +919876543210")
    carrier: str
    circle: Optional[str] = None
    number_type: str = "POSTPAID"


# ===========================================================================
# Lifecycle Events
# ===========================================================================

class LifecycleEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    mobile_number_id: str
    event_type: str
    from_status: Optional[str] = None
    to_status: str
    triggered_by: str
    triggered_by_role: Optional[str] = None
    correlation_id: str
    payload: Optional[str] = None
    notes: Optional[str] = None
    occurred_at: datetime


class LifecycleTransitionRequest(BaseModel):
    """Request to trigger a lifecycle state transition."""
    # NUMBER_DECOMMISSIONED, COOLING_STARTED, PROVIDER_NOTIFIED,
    # PROVIDER_ACKNOWLEDGED, COOLING_COMPLETED, MANUAL_REVIEW_TRIGGERED,
    # MANUAL_REVIEW_RESOLVED, ALLOCATION_APPROVED, ALLOCATION_BLOCKED, NUMBER_REALLOCATED
    event_type: str
    notes: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class StatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    mobile_number_id: str
    previous_status: Optional[str] = None
    new_status: str
    change_reason: Optional[str] = None
    changed_by: str
    changed_at: datetime


# ===========================================================================
# Decommissioning Cases
# ===========================================================================

class CaseCreate(BaseModel):
    mobile_number_id: str
    priority: str = "NORMAL"
    case_type: str = "STANDARD"
    assigned_to: Optional[str] = None
    sla_hours: Optional[int] = 72  # Hours until SLA breach


class CaseUpdate(BaseModel):
    case_status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    dispute_flag: Optional[bool] = None
    dispute_reason: Optional[str] = None
    resolution_notes: Optional[str] = None


class CaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_number: str
    mobile_number_id: str
    case_status: str
    priority: str
    case_type: str
    assigned_to: Optional[str] = None
    organization_id: Optional[str] = None
    dispute_flag: bool
    dispute_reason: Optional[str] = None
    dispute_filed_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    sla_due_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class RemediationActionCreate(BaseModel):
    action_type: str
    description: str
    evidence_ref: Optional[str] = None


class RemediationActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    action_type: str
    description: str
    performed_by: str
    performed_at: datetime
    result: str
    evidence_ref: Optional[str] = None


class CaseDetailOut(CaseOut):
    remediation_actions: List[RemediationActionOut] = []


# ===========================================================================
# Cooling Periods
# ===========================================================================

class CoolingPeriodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    mobile_number_id: str
    cooling_rule_id: Optional[str] = None
    status: str
    started_at: datetime
    scheduled_end_at: datetime
    actual_end_at: Optional[datetime] = None
    extended_by_days: int
    extension_reason: Optional[str] = None
    bypass_reason: Optional[str] = None
    bypassed_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CoolingExtendRequest(BaseModel):
    extend_by_days: int = Field(..., ge=1, le=365)
    reason: str


# ===========================================================================
# Risk Rules
# ===========================================================================

class RiskRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    category: str
    description: Optional[str] = None
    base_weight: int
    multiplier: float
    threshold_value: Optional[float] = None
    threshold_operator: str
    is_active: bool
    is_blocking: bool
    severity: str
    created_at: datetime
    updated_at: datetime


class RiskRuleCreate(BaseModel):
    name: str
    code: str
    category: str
    description: Optional[str] = None
    base_weight: int = 10
    multiplier: float = 1.0
    threshold_value: Optional[float] = None
    threshold_operator: str = "gte"
    is_blocking: bool = False
    severity: str = "MEDIUM"


class RiskRuleUpdate(BaseModel):
    name: Optional[str] = None
    base_weight: Optional[int] = None
    multiplier: Optional[float] = None
    threshold_value: Optional[float] = None
    is_active: Optional[bool] = None
    is_blocking: Optional[bool] = None
    severity: Optional[str] = None


# ===========================================================================
# Service Providers
# ===========================================================================

class ServiceProviderCreate(BaseModel):
    name: str
    code: str
    category: str
    integration_type: str = "WEBHOOK"
    webhook_url: Optional[str] = None
    avg_sla_hours: float = 24.0


class ServiceProviderUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    integration_type: Optional[str] = None
    webhook_url: Optional[str] = None
    status: Optional[str] = None
    avg_sla_hours: Optional[float] = None


class ServiceProviderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    category: str
    integration_type: str
    webhook_url: Optional[str] = None
    status: str
    avg_sla_hours: float
    notification_count: int
    unresolved_count: int
    last_sync_at: datetime
    created_at: datetime


class ProviderIntegrationCreate(BaseModel):
    integration_name: str
    protocol: str = "WEBHOOK"
    endpoint_url: Optional[str] = None
    auth_type: str = "BEARER"
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_backoff_seconds: int = 60


class ProviderIntegrationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider_id: str
    integration_name: str
    protocol: str
    endpoint_url: Optional[str] = None
    auth_type: str
    credential_hint: Optional[str] = None
    timeout_seconds: int
    max_retries: int
    retry_backoff_seconds: int
    is_active: bool
    last_tested_at: Optional[datetime] = None
    last_test_result: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ===========================================================================
# Notifications & Responses
# ===========================================================================

class NotificationAcknowledgeRequest(BaseModel):
    status: str = Field("REMEDIATED", description="ACKNOWLEDGED or REMEDIATED")
    response_payload: Optional[str] = None


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    number_id: str
    masked_number: Optional[str] = None
    provider_id: str
    provider_name: str
    provider_category: str
    pseudonym_ref: str
    notification_type: str
    status: str
    sent_at: datetime
    acknowledged_at: Optional[datetime] = None
    remediated_at: Optional[datetime] = None
    retry_count: int
    error_message: Optional[str] = None


class ProviderResponseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    notification_id: str
    response_type: str
    status_reported: Optional[str] = None
    payload: Optional[str] = None
    http_status_code: Optional[int] = None
    responder_id: Optional[str] = None
    notes: Optional[str] = None
    received_at: datetime


# ===========================================================================
# Allocation Decisions
# ===========================================================================

class AllocationDecisionCreate(BaseModel):
    mobile_number_id: str
    decision: str  # APPROVED, BLOCKED, DEFERRED, MANUAL_OVERRIDE_APPROVED
    decision_notes: Optional[str] = None
    override_justification: Optional[str] = None


class AllocationDecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    decision_number: str
    mobile_number_id: str
    decision: str
    risk_score_at_decision: int
    risk_level_at_decision: str
    cooling_completed: bool
    banking_cleared: bool
    all_providers_cleared: bool
    decided_by: str
    decided_by_role: str
    decision_notes: Optional[str] = None
    override_justification: Optional[str] = None
    decided_at: datetime


# ===========================================================================
# Webhook Events
# ===========================================================================

class WebhookEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    direction: str
    provider_id: Optional[str] = None
    notification_id: Optional[str] = None
    event_type: str
    target_url: Optional[str] = None
    http_method: str
    http_status_code: Optional[int] = None
    latency_ms: Optional[int] = None
    delivery_status: str
    attempt_number: int
    next_retry_at: Optional[datetime] = None
    error_message: Optional[str] = None
    triggered_at: datetime


# ===========================================================================
# Notification Templates
# ===========================================================================

class NotificationTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    template_type: str
    subject: Optional[str] = None
    body: str
    available_variables: Optional[str] = None
    category: str
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime


# ===========================================================================
# System Settings
# ===========================================================================

class SystemSettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    key: str
    value: str
    value_type: str
    category: str
    description: Optional[str] = None
    is_sensitive: bool
    is_readonly: bool
    updated_by: Optional[str] = None
    updated_at: datetime
    created_at: datetime


class SystemSettingUpdate(BaseModel):
    value: str
    description: Optional[str] = None


# ===========================================================================
# Cooling Rules
# ===========================================================================

class CoolingRuleCreate(BaseModel):
    name: str
    carrier: str = "ALL"
    category: str = "STANDARD"
    min_cooling_days: int = 60
    risk_extension_days: int = 30
    auto_extend_on_overdue: bool = True
    release_condition: Optional[str] = "Zero high-risk alerts and cooling elapsed"


class CoolingRuleUpdate(BaseModel):
    name: Optional[str] = None
    min_cooling_days: Optional[int] = None
    risk_extension_days: Optional[int] = None
    auto_extend_on_overdue: Optional[bool] = None
    is_active: Optional[bool] = None
    release_condition: Optional[str] = None


class CoolingRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    carrier: str
    category: str
    min_cooling_days: int
    risk_extension_days: int
    auto_extend_on_overdue: bool
    is_active: bool
    release_condition: str
    created_at: datetime


# ===========================================================================
# Risk Engine
# ===========================================================================

class RiskOverrideRequest(BaseModel):
    new_risk_score: int
    reason: str


class RiskSimulationRequest(BaseModel):
    has_banking_service: bool = True
    has_fintech_service: bool = True
    unacknowledged_providers_count: int = 2
    cooling_days_elapsed: int = 45
    min_cooling_required: int = 60
    prior_recycling_count: int = 0


class RiskSimulationResponse(BaseModel):
    simulated_score: int
    simulated_level: str
    recommended_eligibility: str
    breakdown: List[RiskFactorBreakdown]


# ===========================================================================
# Readiness
# ===========================================================================

class ReadinessReleaseRequest(BaseModel):
    number_ids: List[str]
    notes: Optional[str] = None


class ReadinessSummaryOut(BaseModel):
    total_eligible: int
    total_cooling_hold: int
    total_blocked: int
    total_manual_review: int
    blocked_reasons: Dict[str, int]


# ===========================================================================
# Audit
# ===========================================================================

class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_email: str
    actor_role: str
    organization_name: str
    action: str
    entity_type: str
    entity_id: str
    correlation_id: str
    ip_address: str
    result: str
    details: Optional[str] = None
    timestamp: datetime


# ===========================================================================
# Analytics & Dashboard
# ===========================================================================

class DashboardKPIs(BaseModel):
    total_numbers_managed: int
    decommissioned_numbers: int
    in_cooling_period: int
    high_risk_numbers: int
    ready_for_reallocation: int
    pending_provider_responses: int
    critical_alerts: int
    avg_remediation_hours: float
    risk_distribution: Dict[str, int]
    lifecycle_trend: List[Dict[str, Any]]
    recent_activity: List[AuditLogOut]


# ===========================================================================
# Organization Management
# ===========================================================================

class OrganizationCreate(BaseModel):
    name: str
    org_type: str = Field(..., description="PLATFORM, TELECOM, BANK, FINTECH, ECOMMERCE, MOBILITY, REGULATOR, AUDITOR_ORGANIZATION")
    domain: Optional[str] = None
    primary_contact: Optional[str] = None
    country_code: str = "IN"
    allowed_modules: Optional[List[str]] = None

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    org_type: Optional[str] = None
    domain: Optional[str] = None
    primary_contact: Optional[str] = None
    is_active: Optional[bool] = None
    allowed_modules: Optional[List[str]] = None

class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    org_type: str
    domain: Optional[str] = None
    primary_contact: Optional[str] = None
    country_code: str
    is_active: bool
    allowed_modules: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    user_count: Optional[int] = 0
    number_count: Optional[int] = 0


# Rebuild forward references
Token.model_rebuild()
NumberDetailOut.model_rebuild()
