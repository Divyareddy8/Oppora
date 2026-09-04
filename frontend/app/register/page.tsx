 "use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../../lib/api";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const data = await api("/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem("token", data.access_token);
      router.push("/profile");
    } catch (e: any) {
      setError(e.message);
    }
  }

  return (
    <main className="container">
      <div className="card" style={{maxWidth:450, margin:"40px auto"}}>
        <h1>Create account</h1>
        <form onSubmit={submit}>
          <label>Email<input value={email} onChange={e=>setEmail(e.target.value)} /></label>
          <label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} /></label>
          {error && <p className="error">{error}</p>}
          <button>Create account</button>
        </form>
      </div>
    </main>
  );
}
