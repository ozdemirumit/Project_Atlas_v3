import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export function Workspace() {
  const { subject, refresh } = useAuth();
  const navigate = useNavigate();
  const health = useQuery({ queryKey: ["health"], queryFn: api.health, refetchInterval: 15_000 });

  const handleLogout = async () => {
    await api.logout();
    await refresh();
    navigate("/login", { replace: true });
  };

  return (
    <main style={{ maxWidth: 720, margin: "5vh auto", fontFamily: "system-ui, sans-serif" }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Project Atlas</h1>
        <button type="button" onClick={handleLogout}>
          Sign out
        </button>
      </header>

      <section>
        <h2>Signed in as</h2>
        <p>
          <strong>{subject?.display_name}</strong> ({subject?.identity_source})
        </p>
        <p>Permissions: {subject?.permissions.join(", ") || "none"}</p>
      </section>

      <section>
        <h2>Platform health</h2>
        {health.isLoading && <p>Checking…</p>}
        {health.data && (
          <p>
            API: {health.data.status} · Database: {health.data.database}
          </p>
        )}
        {health.isError && <p style={{ color: "crimson" }}>Health check failed.</p>}
      </section>

      <section>
        <h2>Data and integration</h2>
        <p>
          <Link to="/inventory">View discovered inventory →</Link>
        </p>
      </section>
    </main>
  );
}
