import {
  TokenResponse,
  DemoRoleAccount,
  NumberRecord,
  NumberDetail,
  ServiceProvider,
  NotificationRecord,
  CoolingRule,
  DashboardKPIs,
  ReadinessSummary,
  AuditRecord,
  User,
  Role
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAuthHeader(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("ng_access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      errorDetail = data.detail || data.message || JSON.stringify(data);
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // Auth
  async login(email: string, password: string): Promise<TokenResponse> {
    const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    return handleResponse<TokenResponse>(res);
  },

  async demoLogin(role: Role): Promise<TokenResponse> {
    const res = await fetch(`${API_BASE}/api/v1/auth/demo-login?role=${role}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    return handleResponse<TokenResponse>(res);
  },

  async getDemoRoles(): Promise<DemoRoleAccount[]> {
    const res = await fetch(`${API_BASE}/api/v1/auth/demo-roles`);
    return handleResponse<DemoRoleAccount[]>(res);
  },

  async getMe(): Promise<User> {
    const res = await fetch(`${API_BASE}/api/v1/auth/me`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<User>(res);
  },

  // Dashboard
  async getDashboardMetrics(): Promise<DashboardKPIs> {
    const res = await fetch(`${API_BASE}/api/v1/analytics/dashboard`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<DashboardKPIs>(res);
  },

  // Numbers
  async getNumbers(params?: {
    search?: string;
    carrier?: string;
    status?: string;
    risk_level?: string;
    eligibility?: string;
    limit?: number;
    skip?: number;
  }): Promise<NumberRecord[]> {
    const q = new URLSearchParams();
    if (params?.search) q.set("search", params.search);
    if (params?.carrier) q.set("carrier", params.carrier);
    if (params?.status) q.set("status", params.status);
    if (params?.risk_level) q.set("risk_level", params.risk_level);
    if (params?.eligibility) q.set("eligibility", params.eligibility);
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.skip) q.set("skip", String(params.skip));

    const res = await fetch(`${API_BASE}/api/v1/numbers?${q.toString()}`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<NumberRecord[]>(res);
  },

  async getNumberDetail(id: string): Promise<NumberDetail> {
    const res = await fetch(`${API_BASE}/api/v1/numbers/${id}`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<NumberDetail>(res);
  },

  async createNumber(data: {
    raw_phone: string;
    carrier: string;
    notes?: string;
    custom_cooling_days?: number;
    associated_provider_codes?: string[];
  }): Promise<NumberRecord> {
    const res = await fetch(`${API_BASE}/api/v1/numbers`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeader() },
      body: JSON.stringify(data),
    });
    return handleResponse<NumberRecord>(res);
  },

  async importNumbers(numbers: Array<{ raw_phone: string; carrier: string; notes?: string }>): Promise<{
    total_processed: number;
    successful_count: number;
    failed_count: number;
    errors: string[];
  }> {
    const res = await fetch(`${API_BASE}/api/v1/numbers/import`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeader() },
      body: JSON.stringify({ numbers }),
    });
    return handleResponse(res);
  },

  async updateNumberStatus(
    id: string,
    data: {
      status?: string;
      allocation_eligibility?: string;
      hold_reason?: string;
      notes?: string;
    }
  ): Promise<NumberRecord> {
    const res = await fetch(`${API_BASE}/api/v1/numbers/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...getAuthHeader() },
      body: JSON.stringify(data),
    });
    return handleResponse<NumberRecord>(res);
  },

  async overrideRiskScore(numberId: string, newRiskScore: number, reason: string): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/risk/override/${numberId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeader() },
      body: JSON.stringify({ new_risk_score: newRiskScore, reason }),
    });
    return handleResponse(res);
  },

  // Service Providers
  async getProviders(params?: { category?: string; status?: string }): Promise<ServiceProvider[]> {
    const q = new URLSearchParams();
    if (params?.category) q.set("category", params.category);
    if (params?.status) q.set("status", params.status);

    const res = await fetch(`${API_BASE}/api/v1/providers?${q.toString()}`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<ServiceProvider[]>(res);
  },

  async pingProvider(id: string): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/providers/${id}/ping`, {
      method: "POST",
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  // Notifications
  async getNotifications(params?: { status?: string; provider_id?: string }): Promise<NotificationRecord[]> {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    if (params?.provider_id) q.set("provider_id", params.provider_id);

    const res = await fetch(`${API_BASE}/api/v1/notifications?${q.toString()}`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<NotificationRecord[]>(res);
  },

  async acknowledgeNotification(id: string, status: "ACKNOWLEDGED" | "REMEDIATED"): Promise<NotificationRecord> {
    const res = await fetch(`${API_BASE}/api/v1/notifications/${id}/acknowledge`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeader() },
      body: JSON.stringify({ status }),
    });
    return handleResponse<NotificationRecord>(res);
  },

  // Cooling Rules
  async getCoolingRules(): Promise<CoolingRule[]> {
    const res = await fetch(`${API_BASE}/api/v1/cooling`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<CoolingRule[]>(res);
  },

  // Readiness
  async getReadinessSummary(): Promise<ReadinessSummary> {
    const res = await fetch(`${API_BASE}/api/v1/readiness/summary`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<ReadinessSummary>(res);
  },

  async batchReleaseNumbers(numberIds: string[], notes?: string): Promise<{ released_count: number }> {
    const res = await fetch(`${API_BASE}/api/v1/readiness/batch-release`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeader() },
      body: JSON.stringify({ number_ids: numberIds, notes }),
    });
    return handleResponse(res);
  },

  // Audit Logs
  async getAuditLogs(params?: { search?: string; action?: string; limit?: number }): Promise<AuditRecord[]> {
    const q = new URLSearchParams();
    if (params?.search) q.set("search", params.search);
    if (params?.action) q.set("action", params.action);
    if (params?.limit) q.set("limit", String(params.limit));

    const res = await fetch(`${API_BASE}/api/v1/audit?${q.toString()}`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<AuditRecord[]>(res);
  },

  // Integrations
  async getIntegrationsStatus(): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/integrations/status`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  // Users & RBAC
  async getUsers(): Promise<User[]> {
    const res = await fetch(`${API_BASE}/api/v1/users`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse<User[]>(res);
  },

  async getRbacMatrix(): Promise<Record<string, string[]>> {
    const res = await fetch(`${API_BASE}/api/v1/users/rbac-matrix`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  // --- Phase 3: Modular Risk Engine ---
  async assessNumberRisk(numberId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/risk/assess/${numberId}`, {
      method: "POST",
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  async getRiskWeights(): Promise<{ weights: Record<string, number>; total_weight: number }> {
    const res = await fetch(`${API_BASE}/api/v1/risk/weights`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  async getRiskRules(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/api/v1/risk/rules`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  // --- Phase 3: API Key Management ---
  async listApiKeys(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/api/v1/api-keys`, {
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  async createApiKey(payload: { name: string; scopes?: string; expires_in_days?: number }): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/api-keys`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeader() },
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  async rotateApiKey(keyId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/api-keys/${keyId}/rotate`, {
      method: "POST",
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  async revokeApiKey(keyId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/api-keys/${keyId}`, {
      method: "DELETE",
      headers: { ...getAuthHeader() },
    });
    return handleResponse(res);
  },

  // --- Phase 3: Mock Adapters ---
  async triggerMockProviderEvent(providerCategory: string, payload: any): Promise<any> {
    const cat = providerCategory.toLowerCase();
    const endpoint = cat === "fintech" ? "fintech" : cat === "ecommerce" ? "ecommerce" : "bank";
    const res = await fetch(`${API_BASE}/api/v1/mock/${endpoint}/decommission-event`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  async resetMockState(): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/mock/reset`, {
      method: "POST",
    });
    return handleResponse(res);
  },
};
