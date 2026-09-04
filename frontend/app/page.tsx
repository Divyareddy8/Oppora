import Link from "next/link";

export default function Home() {
  return (
    <main className="container">
      <h1>Opportunity Radar</h1>
      <p>Relevant opportunities, not random listings.</p>
      <p className="muted">
        Phase 1: profile → opportunities → filters → personalized feed.
      </p>
      <div style={{display:"flex", gap:10}}>
        <Link href="/login"><button>Login</button></Link>
        <Link href="/register"><button>Register</button></Link>
      </div>
    </main>
  );
}
