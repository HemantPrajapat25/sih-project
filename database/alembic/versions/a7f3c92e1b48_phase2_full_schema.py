"""phase2_full_schema

Full DDL for all 22 NumberGuard database tables.
Includes all new Phase 2 entities plus ensures existing tables exist.

Revision ID: a7f3c92e1b48
Revises: 5b0bbf7af3ed
Create Date: 2026-09-10

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a7f3c92e1b48"
down_revision: Union[str, Sequence[str], None] = "5b0bbf7af3ed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Core identity tables (create if not exist pattern via checkfirst)
    # ------------------------------------------------------------------
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("org_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), server_default="ACTIVE"),
        sa.Column("contact_email", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        if_not_exists=True,
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_system_role", sa.Boolean, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        if_not_exists=True,
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        if_not_exists=True,
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(128), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(128), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        if_not_exists=True,
    )

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("role_id", sa.String(36), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_id", sa.String(36), sa.ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("granted_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
        if_not_exists=True,
    )

    op.create_table(
        "user_roles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", sa.String(36), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("assigned_by", sa.String(36), nullable=True),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
        if_not_exists=True,
    )

    op.create_table(
        "organization_users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("membership_role", sa.String(32), server_default="MEMBER"),
        sa.Column("joined_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("is_primary", sa.Boolean, server_default=sa.true()),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_org_user"),
        if_not_exists=True,
    )

    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("key_prefix", sa.String(12), nullable=False),
        sa.Column("hashed_key", sa.String(255), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("last_used_at", sa.DateTime, nullable=True),
        if_not_exists=True,
    )

    # ------------------------------------------------------------------
    # Service providers
    # ------------------------------------------------------------------
    op.create_table(
        "service_providers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("code", sa.String(32), nullable=False, unique=True),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("integration_type", sa.String(32), server_default="WEBHOOK"),
        sa.Column("webhook_url", sa.String(512), nullable=True),
        sa.Column("status", sa.String(32), server_default="ACTIVE"),
        sa.Column("avg_sla_hours", sa.Float, server_default="24.0"),
        sa.Column("notification_count", sa.Integer, server_default="0"),
        sa.Column("unresolved_count", sa.Integer, server_default="0"),
        sa.Column("last_sync_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        if_not_exists=True,
    )

    op.create_table(
        "provider_integrations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider_id", sa.String(36), sa.ForeignKey("service_providers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("integration_name", sa.String(128), nullable=False),
        sa.Column("protocol", sa.String(32), server_default="WEBHOOK"),
        sa.Column("endpoint_url", sa.String(512), nullable=True),
        sa.Column("auth_type", sa.String(32), server_default="BEARER"),
        sa.Column("credential_hint", sa.String(64), nullable=True),
        sa.Column("hashed_secret", sa.String(255), nullable=True),
        sa.Column("timeout_seconds", sa.Integer, server_default="30"),
        sa.Column("max_retries", sa.Integer, server_default="3"),
        sa.Column("retry_backoff_seconds", sa.Integer, server_default="60"),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.Column("last_tested_at", sa.DateTime, nullable=True),
        sa.Column("last_test_result", sa.String(16), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        if_not_exists=True,
    )

    # ------------------------------------------------------------------
    # Number lifecycle
    # ------------------------------------------------------------------
    op.create_table(
        "cooling_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("carrier", sa.String(32), server_default="ALL"),
        sa.Column("category", sa.String(32), server_default="STANDARD"),
        sa.Column("min_cooling_days", sa.Integer, server_default="60"),
        sa.Column("risk_extension_days", sa.Integer, server_default="30"),
        sa.Column("auto_extend_on_overdue", sa.Boolean, server_default=sa.true()),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.Column("release_condition", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        if_not_exists=True,
    )

    op.create_table(
        "decommissioned_numbers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("phone_hash", sa.String(64), nullable=False, index=True),
        sa.Column("masked_number", sa.String(32), nullable=False),
        sa.Column("carrier", sa.String(32), nullable=False, server_default="Jio"),
        sa.Column("status", sa.String(32), nullable=False, server_default="DECOMMISSIONED"),
        sa.Column("decommissioned_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("cooling_end_date", sa.DateTime, nullable=False),
        sa.Column("risk_score", sa.Integer, server_default="50"),
        sa.Column("risk_level", sa.String(16), server_default="MEDIUM"),
        sa.Column("allocation_eligibility", sa.String(32), server_default="COOLING_HOLD"),
        sa.Column("hold_reason", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        if_not_exists=True,
    )

    op.create_table(
        "provider_notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("number_id", sa.String(36), sa.ForeignKey("decommissioned_numbers.id"), nullable=False, index=True),
        sa.Column("provider_id", sa.String(36), sa.ForeignKey("service_providers.id"), nullable=False),
        sa.Column("pseudonym_ref", sa.String(64), nullable=False, index=True),
        sa.Column("notification_type", sa.String(32), server_default="DECOMMISSION_ALERT"),
        sa.Column("status", sa.String(32), server_default="SENT"),
        sa.Column("sent_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("acknowledged_at", sa.DateTime, nullable=True),
        sa.Column("remediated_at", sa.DateTime, nullable=True),
        sa.Column("retry_count", sa.Integer, server_default="0"),
        sa.Column("response_payload", sa.Text, nullable=True),
        sa.Column("error_message", sa.String(255), nullable=True),
        if_not_exists=True,
    )

    op.create_table(
        "risk_evaluations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("number_id", sa.String(36), sa.ForeignKey("decommissioned_numbers.id"), nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("risk_level", sa.String(16), nullable=False),
        sa.Column("factor_banking_weight", sa.Integer, server_default="0"),
        sa.Column("factor_cooling_weight", sa.Integer, server_default="0"),
        sa.Column("factor_sla_weight", sa.Integer, server_default="0"),
        sa.Column("factor_velocity_weight", sa.Integer, server_default="0"),
        sa.Column("details_json", sa.Text, nullable=True),
        sa.Column("evaluated_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("evaluated_by", sa.String(64), server_default="SYSTEM_RISK_ENGINE"),
        if_not_exists=True,
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("actor_email", sa.String(128), nullable=False),
        sa.Column("actor_role", sa.String(32), nullable=False),
        sa.Column("organization_name", sa.String(128), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("correlation_id", sa.String(64), nullable=False, index=True),
        sa.Column("ip_address", sa.String(45), server_default="127.0.0.1"),
        sa.Column("result", sa.String(16), server_default="SUCCESS"),
        sa.Column("details", sa.Text, nullable=True),
        sa.Column("timestamp", sa.DateTime, server_default=sa.func.now(), index=True),
        if_not_exists=True,
    )

    # ------------------------------------------------------------------
    # Phase 2 new tables
    # ------------------------------------------------------------------
    op.create_table(
        "mobile_numbers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("phone_hash", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("masked_number", sa.String(32), nullable=False),
        sa.Column("country_code", sa.String(8), server_default="+91"),
        sa.Column("carrier", sa.String(32), nullable=False),
        sa.Column("circle", sa.String(64), nullable=True),
        sa.Column("number_type", sa.String(16), server_default="POSTPAID"),
        sa.Column("lifecycle_status", sa.String(32), server_default="ACTIVE"),
        sa.Column("total_recycling_count", sa.Integer, server_default="0"),
        sa.Column("first_seen_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("last_decommissioned_at", sa.DateTime, nullable=True),
        sa.Column("last_reallocated_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        if_not_exists=True,
    )
    op.create_index("ix_mobile_numbers_carrier", "mobile_numbers", ["carrier"], if_not_exists=True)
    op.create_index("ix_mobile_numbers_lifecycle_status", "mobile_numbers", ["lifecycle_status"], if_not_exists=True)

    op.create_table(
        "number_lifecycle_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mobile_number_id", sa.String(36), sa.ForeignKey("mobile_numbers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("event_type", sa.String(64), nullable=False, index=True),
        sa.Column("from_status", sa.String(32), nullable=True),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column("triggered_by", sa.String(64), nullable=False),
        sa.Column("triggered_by_role", sa.String(32), nullable=True),
        sa.Column("correlation_id", sa.String(64), nullable=False, index=True),
        sa.Column("payload", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("occurred_at", sa.DateTime, server_default=sa.func.now(), index=True),
        if_not_exists=True,
    )
    op.create_index("ix_nle_mobile_number_occurred", "number_lifecycle_events", ["mobile_number_id", "occurred_at"], if_not_exists=True)

    op.create_table(
        "number_status_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mobile_number_id", sa.String(36), sa.ForeignKey("mobile_numbers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("previous_status", sa.String(32), nullable=True),
        sa.Column("new_status", sa.String(32), nullable=False),
        sa.Column("change_reason", sa.String(255), nullable=True),
        sa.Column("changed_by", sa.String(64), nullable=False),
        sa.Column("changed_at", sa.DateTime, server_default=sa.func.now(), index=True),
        if_not_exists=True,
    )

    op.create_table(
        "decommissioning_cases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("case_number", sa.String(32), nullable=False, unique=True, index=True),
        sa.Column("mobile_number_id", sa.String(36), sa.ForeignKey("mobile_numbers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("case_status", sa.String(32), server_default="OPEN"),
        sa.Column("priority", sa.String(16), server_default="NORMAL"),
        sa.Column("case_type", sa.String(32), server_default="STANDARD"),
        sa.Column("assigned_to", sa.String(64), nullable=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("dispute_flag", sa.Boolean, server_default=sa.false()),
        sa.Column("dispute_reason", sa.Text, nullable=True),
        sa.Column("dispute_filed_at", sa.DateTime, nullable=True),
        sa.Column("resolution_notes", sa.Text, nullable=True),
        sa.Column("resolved_at", sa.DateTime, nullable=True),
        sa.Column("sla_due_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        if_not_exists=True,
    )
    op.create_index("ix_decomm_cases_status_priority", "decommissioning_cases", ["case_status", "priority"], if_not_exists=True)

    op.create_table(
        "cooling_periods",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mobile_number_id", sa.String(36), sa.ForeignKey("mobile_numbers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("cooling_rule_id", sa.String(36), sa.ForeignKey("cooling_rules.id"), nullable=True),
        sa.Column("status", sa.String(16), server_default="ACTIVE"),
        sa.Column("started_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("scheduled_end_at", sa.DateTime, nullable=False),
        sa.Column("actual_end_at", sa.DateTime, nullable=True),
        sa.Column("extended_by_days", sa.Integer, server_default="0"),
        sa.Column("extension_reason", sa.Text, nullable=True),
        sa.Column("bypass_reason", sa.Text, nullable=True),
        sa.Column("bypassed_by", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        if_not_exists=True,
    )

    op.create_table(
        "risk_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("base_weight", sa.Integer, server_default="10"),
        sa.Column("multiplier", sa.Float, server_default="1.0"),
        sa.Column("condition_expression", sa.Text, nullable=True),
        sa.Column("threshold_value", sa.Float, nullable=True),
        sa.Column("threshold_operator", sa.String(16), server_default="gte"),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.Column("is_blocking", sa.Boolean, server_default=sa.false()),
        sa.Column("severity", sa.String(16), server_default="MEDIUM"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        if_not_exists=True,
    )

    op.create_table(
        "provider_number_associations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider_id", sa.String(36), sa.ForeignKey("service_providers.id"), nullable=False, index=True),
        sa.Column("mobile_number_id", sa.String(36), sa.ForeignKey("mobile_numbers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("association_status", sa.String(32), server_default="ACTIVE"),
        sa.Column("service_type", sa.String(64), nullable=True),
        sa.Column("pseudonym_token", sa.String(64), nullable=False, index=True),
        sa.Column("linked_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("unlinked_at", sa.DateTime, nullable=True),
        sa.Column("unlinked_by", sa.String(64), nullable=True),
        sa.UniqueConstraint("provider_id", "mobile_number_id", name="uq_provider_number"),
        if_not_exists=True,
    )

    op.create_table(
        "provider_responses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("notification_id", sa.String(36), sa.ForeignKey("provider_notifications.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("response_type", sa.String(32), nullable=False),
        sa.Column("status_reported", sa.String(32), nullable=True),
        sa.Column("payload", sa.Text, nullable=True),
        sa.Column("http_status_code", sa.Integer, nullable=True),
        sa.Column("responder_id", sa.String(64), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("received_at", sa.DateTime, server_default=sa.func.now(), index=True),
        if_not_exists=True,
    )

    op.create_table(
        "remediation_actions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("decommissioning_cases.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("performed_by", sa.String(64), nullable=False),
        sa.Column("performed_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("result", sa.String(16), server_default="SUCCESS"),
        sa.Column("evidence_ref", sa.String(255), nullable=True),
        if_not_exists=True,
    )

    op.create_table(
        "allocation_decisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("decision_number", sa.String(32), nullable=False, unique=True, index=True),
        sa.Column("mobile_number_id", sa.String(36), sa.ForeignKey("mobile_numbers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("risk_score_at_decision", sa.Integer, nullable=False),
        sa.Column("risk_level_at_decision", sa.String(16), nullable=False),
        sa.Column("cooling_completed", sa.Boolean, server_default=sa.false()),
        sa.Column("banking_cleared", sa.Boolean, server_default=sa.false()),
        sa.Column("all_providers_cleared", sa.Boolean, server_default=sa.false()),
        sa.Column("decided_by", sa.String(64), nullable=False),
        sa.Column("decided_by_role", sa.String(32), nullable=False),
        sa.Column("decision_notes", sa.Text, nullable=True),
        sa.Column("override_justification", sa.Text, nullable=True),
        sa.Column("decided_at", sa.DateTime, server_default=sa.func.now()),
        if_not_exists=True,
    )

    op.create_table(
        "webhook_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("direction", sa.String(16), server_default="OUTBOUND"),
        sa.Column("provider_id", sa.String(36), sa.ForeignKey("service_providers.id"), nullable=True, index=True),
        sa.Column("notification_id", sa.String(36), sa.ForeignKey("provider_notifications.id"), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("target_url", sa.String(512), nullable=True),
        sa.Column("http_method", sa.String(8), server_default="POST"),
        sa.Column("request_payload", sa.Text, nullable=True),
        sa.Column("response_payload", sa.Text, nullable=True),
        sa.Column("http_status_code", sa.Integer, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("delivery_status", sa.String(16), server_default="PENDING"),
        sa.Column("attempt_number", sa.Integer, server_default="1"),
        sa.Column("next_retry_at", sa.DateTime, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("triggered_at", sa.DateTime, server_default=sa.func.now(), index=True),
        if_not_exists=True,
    )
    op.create_index("ix_webhook_events_provider_status", "webhook_events", ["provider_id", "delivery_status"], if_not_exists=True)

    op.create_table(
        "notification_templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("template_type", sa.String(32), nullable=False),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("available_variables", sa.Text, nullable=True),
        sa.Column("category", sa.String(32), server_default="GENERAL"),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.Column("version", sa.Integer, server_default="1"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        if_not_exists=True,
    )

    op.create_table(
        "system_settings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key", sa.String(128), nullable=False, unique=True, index=True),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("value_type", sa.String(16), server_default="string"),
        sa.Column("category", sa.String(32), server_default="GENERAL"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_sensitive", sa.Boolean, server_default=sa.false()),
        sa.Column("is_readonly", sa.Boolean, server_default=sa.false()),
        sa.Column("updated_by", sa.String(64), nullable=True),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        if_not_exists=True,
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("system_settings", if_exists=True)
    op.drop_table("notification_templates", if_exists=True)
    op.drop_index("ix_webhook_events_provider_status", if_exists=True)
    op.drop_table("webhook_events", if_exists=True)
    op.drop_table("allocation_decisions", if_exists=True)
    op.drop_table("remediation_actions", if_exists=True)
    op.drop_table("provider_responses", if_exists=True)
    op.drop_table("provider_number_associations", if_exists=True)
    op.drop_table("risk_rules", if_exists=True)
    op.drop_table("cooling_periods", if_exists=True)
    op.drop_index("ix_decomm_cases_status_priority", if_exists=True)
    op.drop_table("decommissioning_cases", if_exists=True)
    op.drop_table("number_status_history", if_exists=True)
    op.drop_index("ix_nle_mobile_number_occurred", if_exists=True)
    op.drop_table("number_lifecycle_events", if_exists=True)
    op.drop_index("ix_mobile_numbers_lifecycle_status", if_exists=True)
    op.drop_index("ix_mobile_numbers_carrier", if_exists=True)
    op.drop_table("mobile_numbers", if_exists=True)
    op.drop_table("risk_evaluations", if_exists=True)
    op.drop_table("provider_notifications", if_exists=True)
    op.drop_table("decommissioned_numbers", if_exists=True)
    op.drop_table("cooling_rules", if_exists=True)
    op.drop_table("audit_logs", if_exists=True)
    op.drop_table("provider_integrations", if_exists=True)
    op.drop_table("service_providers", if_exists=True)
    op.drop_table("api_keys", if_exists=True)
    op.drop_table("organization_users", if_exists=True)
    op.drop_table("user_roles", if_exists=True)
    op.drop_table("role_permissions", if_exists=True)
    op.drop_table("users", if_exists=True)
    op.drop_table("permissions", if_exists=True)
    op.drop_table("roles", if_exists=True)
    op.drop_table("organizations", if_exists=True)
