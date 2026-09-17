export type Role =
  | "SUPER_ADMIN"
  | "TELECOM_ADMIN"
  | "TELECOM_OPERATOR"
  | "SERVICE_PROVIDER_ADMIN"
  | "SERVICE_PROVIDER_OPERATOR"
  | "AUDITOR"
  | "ANALYST";

export type OrganizationType =
  | "PLATFORM"
  | "TELECOM"
  | "BANK"
  | "FINTECH"
  | "ECOMMERCE"
  | "MOBILITY"
  | "OTHER_SERVICE_PROVIDER"
  | "AUDITOR_ORGANIZATION";

/** Returns the dedicated home dashboard path for a given role. */
export function getDashboardPath(role: Role): string {
  switch (role) {
    case "SUPER_ADMIN":      return "/platform/dashboard";
    case "TELECOM_ADMIN":    return "/telecom/dashboard";
    case "TELECOM_OPERATOR": return "/telecom/operations";
    case "SERVICE_PROVIDER_ADMIN":    return "/provider/dashboard";
    case "SERVICE_PROVIDER_OPERATOR": return "/provider/tasks";
    case "ANALYST":  return "/analytics/dashboard";
    case "AUDITOR":  return "/audit/dashboard";
    default:         return "/telecom/dashboard";
  }
}

export type Permission =
  | "numbers.read"
  | "numbers.import"
  | "numbers.update"
  | "numbers.reallocate"
  | "risk.read"
  | "risk.override"
  | "providers.manage"
  | "notifications.send"
  | "notifications.acknowledge"
  | "audit.read"
  | "integrations.manage"
  | "users.manage"
  | "settings.manage";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  organization_id?: string | null;
  organization_name?: string | null;
  organization_type?: OrganizationType | null;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: Role;
  user: User;
}

export interface DemoRoleAccount {
  email: string;
  role: Role;
  name: string;
  org: string;
  permissions: Permission[];
}

export interface NumberRecord {
  id: string;
  masked_number: string;
  carrier: string;
  status: "DECOMMISSIONED" | "NOTIFYING_PROVIDERS" | "COOLING_HOLD" | "MANUAL_REVIEW" | "ELIGIBLE" | "REALLOCATED";
  decommissioned_at: string;
  cooling_end_date: string;
  risk_score: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  allocation_eligibility: "ELIGIBLE" | "COOLING_HOLD" | "BLOCKED" | "MANUAL_REVIEW_REQUIRED" | "REALLOCATED";
  provider_count: number;
  remediation_percentage: number;
  hold_reason?: string | null;
  created_at: string;
  updated_at: string;
}

export interface NotificationBrief {
  id: string;
  provider_id: string;
  provider_name: string;
  provider_category: string;
  pseudonym_ref: string;
  status: "PENDING" | "SENT" | "ACKNOWLEDGED" | "REMEDIATED" | "FAILED";
  sent_at: string;
  acknowledged_at?: string | null;
  remediated_at?: string | null;
  error_message?: string | null;
}

export interface RiskFactor {
  name: string;
  weight: number;
  score_contribution: number;
  description: string;
}

export interface AuditRecord {
  id: string;
  actor_email: string;
  actor_role: string;
  organization_name: string;
  action: string;
  entity_type: string;
  entity_id: string;
  correlation_id: string;
  ip_address: string;
  result: "SUCCESS" | "FAILED" | "WARNING";
  details?: string | null;
  timestamp: string;
}

export interface NumberDetail extends NumberRecord {
  notifications: NotificationBrief[];
  risk_factors: RiskFactor[];
  audit_events: AuditRecord[];
}

export interface ServiceProvider {
  id: string;
  name: string;
  code: string;
  category: "BANKING" | "FINTECH" | "ECOMMERCE" | "IDENTITY" | "SOCIAL" | "GENERAL";
  integration_type: "WEBHOOK" | "REST_API" | "SFTP" | "MANUAL" | "MOCK";
  webhook_url?: string | null;
  status: "ACTIVE" | "INACTIVE" | "DEGRADED";
  avg_sla_hours: number;
  notification_count: number;
  unresolved_count: number;
  last_sync_at: string;
  created_at: string;
}

export interface NotificationRecord {
  id: string;
  number_id: string;
  masked_number?: string | null;
  provider_id: string;
  provider_name: string;
  provider_category: string;
  pseudonym_ref: string;
  notification_type: string;
  status: "PENDING" | "SENT" | "ACKNOWLEDGED" | "REMEDIATED" | "FAILED";
  sent_at: string;
  acknowledged_at?: string | null;
  remediated_at?: string | null;
  retry_count: number;
  error_message?: string | null;
}

export interface CoolingRule {
  id: string;
  name: string;
  carrier: string;
  category: "STANDARD" | "BANKING_ASSOCIATED" | "HIGH_RISK" | "CUSTOM";
  min_cooling_days: number;
  risk_extension_days: number;
  auto_extend_on_overdue: boolean;
  is_active: boolean;
  release_condition: string;
  created_at: string;
}

export interface DashboardKPIs {
  total_numbers_managed: number;
  decommissioned_numbers: number;
  in_cooling_period: number;
  high_risk_numbers: number;
  ready_for_reallocation: number;
  pending_provider_responses: number;
  critical_alerts: number;
  avg_remediation_hours: number;
  risk_distribution: {
    LOW: number;
    MEDIUM: number;
    HIGH: number;
    CRITICAL: number;
  };
  lifecycle_trend: Array<{
    month: string;
    decommissioned: number;
    cooling: number;
    reallocated: number;
  }>;
  recent_activity: AuditRecord[];
}

export interface ReadinessSummary {
  total_eligible: number;
  total_cooling_hold: number;
  total_blocked: number;
  total_manual_review: number;
  blocked_reasons: Record<string, number>;
}
