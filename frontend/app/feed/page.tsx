 "use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";

type Opportunity = {
  id:number; title:string; organization:string; opportunity_type:string;
  role:string; description:string; source_url:string; source_name:string;
  deadline:string|null; location:string; company_tier:string; verified:boolean;
  inferred_company_tier:string; women_focused:boolean; skills:string[];
  experience_min:number; experience_max:number;
  match_score:number|null; semantic_score:number|null; reasons:string[];
};

type Filters = {
  search:string; type:string; tier:string; audience:string; role:string;
  experience:string; skill:string; location:string; verifiedOnly:boolean;
};

export default function Feed() {
  const [items, setItems] = useState<Opportunity[]>([]);
  const [profile, setProfile] = useState<any>(null);
  const [search, setSearch] = useState("");
  const [type, setType] = useState("");
  const [tier, setTier] = useState("");
  const [audience, setAudience] = useState("all");
  const [role, setRole] = useState("");
  const [experience, setExperience] = useState("");
  const [skill, setSkill] = useState("");
  const [location, setLocation] = useState("");
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [appliedFilters, setAppliedFilters] = useState<Filters>({
    search:"", type:"", tier:"", audience:"all", role:"", experience:"",
    skill:"", location:"", verifiedOnly:false,
  });
  const [error, setError] = useState("");

  async function loadFeed() {
    try { setItems(await api("/opportunities/feed")); }
    catch (e:any) { setError(e.message); }
  }

  useEffect(() => {
    loadFeed();
    api("/profile").then(data => {
      setProfile(data);
    }).catch(() => {});
  }, []);

  function matchesExperience(op: Opportunity) {
    if (!appliedFilters.experience) return true;
    if (appliedFilters.experience === "0") return op.experience_min === 0 && op.experience_max <= 1;
    if (appliedFilters.experience === "1-3") return op.experience_max >= 1 && op.experience_min <= 3;
    if (appliedFilters.experience === "3-5") return op.experience_max >= 3 && op.experience_min <= 5;
    return op.experience_max >= 5;
  }

  const filteredItems = items.filter(op => {
    const haystack = `${op.title} ${op.organization} ${op.description} ${op.role}`.toLowerCase();
    const roleText = op.role.toLowerCase();
    const opportunitySkills = op.skills.map(item => item.toLowerCase());
    const audienceMatches = appliedFilters.audience === "all"
      || (appliedFilters.audience === "student" && op.experience_max <= 1)
      || (appliedFilters.audience === "professional" && op.experience_max > 1);
    const roleMatches = !appliedFilters.role || (appliedFilters.role === "Other"
      ? !/(sde|software|developer|machine learning|mle|data scientist)/i.test(roleText)
      : new RegExp(appliedFilters.role === "SDE" ? "sde|software|developer" : "mle|machine learning", "i").test(roleText));
    const skillMatches = !appliedFilters.skill || opportunitySkills.some(item => item.includes(appliedFilters.skill.toLowerCase()));
    const locationMatches = !appliedFilters.location || op.location.toLowerCase().includes(appliedFilters.location.toLowerCase());
    return (!appliedFilters.search || haystack.includes(appliedFilters.search.toLowerCase()))
      && (!appliedFilters.type || op.opportunity_type === appliedFilters.type)
      && (!appliedFilters.tier || (op.inferred_company_tier || op.company_tier) === appliedFilters.tier)
      && audienceMatches && roleMatches && matchesExperience(op) && skillMatches
      && locationMatches && (!appliedFilters.verifiedOnly || op.verified);
  });

  function applyFilters() {
    setAppliedFilters({ search, type, tier, audience, role, experience, skill, location, verifiedOnly });
  }

  function clearFilters() {
    setSearch(""); setType(""); setTier(""); setRole(""); setExperience("");
    setSkill(""); setLocation(""); setVerifiedOnly(false); setAudience("all");
    setAppliedFilters({ search:"", type:"", tier:"", audience:"all", role:"", experience:"", skill:"", location:"", verifiedOnly:false });
  }

  async function save(id:number) {
    await api(`/opportunities/${id}/save`, {method:"POST"});
    alert("Saved");
  }

  async function recordView(id:number) {
    try { await api(`/opportunities/${id}/interact`, {method:"POST", body:JSON.stringify({event_type:"view"})}); }
    catch (_) {}
  }

  return (
    <main className="container">
      <nav style={{margin:"-32px -20px 30px"}}>
        <div className="brand">Opportunity Radar</div>
        <a href="/profile">Profile</a>
      </nav>

      <div className="feed-header">
        <div>
          <p className="eyebrow">PERSONAL FEED</p>
          <h1>Your opportunity feed</h1>
          <p className="muted">One ranked feed for the roles and opportunities that fit your profile.</p>
        </div>
        <a className="profile-link" href="/profile">{profile?.name || "Your profile"} <span>→</span></a>
      </div>

      <div className="feed-layout">
        <aside className="filter-rail">
          <div className="filter-heading"><div><p className="eyebrow">REFINE</p><h3>Filters</h3></div><button className="text-button" onClick={clearFilters}>Clear</button></div>
          <label>Search<input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Role, company, skill" /></label>
          <fieldset>
            <legend>Who are you?</legend>
            <div className="segmented">
              {[['all','Everyone'], ['student','Student'], ['professional','Working pro']].map(([value, label]) => <button type="button" className={audience === value ? "active" : ""} key={value} onClick={()=>setAudience(value)}>{label}</button>)}
            </div>
          </fieldset>
          <label>Role
            <select value={role} onChange={e=>setRole(e.target.value)}><option value="">All roles</option><option>SDE</option><option>MLE</option><option>Other</option></select>
          </label>
          <label>Experience
            <select value={experience} onChange={e=>setExperience(e.target.value)}><option value="">Any experience</option><option value="0">Student / 0-1 year</option><option value="1-3">1-3 years</option><option value="3-5">3-5 years</option><option value="5+">5+ years</option></select>
          </label>
          <label>Skill<input value={skill} onChange={e=>setSkill(e.target.value)} placeholder="e.g. Python" /></label>
          <label>Location<input value={location} onChange={e=>setLocation(e.target.value)} placeholder="Remote, Bangalore" /></label>
          <label>Opportunity type
            <select value={type} onChange={e=>setType(e.target.value)}><option value="">All types</option><option>Internship</option><option>Research</option><option>Hackathon</option><option>Scholarship</option><option>Open Source</option></select>
          </label>
          <label>Company tier
            <select value={tier} onChange={e=>setTier(e.target.value)}><option value="">All tiers</option><option>S</option><option>A</option><option>B</option><option>C</option></select>
          </label>
          <label className="check-label"><input type="checkbox" checked={verifiedOnly} onChange={e=>setVerifiedOnly(e.target.checked)} /> Verified sources only</label>
          <button className="apply-button" onClick={applyFilters}>Apply filters</button>
        </aside>

        <section className="feed-results">
          <div className="results-bar"><strong>{filteredItems.length} opportunities</strong><span className="muted">Ranked for you · {appliedFilters.audience === "professional" ? "Working professional" : appliedFilters.audience === "student" ? "Student" : "All profiles"}</span></div>
          {filteredItems.length === 0 && <div className="empty-state"><h2>No matches yet</h2><p className="muted">Try widening your filters or clearing the search.</p></div>}
          <div className="grid">
            {filteredItems.map(op => (
              <article className="card opportunity-card" key={op.id}>
                <div className="opportunity-top"><span className="badge">{op.opportunity_type}</span><span className="score">{op.match_score != null ? `${op.match_score}% match` : ""}</span></div>
                <h2>{op.title}</h2>
                <p><strong>{op.organization}</strong> · {op.role}</p>
                <p className="muted">{op.location} · {op.experience_min === op.experience_max ? `${op.experience_min} yrs` : `${op.experience_min}-${op.experience_max} yrs`} · Tier {op.inferred_company_tier || op.company_tier}</p>
                <div>{op.verified && <span className="badge">✓ Verified</span>}{op.women_focused && <span className="badge">Women-focused</span>}</div>
                <p>{op.description}</p>
                <div>{op.skills.map(s=><span className="badge" key={s}>{s}</span>)}</div>
                <p><strong>Deadline:</strong> {op.deadline || "Not specified"}</p>

                {op.reasons?.length > 0 && <div className="match-panel"><strong>Why this matches you:</strong><ul>{op.reasons.map(r=><li key={r}>{r}</li>)}</ul></div>}

                <div className="opportunity-actions"><button onClick={()=>save(op.id)}>Save</button><a href={op.source_url} target="_blank" rel="noreferrer" onClick={()=>recordView(op.id)}><button className="secondary-button">View source</button></a></div>
              </article>
            ))}
          </div>
        </section>
      </div>
      {error && <p className="error">{error}</p>}
    </main>
  );
}
