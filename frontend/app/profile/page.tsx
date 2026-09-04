 "use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { useRouter } from "next/navigation";

export default function Profile() {
  const router = useRouter();
  const [form, setForm] = useState<any>({
    user_type:"student", name:"", college:"", degree:"", graduation_year:2028,
    branch:"", years_experience:0, current_role:"",
    target_roles:["SDE","MLE"], preferred_locations:["India","Bangalore","Remote"],
    preferred_types:["Internship","Research"], preferred_tiers:["S","A"],
    women_focused:false, skills:["Python","C++","Machine Learning"]
  });
  const [message, setMessage] = useState("");

  useEffect(() => {
    api("/profile").then(data => setForm(data)).catch(() => {});
  }, []);

  function set(key:string, value:any) {
    setForm((x:any)=>({...x,[key]:value}));
  }

  async function save(e:React.FormEvent) {
    e.preventDefault();
    await api("/profile", {
      method:"PUT",
      body:JSON.stringify(form)
    });
    setMessage("Profile saved. Open the feed to see your ranking.");
  }

  return (
    <main className="container">
      <h1>Your profile</h1>
      <p className="muted">These preferences drive Phase 1 ranking.</p>

      <form className="card" onSubmit={save}>
        <div className="row">
          <label>Name<input value={form.name||""} onChange={e=>set("name",e.target.value)} /></label>
          <label>User type
            <select value={form.user_type} onChange={e=>set("user_type",e.target.value)}>
              <option value="student">Student</option>
              <option value="professional">Working Professional</option>
            </select>
          </label>
          <label>College / University<input value={form.college||""} onChange={e=>set("college",e.target.value)} /></label>
          <label>Degree<input value={form.degree||""} onChange={e=>set("degree",e.target.value)} /></label>
          <label>Graduation year<input type="number" value={form.graduation_year||""} onChange={e=>set("graduation_year",Number(e.target.value))} /></label>
          <label>Branch<input value={form.branch||""} onChange={e=>set("branch",e.target.value)} /></label>
          <label>Years experience<input type="number" value={form.years_experience||0} onChange={e=>set("years_experience",Number(e.target.value))} /></label>
          <label>Current / target role<input value={form.current_role||""} onChange={e=>set("current_role",e.target.value)} /></label>
        </div>

        <label>Skills (comma-separated)
          <input value={(form.skills||[]).join(", ")}
            onChange={e=>set("skills",e.target.value.split(",").map((x:string)=>x.trim()).filter(Boolean))} />
        </label>
        <label>Target roles
          <input value={(form.target_roles||[]).join(", ")}
            onChange={e=>set("target_roles",e.target.value.split(",").map((x:string)=>x.trim()).filter(Boolean))} />
        </label>
        <label>Preferred locations
          <input value={(form.preferred_locations||[]).join(", ")}
            onChange={e=>set("preferred_locations",e.target.value.split(",").map((x:string)=>x.trim()).filter(Boolean))} />
        </label>
        <label>Opportunity types
          <input value={(form.preferred_types||[]).join(", ")}
            onChange={e=>set("preferred_types",e.target.value.split(",").map((x:string)=>x.trim()).filter(Boolean))} />
        </label>
        <label>Company tiers
          <input value={(form.preferred_tiers||[]).join(", ")}
            onChange={e=>set("preferred_tiers",e.target.value.split(",").map((x:string)=>x.trim()).filter(Boolean))} />
        </label>
        <label>
          <input type="checkbox" checked={!!form.women_focused}
            onChange={e=>set("women_focused",e.target.checked)} />
          Show women-focused opportunities
        </label>

        <button>Save profile</button>
        {message && <p>{message}</p>}
      </form>

      <p style={{marginTop:20}}><button onClick={()=>router.push("/feed")}>Go to personalized feed</button></p>
    </main>
  );
}
