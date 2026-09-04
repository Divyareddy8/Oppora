 "use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../../lib/api";

export default function Login() {
  const [email, setEmail] = useState("demo@student.com");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState("");
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const data = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem("token", data.access_token);
      router.push("/feed");
    } catch (e: any) {
      setError(e.message);
    }
  }

  return (
    <main className="container">
      <div className="card" style={{maxWidth:450, margin:"40px auto"}}>
        <h1>Login</h1>
        <form onSubmit={submit}>
          <label>Email<input value={email} onChange={e=>setEmail(e.target.value)} /></label>
          <label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} /></label>
          {error && <p className="error">{error}</p>}
          <button>Login</button>
        </form>
        <p className="muted">Demo: demo@student.com / password123</p>
      </div>
    </main>
  );
}
