import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { api, ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { refresh } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.loginLocal(username, password);
      await refresh();
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to sign in.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDevelopmentLogin = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await api.loginDevelopment();
      await refresh();
      navigate("/", { replace: true });
    } catch {
      setError("Development identity is not available on this server.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main style={{ maxWidth: 360, margin: "10vh auto", fontFamily: "system-ui, sans-serif" }}>
      <h1>Project Atlas</h1>
      <form onSubmit={handleSubmit}>
        <label style={{ display: "block", marginBottom: 8 }}>
          Username
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
            style={{ display: "block", width: "100%" }}
          />
        </label>
        <label style={{ display: "block", marginBottom: 8 }}>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
            style={{ display: "block", width: "100%" }}
          />
        </label>
        {error && <p style={{ color: "crimson" }}>{error}</p>}
        <button type="submit" disabled={submitting}>
          Sign in
        </button>
      </form>
      <hr style={{ margin: "16px 0" }} />
      <button type="button" onClick={handleDevelopmentLogin} disabled={submitting}>
        Continue as Local Operator (development only)
      </button>
    </main>
  );
}
