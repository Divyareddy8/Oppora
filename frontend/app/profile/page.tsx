"use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";

type Opportunity = { id:number; title:string; organization:string; opportunity_type:string; role:string; description:string; source_url:string; deadline:string|null; location:string; skills:string[]; verified:boolean; };
type Application = { id:number; status:string; notes:string; applied_at:string|null; follow_up_date:string|null; opportunity:Opportunity; };
type Preferences = { email_enabled:boolean; deadline_alerts:boolean; daily_digest:boolean; telegram_enabled:boolean; telegram_chat_id:string; digest_hour:number; };
const statuses = ["saved", "applied", "interview", "offer", "rejected", "withdrawn"];

export default function Profile() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [preferences, setPreferences] = useState<Preferences | null>(null);
  const [tab, setTab] = useState<"tracker" | "alerts">("tracker");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function load() {
    try {
      const [tracker, settings] = await Promise.all([api("/applications"), api("/notifications/preferences")]);
      setApplications(tracker); setPreferences(settings);
    } catch (e:any) { setError(e.message); }
  }
  useEffect(() => { load(); }, []);

  async function updateApplication(item:Application, status:string) {
    try {
      const updated = await api(`/applications/${item.id}`, { method:"PATCH", body:JSON.stringify({ status, notes:item.notes, follow_up_date:item.follow_up_date }) });
      setApplications(items => items.map(current => current.id === item.id ? updated : current));
    } catch (e:any) { setError(e.message); }
  }

  async function updatePreferences(patch:Partial<Preferences>) {
    if (!preferences) return;
    const next = { ...preferences, ...patch };
    setPreferences(next);
    try { await api("/notifications/preferences", { method:"PUT", body:JSON.stringify(next) }); setNotice("Notification settings updated"); }
    catch (e:any) { setError(e.message); }
  }

  async function send(path:string) {
    try { const result = await api(path, { method:"POST" }); setNotice(result.sent ? `${result.sent} notification channel(s) processed` : result.reason); }
    catch (e:any) { setError(e.message); }
  }

  return (
    <main className="container">
      <nav style={{margin:"-32px -20px 30px"}}><a className="brand" href="/feed">Opportunity Radar</a><a href="/feed">Personal feed</a></nav>
      <div className="feed-header"><div><p className="eyebrow">YOUR WORKSPACE</p><h1>Applications & alerts</h1><p className="muted">Track progress, keep deadlines visible, and choose how Oppora reaches you.</p></div></div>
      <div className="segmented workspace-tabs"><button className={tab === "tracker" ? "active" : ""} onClick={()=>setTab("tracker")}>Application tracker</button><button className={tab === "alerts" ? "active" : ""} onClick={()=>setTab("alerts")}>Alerts & delivery</button></div>
      {error && <p className="error">{error}</p>}{notice && <p className="success">{notice}</p>}

      {tab === "tracker" && <section>
        <div className="results-bar"><strong>{applications.length} tracked opportunities</strong><a className="profile-link" href="/feed">Find more opportunities <span>→</span></a></div>
        {applications.length === 0 && <div className="empty-state"><h2>Your tracker is empty</h2><p className="muted">Save an opportunity from your feed, then add it here to track applications.</p><a href="/feed"><button>Explore feed</button></a></div>}
        <div className="grid">{applications.map(item => <article className="card opportunity-card" key={item.id}>
          <div className="opportunity-top"><span className="badge">{item.opportunity.opportunity_type}</span><span className="badge">{item.status}</span></div>
          <h2>{item.opportunity.title}</h2><p><strong>{item.opportunity.organization}</strong> · {item.opportunity.role}</p>
          <p className="muted">{item.opportunity.location} · Deadline: {item.opportunity.deadline || "Not specified"}</p>
          <p>{item.opportunity.description}</p>
          <label>Status<select value={item.status} onChange={e=>updateApplication(item, e.target.value)}>{statuses.map(status=><option key={status}>{status}</option>)}</select></label>
          <label>Follow-up date<input type="date" value={item.follow_up_date || ""} onChange={e=>api(`/applications/${item.id}`, { method:"PATCH", body:JSON.stringify({ status:item.status, notes:item.notes, follow_up_date:e.target.value || null }) }).then(load).catch((e:any)=>setError(e.message))} /></label>
          <div className="opportunity-actions"><a href={item.opportunity.source_url} target="_blank" rel="noreferrer"><button>View source</button></a><button className="secondary-button" onClick={()=>api(`/applications/${item.id}`, { method:"DELETE" }).then(load)}>Remove</button></div>
        </article>)}</div>
      </section>}

      {tab === "alerts" && preferences && <section className="settings-layout">
        <div className="card settings-card"><p className="eyebrow">DELIVERY</p><h2>Notification settings</h2>
          <label className="check-label"><input type="checkbox" checked={preferences.email_enabled} onChange={e=>updatePreferences({email_enabled:e.target.checked})} /> Email notifications</label>
          <label className="check-label"><input type="checkbox" checked={preferences.deadline_alerts} onChange={e=>updatePreferences({deadline_alerts:e.target.checked})} /> Deadline alerts</label>
          <label className="check-label"><input type="checkbox" checked={preferences.daily_digest} onChange={e=>updatePreferences({daily_digest:e.target.checked})} /> Daily digest</label>
          <label className="check-label"><input type="checkbox" checked={preferences.telegram_enabled} onChange={e=>updatePreferences({telegram_enabled:e.target.checked})} /> Telegram delivery</label>
          <label>Telegram chat ID<input value={preferences.telegram_chat_id} onChange={e=>setPreferences({...preferences, telegram_chat_id:e.target.value})} onBlur={()=>updatePreferences({telegram_chat_id:preferences.telegram_chat_id})} placeholder="Connect your bot chat ID" /></label>
          <label>Digest hour<input type="number" min="0" max="23" value={preferences.digest_hour} onChange={e=>updatePreferences({digest_hour:Number(e.target.value)})} /></label>
        </div>
        <div className="card settings-card"><p className="eyebrow">AUTOMATIONS</p><h2>Send a test digest</h2><p className="muted">Preview or send the alerts generated from your tracked opportunities. Without credentials, sends are recorded as previews.</p>
          <div className="opportunity-actions"><button onClick={()=>send("/notifications/deadline-alerts/send")}>Send deadline alerts</button><button className="secondary-button" onClick={()=>send("/notifications/digest/send")}>Send daily digest</button></div>
          <p className="muted settings-note">Email uses SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM. Telegram uses TELEGRAM_BOT_TOKEN.</p>
        </div>
      </section>}
    </main>
  );
}
