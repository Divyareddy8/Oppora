# Oppora

Oppora is an opportunity discovery and application-tracking platform for students and working professionals. It combines personalized recommendations, application tracking, deadline alerts, and notification delivery in one workspace.

## Features

- Email registration and JWT login
- Student and professional profiles
- Years-of-experience and seniority matching
- Target-company preferences
- Personalized opportunity feed with search and filters
- Official-source coverage from seeded company portals across Bangalore, Hyderabad, Chennai, Mumbai, and Gurgaon
- Skill, role, location, type, tier, and semantic matching
- Content-based and interaction-based recommendations
- Cold-start recommendations for new users
- Click, save, apply, and dismiss tracking
- Learned user preferences and ranking diagnostics
- Saved opportunities and application tracker
- Application statuses: saved, applied, interview, offer, rejected, withdrawn
- Follow-up dates and application notes
- Deadline alerts and daily digest previews
- Email notifications through SMTP
- Telegram notifications through a Telegram bot
- User reports for expired, incorrect, duplicate, spam, or unsafe listings
- Admin moderation and source-health checks
- Recommendation metrics: Precision@K, Recall@K, and NDCG
- Admin analytics for interactions, reports, moderation, and source health

## How to use

1. Register with a Gmail address and log in.
2. Complete your profile with your role, experience, skills, locations, and preferred opportunity types.
3. Open the feed, search or filter opportunities, and review the match explanations.
4. Save an opportunity to add it to your workspace.
5. Open **Profile** to update application status, follow-up dates, and notes.
6. Use **Alerts & delivery** to configure email, Telegram, deadline alerts, and daily digest settings.
7. Report inaccurate or unsafe listings from the opportunity API when needed.

Saving an opportunity creates both a bookmark and a `saved` tracker entry. Updating a tracker item to `applied`, `interview`, or `offer` improves future recommendations.

## Run locally

### Backend

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload
```

Backend: http://127.0.0.1:8000
API documentation: http://127.0.0.1:8000/docs

### Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:3000

The default demo account is `demo@student.com` with password `password123` after running the seed command.

### Fetch live jobs

The built-in importer supports public Greenhouse, Lever, Ashby, SmartRecruiters, and configured Workday JSON endpoints. Workday URLs vary by company, so provide the exact official endpoint. Set comma-separated board IDs, company handles, or Workday URLs, then run:

```powershell
$env:GREENHOUSE_BOARDS="company-one,company-two"
$env:LEVER_SITES="company-one"
$env:ASHBY_BOARDS="company-one"
$env:SMARTRECRUITERS_COMPANIES="company-one"
$env:WORKDAY_ENDPOINTS="https://company.wd5.myworkdayjobs.com/wday/cxs/company/site/jobs"
python -m app.fetch_jobs
```

Fetched records are marked as verified and deduplicated by source URL. The importer is intentionally opt-in so local development does not depend on external portals or overload them.

## Optional notifications and embeddings

Without notification credentials, sends are stored as local previews. Configure real delivery with:

- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`
- `TELEGRAM_BOT_TOKEN` and a Telegram chat ID in the profile settings

For enhanced semantic recommendations:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install sentence-transformers
```

Oppora falls back to deterministic token similarity if the embedding model is unavailable.

## Admin

Set `ADMIN_EMAILS` to a comma-separated list of administrator emails. Admin endpoints cover reports, moderation, source-health checks, and analytics. A scheduler or worker should call notification send endpoints for automatic daily delivery.

## Stack

Next.js, React, TypeScript, FastAPI, SQLAlchemy, SQLite, Pydantic, and JWT authentication.
