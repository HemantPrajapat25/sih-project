"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { User, Role, Permission, OrganizationType, getDashboardPath } from "@/types";
import { api } from "@/lib/api";

const ROLE_PERMISSIONS_MAP: Record<Role, Permission[]> = {
  SUPER_ADMIN: [
    "numbers.read", "numbers.import", "numbers.update", "numbers.reallocate",
    "risk.read", "risk.override", "providers.manage", "notifications.send",
    "notifications.acknowledge", "audit.read", "integrations.manage",
    "users.manage", "settings.manage",
  ],
  TELECOM_ADMIN: [
    "numbers.read", "numbers.import", "numbers.update", "numbers.reallocate",
    "risk.read", "risk.override", "providers.manage", "notifications.send",
    "audit.read", "integrations.manage", "users.manage", "settings.manage",
  ],
  TELECOM_OPERATOR: [
    "numbers.read", "numbers.import", "numbers.update",
    "risk.read", "notifications.send", "audit.read",
  ],
  SERVICE_PROVIDER_ADMIN: [
    "numbers.read", "notifications.acknowledge", "providers.manage",
    "integrations.manage", "audit.read", "settings.manage",
  ],
  SERVICE_PROVIDER_OPERATOR: [
    "numbers.read", "notifications.acknowledge", "audit.read",
  ],
  AUDITOR: ["numbers.read", "risk.read", "audit.read"],
  ANALYST: ["numbers.read", "risk.read", "audit.read"],
};

interface DemoPersona {
  full_name: string;
  email: string;
  organization_name: string;
  organization_type: OrganizationType;
}

const DEMO_PERSONAS: Record<Role, DemoPersona> = {
  SUPER_ADMIN: {
    full_name: "Arjun Mehta (Platform Admin)",
    email: "superadmin@numberguard.demo",
    organization_name: "NumberGuard Platform",
    organization_type: "PLATFORM",
  },
  TELECOM_ADMIN: {
    full_name: "Rajesh Sharma (Telecom Admin)",
    email: "telecom.admin@demotel.demo",
    organization_name: "DemoTel Telecom",
    organization_type: "TELECOM",
  },
  TELECOM_OPERATOR: {
    full_name: "Priya Nair (Carrier Ops)",
    email: "operator@demotel.demo",
    organization_name: "DemoTel Telecom",
    organization_type: "TELECOM",
  },
  SERVICE_PROVIDER_ADMIN: {
    full_name: "Vikram Singh (Bank Lead)",
    email: "bank.admin@securebank.demo",
    organization_name: "SecureBank Ltd",
    organization_type: "BANK",
  },
  SERVICE_PROVIDER_OPERATOR: {
    full_name: "Ananya Patel (SecOps)",
    email: "bank.operator@securebank.demo",
    organization_name: "SecureBank Ltd",
    organization_type: "BANK",
  },
  AUDITOR: {
    full_name: "Kavitha Reddy (Compliance)",
    email: "auditor@numberguard.demo",
    organization_name: "Deloitte Compliance Bureau",
    organization_type: "AUDITOR_ORGANIZATION",
  },
  ANALYST: {
    full_name: "Suresh Iyer (Risk Analyst)",
    email: "analyst@numberguard.demo",
    organization_name: "NumberGuard Analytics",
    organization_type: "PLATFORM",
  },
};

interface AuthContextType {
  user: User | null;
  role: Role;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  switchDemoRole: (role: Role) => Promise<void>;
  logout: () => void;
  hasPermission: (perm: Permission) => boolean;
  getDashboard: () => string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [role, setRole] = useState<Role>("TELECOM_ADMIN");
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    async function initAuth() {
      try {
        const savedToken = localStorage.getItem("ng_access_token");
        const savedRole = localStorage.getItem("ng_user_role") as Role;
        if (savedToken && savedRole) {
          setToken(savedToken);
          setRole(savedRole);
          try {
            const me = await api.getMe();
            setUser(me);
            setRole(me.role as Role);
          } catch {
            await autoDemoLogin(savedRole || "TELECOM_ADMIN");
          }
        } else {
          await autoDemoLogin("TELECOM_ADMIN");
        }
      } catch (err) {
        console.error("Auth init error:", err);
      } finally {
        setIsLoading(false);
      }
    }
    initAuth();
  }, []);

  async function autoDemoLogin(targetRole: Role) {
    try {
      const resp = await api.demoLogin(targetRole);
      setToken(resp.access_token);
      setRole(resp.role);
      setUser(resp.user);
      localStorage.setItem("ng_access_token", resp.access_token);
      localStorage.setItem("ng_user_role", resp.role);
    } catch {
      const persona = DEMO_PERSONAS[targetRole];
      const mockUser: User = {
        id: `usr-demo-${targetRole.toLowerCase()}`,
        email: persona.email,
        full_name: persona.full_name,
        role: targetRole,
        organization_name: persona.organization_name,
        organization_type: persona.organization_type,
        is_active: true,
        created_at: new Date().toISOString(),
      };
      setUser(mockUser);
      setRole(targetRole);
      setToken("mock_jwt_token");
    }
  }

  async function login(email: string, pass: string) {
    setIsLoading(true);
    try {
      const resp = await api.login(email, pass);
      setToken(resp.access_token);
      setRole(resp.role);
      setUser(resp.user);
      localStorage.setItem("ng_access_token", resp.access_token);
      localStorage.setItem("ng_user_role", resp.role);
    } finally {
      setIsLoading(false);
    }
  }

  async function switchDemoRole(targetRole: Role) {
    setIsLoading(true);
    try {
      const resp = await api.demoLogin(targetRole);
      setToken(resp.access_token);
      setRole(resp.role);
      setUser(resp.user);
      localStorage.setItem("ng_access_token", resp.access_token);
      localStorage.setItem("ng_user_role", resp.role);
    } catch {
      await autoDemoLogin(targetRole);
    } finally {
      setIsLoading(false);
    }
  }

  function logout() {
    setUser(null);
    setToken(null);
    localStorage.removeItem("ng_access_token");
    localStorage.removeItem("ng_user_role");
  }

  function hasPermission(perm: Permission): boolean {
    if (!role) return false;
    return (ROLE_PERMISSIONS_MAP[role] || []).includes(perm);
  }

  function getDashboard(): string {
    return getDashboardPath(role);
  }

  return (
    <AuthContext.Provider
      value={{
        user, role, token,
        isAuthenticated: !!user,
        isLoading, login, switchDemoRole, logout,
        hasPermission, getDashboard,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
