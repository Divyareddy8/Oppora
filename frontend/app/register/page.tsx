 "use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../../lib/api";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (submitting) return;
    setError("");
    if (!email.trim().toLowerCase().endsWith("@gmail.com")) {
      setError("Please register with a Gmail address");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    setSubmitting(true);
    try {
      const data = await api("/auth/register", {
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
        <div className="auth-heading"><p className="eyebrow">GET STARTED</p><h1>Create your account.</h1><p className="muted">Start with your Gmail and password. Complete your profile after signing in.</p></div>
        <form onSubmit={submit}>
          <label htmlFor="email">Gmail address<input id="email" type="email" autoComplete="email" required value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@gmail.com" /></label>
          <label htmlFor="password">Password<input id="password" type="password" autoComplete="new-password" required minLength={8} value={password} onChange={e=>setPassword(e.target.value)} placeholder="At least 8 characters" /></label>
          {error && <p className="error">{error}</p>}
          <button className="auth-submit" type="submit" disabled={submitting}>{submitting ? "Creating account..." : "Create account and browse"}</button>
        </form>
        <p className="auth-switch muted">Already have an account? <a href="/login">Sign in</a></p>
      </section>
    </main>
  );
}
