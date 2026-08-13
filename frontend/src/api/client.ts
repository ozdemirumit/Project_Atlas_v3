export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail ?? detail;
    } catch {
      // response had no JSON body
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export interface HealthStatus {
  status: "ok" | "degraded";
  database: "ok" | "unavailable";
}

export interface CurrentSubject {
  subject_id: string;
  display_name: string;
  identity_source: "local" | "ldap" | "development";
  permissions: string[];
}

export interface AuditEventSummary {
  id: string;
  occurred_at: string;
  event_type: string;
  outcome: string;
  subject_id: string | null;
  correlation_id: string;
}

export const api = {
  health: () => request<HealthStatus>("/health"),
  me: () => request<CurrentSubject>("/auth/me"),
  loginLocal: (username: string, password: string) =>
    request<void>("/auth/login/local", { method: "POST", body: JSON.stringify({ username, password }) }),
  loginDevelopment: () => request<void>("/auth/login/development", { method: "POST" }),
  logout: () => request<void>("/auth/logout", { method: "POST" }),
  auditEvents: (limit = 50) => request<AuditEventSummary[]>(`/audit/events?limit=${limit}`),
};
