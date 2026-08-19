import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router";
import { api, ApiError, type InventoryEntity } from "../api/client";

const CONNECTOR_KEY = "sanfabric-sim";

function groupByType(entities: InventoryEntity[]): Map<string, InventoryEntity[]> {
  const groups = new Map<string, InventoryEntity[]>();
  for (const entity of entities) {
    const list = groups.get(entity.entity_type) ?? [];
    list.push(entity);
    groups.set(entity.entity_type, list);
  }
  return groups;
}

export function Inventory() {
  const [syncError, setSyncError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const entities = useQuery({ queryKey: ["inventory", "entities"], queryFn: api.inventoryEntities });
  const relationships = useQuery({
    queryKey: ["inventory", "relationships"],
    queryFn: api.inventoryRelationships,
  });

  const sync = useMutation({
    mutationFn: () => api.syncConnector(CONNECTOR_KEY),
    onSuccess: () => {
      setSyncError(null);
      queryClient.invalidateQueries({ queryKey: ["inventory"] });
    },
    onError: (err) => setSyncError(err instanceof ApiError ? err.message : "Sync failed."),
  });

  const groups = groupByType(entities.data ?? []);

  return (
    <main style={{ maxWidth: 900, margin: "5vh auto", fontFamily: "system-ui, sans-serif" }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Inventory</h1>
        <Link to="/">Back to workspace</Link>
      </header>

      <section>
        <button type="button" onClick={() => sync.mutate()} disabled={sync.isPending}>
          {sync.isPending ? "Syncing…" : `Sync ${CONNECTOR_KEY}`}
        </button>
        {syncError && <p style={{ color: "crimson" }}>{syncError}</p>}
        {sync.data && (
          <p>
            Discovered {sync.data.entities_written} entities and {sync.data.relationships_written}{" "}
            relationships.
          </p>
        )}
      </section>

      {entities.isLoading && <p>Loading…</p>}
      {entities.isError && (
        <p style={{ color: "crimson" }}>
          {entities.error instanceof ApiError ? entities.error.message : "Failed to load inventory."}
        </p>
      )}

      {["fabric", "switch", "port", "zone"].map((type) => {
        const items = groups.get(type) ?? [];
        if (items.length === 0) return null;
        return (
          <section key={type}>
            <h2 style={{ textTransform: "capitalize" }}>
              {type} ({items.length})
            </h2>
            <table style={{ borderCollapse: "collapse", width: "100%" }}>
              <thead>
                <tr>
                  <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Name</th>
                  <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>External ID</th>
                  <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Attributes</th>
                </tr>
              </thead>
              <tbody>
                {items.map((entity) => (
                  <tr key={entity.id}>
                    <td>{entity.display_name}</td>
                    <td>
                      <code>{entity.external_id}</code>
                    </td>
                    <td>{JSON.stringify(entity.attributes)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        );
      })}

      {relationships.data && relationships.data.length > 0 && (
        <section>
          <h2>Relationships ({relationships.data.length})</h2>
          <p>{relationships.data.filter((r) => r.relationship_type === "managed_by").length} managed_by · {" "}
            {relationships.data.filter((r) => r.relationship_type === "member_of").length} member_of</p>
        </section>
      )}

      <ConnectorHealth />
      <KnowledgeSearch />
    </main>
  );
}

function ConnectorHealth() {
  const checks = useQuery({
    queryKey: ["connector-health", CONNECTOR_KEY],
    queryFn: () => api.connectorHealthChecks(CONNECTOR_KEY),
  });

  return (
    <section>
      <h2>Connector health</h2>
      {checks.isLoading && <p>Loading…</p>}
      {checks.data && checks.data.length === 0 && <p>No health checks recorded yet.</p>}
      {checks.data && checks.data.length > 0 && (
        <ul>
          {checks.data.slice(0, 5).map((check) => (
            <li key={check.id}>
              {new Date(check.checked_at).toLocaleString()} — {check.status} ({check.latency_ms}ms)
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function KnowledgeSearch() {
  const [query, setQuery] = useState("");
  const search = useMutation({ mutationFn: (q: string) => api.knowledgeSearch(q) });

  return (
    <section>
      <h2>Knowledge search</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (query.trim()) search.mutate(query);
        }}
      >
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search knowledge…" />
        <button type="submit" disabled={search.isPending}>
          Search
        </button>
      </form>
      {search.isError && (
        <p style={{ color: "crimson" }}>
          {search.error instanceof ApiError ? search.error.message : "Search failed."}
        </p>
      )}
      {search.data && (
        <ul>
          {search.data.map((result) => (
            <li key={result.chunk_id}>
              <strong>{result.source_title}</strong> (score {result.score.toFixed(2)}): {result.content}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
