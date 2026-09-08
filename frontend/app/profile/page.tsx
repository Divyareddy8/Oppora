"use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";

type Bookmark = {
  id:number; title:string; organization:string; opportunity_type:string;
  role:string; description:string; source_url:string; deadline:string|null;
  location:string; skills:string[]; verified:boolean;
};

export default function Profile() {
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [error, setError] = useState("");

  async function loadBookmarks() {
    try { setBookmarks(await api("/profile/bookmarks")); }
    catch (e:any) { setError(e.message); }
  }

  useEffect(() => { loadBookmarks(); }, []);

  async function removeBookmark(id:number) {
    await api(`/profile/bookmarks/${id}`, { method:"DELETE" });
    setBookmarks(items => items.filter(item => item.id !== id));
  }

  return (
    <main className="container">
      <nav style={{margin:"-32px -20px 30px"}}>
        <a className="brand" href="/feed">Opportunity Radar</a>
        <a href="/feed">Personal feed</a>
      </nav>

      <div className="feed-header">
        <div><p className="eyebrow">YOUR LIBRARY</p><h1>Bookmarked opportunities</h1><p className="muted">Keep the opportunities you want to come back to in one place.</p></div>
      </div>

      {error && <p className="error">{error}</p>}
      {bookmarks.length === 0 && !error && <div className="empty-state"><h2>No bookmarks yet</h2><p className="muted">Save an opportunity from your personal feed and it will appear here.</p><a href="/feed"><button>Explore feed</button></a></div>}
      <div className="grid">
        {bookmarks.map(op => <article className="card opportunity-card" key={op.id}>
          <div className="opportunity-top"><span className="badge">{op.opportunity_type}</span>{op.verified && <span className="badge">✓ Verified</span>}</div>
          <h2>{op.title}</h2>
          <p><strong>{op.organization}</strong> · {op.role}</p>
          <p className="muted">{op.location} · Deadline: {op.deadline || "Not specified"}</p>
          <p>{op.description}</p>
          <div>{op.skills.map(skill => <span className="badge" key={skill}>{skill}</span>)}</div>
          <div className="opportunity-actions"><a href={op.source_url} target="_blank" rel="noreferrer"><button>View source</button></a><button className="secondary-button" onClick={()=>removeBookmark(op.id)}>Remove bookmark</button></div>
        </article>)}
      </div>
    </main>
  );
}
