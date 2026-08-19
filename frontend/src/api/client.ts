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

export interface InventoryEntity {
  id: string;
  connector_instance_id: string;
  entity_type: "fabric" | "switch" | "port" | "zone";
  external_id: string;
  display_name: string;
  attributes: Record<string, unknown>;
  last_observed_at: string;
}

export interface InventoryRelationship {
  id: string;
  from_entity_id: string;
  to_entity_id: string;
  relationship_type: "managed_by" | "member_of";
}

export interface SyncResult {
  connector_instance_key: string;
  entities_written: number;
  relationships_written: number;
}

export interface ConnectorHealthCheck {
  id: string;
  checked_at: string;
  status: "healthy" | "unhealthy";
  latency_ms: number;
  detail: Record<string, unknown>;
}

export interface KnowledgeSearchResult {
  chunk_id: string;
  source_key: string;
  source_title: string;
  content: string;
  score: number;
}

export interface Investigation {
  id: string;
  key: string;
  title: string;
  status: string;
  created_by: string;
  created_at: string;
}

export interface RcaHypothesis {
  id: string;
  fault_family: string;
  description: string;
  confidence: string;
  supporting_evidence: string[];
  contradicting_evidence: string[];
  status: string;
  generated_by: string;
}

export interface ChangeImpactAssessment {
  id: string;
  target_entity_id: string;
  affected_entity_ids: string[];
  graph_gaps: string[];
  summary: string;
}

export interface Recommendation {
  id: string;
  title: string;
  summary: string;
  risk_level: string;
  estimated_duration_minutes: number;
  preconditions: string[];
  rollback_plan: string;
  status: string;
  generated_by: string;
}

export interface InvestigationReport {
  investigation: Investigation;
  events: unknown[];
  hypotheses: RcaHypothesis[];
  impact_assessments: ChangeImpactAssessment[];
  recommendations: Recommendation[];
}

export const api = {
  health: () => request<HealthStatus>("/health"),
  me: () => request<CurrentSubject>("/auth/me"),
  loginLocal: (username: string, password: string) =>
    request<void>("/auth/login/local", { method: "POST", body: JSON.stringify({ username, password }) }),
  loginDevelopment: () => request<void>("/auth/login/development", { method: "POST" }),
  logout: () => request<void>("/auth/logout", { method: "POST" }),
  auditEvents: (limit = 50) => request<AuditEventSummary[]>(`/audit/events?limit=${limit}`),
  inventoryEntities: () => request<InventoryEntity[]>("/inventory/entities"),
  inventoryRelationships: () => request<InventoryRelationship[]>("/inventory/relationships"),
  syncConnector: (key: string) => request<SyncResult>(`/connectors/${key}/sync`, { method: "POST" }),
  connectorHealthChecks: (key: string) =>
    request<ConnectorHealthCheck[]>(`/connectors/${key}/health-checks`),
  knowledgeSearch: (q: string) =>
    request<KnowledgeSearchResult[]>(`/knowledge/search?q=${encodeURIComponent(q)}`),
  listInvestigations: () => request<Investigation[]>("/investigations"),
  createInvestigation: (key: string, title: string) =>
    request<Investigation>("/investigations", { method: "POST", body: JSON.stringify({ key, title }) }),
  getInvestigationReport: (key: string) => request<InvestigationReport>(`/investigations/${key}/report`),
  generateHypotheses: (key: string, targetEntityId: string) =>
    request<RcaHypothesis[]>(`/investigations/${key}/hypotheses/generate`, {
      method: "POST",
      body: JSON.stringify({ target_entity_id: targetEntityId }),
    }),
  updateHypothesisStatus: (key: string, hypothesisId: string, status: string) =>
    request<RcaHypothesis>(`/investigations/${key}/hypotheses/${hypothesisId}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  assessImpact: (key: string, targetEntityId: string) =>
    request<ChangeImpactAssessment>(`/investigations/${key}/impact`, {
      method: "POST",
      body: JSON.stringify({ target_entity_id: targetEntityId }),
    }),
  draftRecommendation: (key: string, hypothesisId: string) =>
    request<Recommendation>(`/investigations/${key}/recommendations`, {
      method: "POST",
      body: JSON.stringify({ hypothesis_id: hypothesisId }),
    }),
  submitRecommendation: (key: string, recommendationId: string) =>
    request<Recommendation>(`/investigations/${key}/recommendations/${recommendationId}/submit`, {
      method: "POST",
    }),
  decideRecommendation: (key: string, recommendationId: string, decision: "approved" | "rejected", comment: string) =>
    request<Recommendation>(`/investigations/${key}/recommendations/${recommendationId}/decide`, {
      method: "POST",
      body: JSON.stringify({ decision, comment }),
    }),
};
