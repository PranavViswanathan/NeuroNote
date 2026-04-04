"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

interface LoginFormProps {
  next: string;
}

export function LoginForm({ next }: LoginFormProps) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      if (res.ok) {
        router.push(next);
      } else {
        setError("Incorrect password. Try again.");
        setPassword("");
      }
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--workspace-bg)",
      }}
    >
      <div
        style={{
          background: "var(--panel-bg)",
          border: "1px solid var(--panel-border)",
          borderRadius: "12px",
          padding: "2.5rem 2rem",
          width: "100%",
          maxWidth: "360px",
          boxShadow: "var(--shadow-panel)",
        }}
      >
        <h1
          style={{
            margin: "0 0 0.25rem",
            fontSize: "1.25rem",
            fontWeight: 700,
            color: "var(--text-strong)",
            letterSpacing: "-0.01em",
          }}
        >
          NeuroNote
        </h1>
        <p
          style={{
            margin: "0 0 1.75rem",
            fontSize: "var(--text-sm)",
            color: "var(--text-muted)",
          }}
        >
          Enter your password to continue
        </p>
        <form onSubmit={handleSubmit}>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            // eslint-disable-next-line jsx-a11y/no-autofocus
            autoFocus
            required
            style={{
              width: "100%",
              boxSizing: "border-box",
              padding: "0.6rem 0.75rem",
              fontSize: "var(--text-base)",
              border: "1px solid var(--input-border)",
              borderRadius: "6px",
              outline: "none",
              color: "var(--text-strong)",
              background: "var(--panel-bg)",
              marginBottom: error ? "0.5rem" : "0.75rem",
            }}
          />
          {error && (
            <p
              style={{
                margin: "0 0 0.75rem",
                fontSize: "var(--text-sm)",
                color: "var(--danger)",
              }}
            >
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={loading || !password}
            style={{
              width: "100%",
              padding: "0.6rem",
              fontSize: "var(--text-base)",
              fontWeight: 600,
              color: "#fff",
              background: "var(--accent)",
              border: "none",
              borderRadius: "6px",
              cursor: loading || !password ? "default" : "pointer",
              opacity: loading || !password ? 0.65 : 1,
              transition: "opacity 0.15s",
            }}
          >
            {loading ? "Unlocking…" : "Unlock"}
          </button>
        </form>
      </div>
    </div>
  );
}
