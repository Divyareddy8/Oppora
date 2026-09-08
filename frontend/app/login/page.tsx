 "use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../../lib/api";

export default function Login() {
  const [email, setEmail] = useState("demo@student.com");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (submitting) return;
    setError("");
    setSubmitting(true);
    try {
      const data = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem("token", data.access_token);
      router.push("/feed");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <a className="auth-brand" href="/">Oppora</a>
        <div className="auth-heading"><p className="eyebrow">WELCOME BACK</p><h1>Find your next opportunity.</h1><p className="muted">Sign in to continue to your personalized feed.</p></div>
        <form onSubmit={submit}>
          <label htmlFor="email">Email<input id="email" type="email" autoComplete="email" required value={email} onChange={e=>setEmail(e.target.value)} /></label>
          <label htmlFor="password">Password<input id="password" type="password" autoComplete="current-password" required value={password} onChange={e=>setPassword(e.target.value)} /></label>
          {error && <p className="error">{error}</p>}
          <button className="auth-submit" type="submit" disabled={submitting}>{submitting ? "Signing in..." : "Login"}</button>
        </form>
        <p className="auth-demo muted">Demo: demo@student.com / password123</p>
        <p className="auth-switch muted">New to Oppora? <a href="/register">Create an account</a></p>
      </section>
    </main>
  );
}
