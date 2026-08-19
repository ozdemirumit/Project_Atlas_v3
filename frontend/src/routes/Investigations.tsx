import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router";
import { api, ApiError, type InventoryEntity } from "../api/client";

export function Investigations() {
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const investigations = useQuery({ queryKey: ["investigations"], queryFn: api.listInvestigations });

  return (
    <main style={{ maxWidth: 900, margin: "5vh auto", fontFamily: "system-ui, sans-serif" }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Investigations</h1>
        <Link to="/">Back to workspace</Link>
      </header>

      <NewInvestigationForm onCreated={setSelectedKey} />

      <section>
        <h2>Open investigations</h2>
        <ul>
          {(investigations.data ?? []).map((inv) => (
            <li key={inv.id}>
              <button type="button" onClick={() => setSelectedKey(inv.key)}>
                {inv.key}
              </button>{" "}
              — {inv.title} ({inv.status})
            </li>
          ))}
        </ul>
      </section>

      {selectedKey && <InvestigationDetail investigationKey={selectedKey} />}
    </main>
  );
}

function NewInvestigationForm({ onCreated }: { onCreated: (key: string) => void }) {
  const [key, setKey] = useState("");
  const [title, setTitle] = useState("");
  const queryClient = useQueryClient();
  const create = useMutation({
    mutationFn: () => api.createInvestigation(key, title),
    onSuccess: (inv) => {
      queryClient.invalidateQueries({ queryKey: ["investigations"] });
      onCreated(inv.key);
      setKey("");
      setTitle("");
    },
  });

  return (
    <section>
      <h2>Open a new investigation</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (key.trim() && title.trim()) create.mutate();
        }}
      >
        <input value={key} onChange={(e) => setKey(e.target.value)} placeholder="key (e.g. inv-2026-08-19-01)" />
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="title" />
        <button type="submit" disabled={create.isPending}>
          Create
        </button>
      </form>
      {create.isError && (
        <p style={{ color: "crimson" }}>
          {create.error instanceof ApiError ? create.error.message : "Failed to create."}
        </p>
      )}
    </section>
  );
}

function InvestigationDetail({ investigationKey }: { investigationKey: string }) {
  const queryClient = useQueryClient();
  const report = useQuery({
    queryKey: ["investigation-report", investigationKey],
    queryFn: () => api.getInvestigationReport(investigationKey),
  });
  const entities = useQuery({ queryKey: ["inventory", "entities"], queryFn: api.inventoryEntities });
  const [targetEntityId, setTargetEntityId] = useState("");

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ["investigation-report", investigationKey] });

  const generateHypotheses = useMutation({
    mutationFn: (entityId: string) => api.generateHypotheses(investigationKey, entityId),
    onSuccess: invalidate,
  });
  const confirmHypothesis = useMutation({
    mutationFn: (hypothesisId: string) =>
      api.updateHypothesisStatus(investigationKey, hypothesisId, "confirmed"),
    onSuccess: invalidate,
  });
  const assessImpact = useMutation({
    mutationFn: (entityId: string) => api.assessImpact(investigationKey, entityId),
    onSuccess: invalidate,
  });
  const draftRecommendation = useMutation({
    mutationFn: (hypothesisId: string) => api.draftRecommendation(investigationKey, hypothesisId),
    onSuccess: invalidate,
  });
  const submitRecommendation = useMutation({
    mutationFn: (recommendationId: string) => api.submitRecommendation(investigationKey, recommendationId),
    onSuccess: invalidate,
  });
  const decideRecommendation = useMutation({
    mutationFn: ({ id, decision }: { id: string; decision: "approved" | "rejected" }) =>
      api.decideRecommendation(investigationKey, id, decision, ""),
    onSuccess: invalidate,
    onError: (err) =>
      window.alert(err instanceof ApiError ? err.message : "Approval decision failed."),
  });

  const options: InventoryEntity[] = entities.data ?? [];

  return (
    <section style={{ borderTop: "2px solid #333", marginTop: 24, paddingTop: 16 }}>
      <h2>Investigation: {investigationKey}</h2>

      <div>
        <select value={targetEntityId} onChange={(e) => setTargetEntityId(e.target.value)}>
          <option value="">Select a target entity…</option>
          {options.map((entity) => (
            <option key={entity.id} value={entity.id}>
              {entity.entity_type}: {entity.display_name} ({entity.external_id})
            </option>
          ))}
        </select>{" "}
        <button
          type="button"
          disabled={!targetEntityId || generateHypotheses.isPending}
          onClick={() => generateHypotheses.mutate(targetEntityId)}
        >
          Generate RCA hypotheses
        </button>{" "}
        <button
          type="button"
          disabled={!targetEntityId || assessImpact.isPending}
          onClick={() => assessImpact.mutate(targetEntityId)}
        >
          Assess change impact
        </button>
      </div>

      {report.data && (
        <>
          <h3>Hypotheses</h3>
          <ul>
            {report.data.hypotheses.map((h) => (
              <li key={h.id}>
                <strong>[{h.fault_family}]</strong> {h.description} — confidence: {h.confidence}, status:{" "}
                {h.status} ({h.generated_by})
                {h.status === "proposed" && (
                  <>
                    {" "}
                    <button type="button" onClick={() => confirmHypothesis.mutate(h.id)}>
                      Confirm
                    </button>{" "}
                    <button type="button" onClick={() => draftRecommendation.mutate(h.id)}>
                      Draft recommendation
                    </button>
                  </>
                )}
              </li>
            ))}
          </ul>

          <h3>Impact assessments</h3>
          <ul>
            {report.data.impact_assessments.map((i) => (
              <li key={i.id}>{i.summary}</li>
            ))}
          </ul>

          <h3>Recommendations</h3>
          <ul>
            {report.data.recommendations.map((r) => (
              <li key={r.id}>
                <strong>{r.title}</strong> (risk: {r.risk_level}, ~{r.estimated_duration_minutes}min,
                status: {r.status}) — {r.summary}
                <br />
                Rollback: {r.rollback_plan}
                <br />
                {r.status === "proposed" && (
                  <button type="button" onClick={() => submitRecommendation.mutate(r.id)}>
                    Submit for approval
                  </button>
                )}
                {r.status === "pending_approval" && (
                  <>
                    <button
                      type="button"
                      onClick={() => decideRecommendation.mutate({ id: r.id, decision: "approved" })}
                    >
                      Approve
                    </button>{" "}
                    <button
                      type="button"
                      onClick={() => decideRecommendation.mutate({ id: r.id, decision: "rejected" })}
                    >
                      Reject
                    </button>
                  </>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
