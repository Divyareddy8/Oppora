 "use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";

type Opportunity = {
  id:number; title:string; organization:string; opportunity_type:string;
  role:string; description:string; source_url:string; source_name:string;
  deadline:string|null; location:string; company_tier:string; verified:boolean;
  women_focused:boolean; skills:string[]; match_score:number|null; reasons:string[];
};

export default function Feed() {
  const [items, setItems] = useState<Opportunity[]>([]);
  const [search, setSearch] = useState("");
  const [type, setType] = useState("");
  const [tier, setTier] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (type) params.set("opportunity_type", type);
      if (tier) params.set("tier", tier);
      const data = await api(`/opportunities${params.toString() ? "?" + params : ""}`);
      setItems(data);
    } catch (e:any) { setError(e.message); }
  }

  async function loadFeed() {
    try { setItems(await api("/opportunities/feed")); }
    catch (e:any) { setError(e.message); }
  }

  useEffect(() => { loadFeed(); }, []);

  async function save(id:number) {
    await api(`/opportunities/${id}/save`, {method:"POST"});
    alert("Saved");
  }

  return (
    <main className="container">
      <nav style={{margin:"-32px -20px 30px"}}>
        <div className="brand">Opportunity Radar</div>
        <a href="/profile">Profile</a>
      </nav>

      <h1>Your opportunity feed</h1>
      <p className="muted">Rule-based Phase 1 personalization. ML comes in Phase 2.</p>

      <div className="card">
        <h3>Search / filter</h3>
        <div className="row">
          <label>Search<input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Python, Google, SDE..." /></label>
          <label>Type
            <select value={type} onChange={e=>setType(e.target.value)}>
              <option value="">All</option><option>Internship</option><option>Research</option>
              <option>Hackathon</option><option>Scholarship</option><option>Open Source</option>
            </select>
          </label>
          <label>Tier
            <select value={tier} onChange={e=>setTier(e.target.value)}>
              <option value="">All</option><option>S</option><option>A</option><option>B</option><option>C</option>
            </select>
          </label>
        </div>
        <div style={{display:"flex", gap:10}}>
          <button onClick={load}>Apply filters</button>
          <button onClick={loadFeed}>Personalized feed</button>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="grid" style={{marginTop:20}}>
        {items.map(op => (
          <article className="card" key={op.id}>
            <div style={{display:"flex", justifyContent:"space-between"}}>
              <span className="badge">{op.opportunity_type}</span>
              <span className="score">{op.match_score != null ? `${op.match_score}%` : ""}</span>
            </div>
            <h2>{op.title}</h2>
            <p><strong>{op.organization}</strong> · {op.role}</p>
            <p className="muted">{op.location} · Tier {op.company_tier}</p>
            {op.verified && <span className="badge">✓ Verified source</span>}
            {op.women_focused && <span className="badge">Women-focused</span>}
            <p>{op.description}</p>
            <div>{op.skills.map(s=><span className="badge" key={s}>{s}</span>)}</div>
            <p><strong>Deadline:</strong> {op.deadline || "Not specified"}</p>

            {op.reasons?.length > 0 && (
              <div>
                <strong>Why this matches:</strong>
                <ul>{op.reasons.map(r=><li key={r}>{r}</li>)}</ul>
              </div>
            )}

            <div style={{display:"flex", gap:10}}>
              <button onClick={()=>save(op.id)}>Save</button>
              <a href={op.source_url} target="_blank"><button>View source</button></a>
            </div>
          </article>
        ))}
      </div>
    </main>
  );
}
