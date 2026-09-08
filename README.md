# Opportunity Radar — Phase 2 (Local MVP)

India-first opportunity intelligence platform for students and working professionals.

Phase 1 implements:
- JWT authentication
- Student / professional profile
- Opportunity database
- Verified-source flag
- Search + filters
- Rule-based personalized feed
- Save opportunities
- Local SQLite database (easy to migrate to PostgreSQL later)

Phase 2 adds:
- Profile and opportunity skill matching
- Sentence Transformers semantic similarity when the model is available
- Deterministic token similarity fallback for offline/local development
- Better duplicate suppression across opportunity sources
- Automatic company tier inference for known organizations
- Semantic match scores and "Why this matches you" explanations in the feed

## Recommendation engine

The feed now uses a two-stage recommendation pipeline:

1. Candidate generation combines profile/opportunity content similarity, similarity to positively interacted opportunities, and global popularity.
2. Ranking blends the existing profile rules with retrieval signals and returns the ranking score and candidate sources for each item.

`view`, `save`, `apply`, and `dismiss` events are stored in an interaction table and represented as a sparse user-item matrix. The authenticated `GET /opportunities/recommendation-diagnostics` endpoint exposes matrix dimensions, candidate sources, top-K IDs, cold-start state, and `Precision@K`, `Recall@K`, and `NDCG@K` over observed positive interactions.

New users without meaningful profile data or interactions use popularity and deterministic recency-independent fallback retrieval. Content similarity uses token cosine similarity by default; installing `sentence-transformers` activates the existing MiniLM embedding backend automatically, leaving the engine ready for a future persisted embedding index.

No deployment is included.

## Phase 3: tracking and notifications

The profile workspace at `/profile` now includes an application tracker and alert settings. Saving an opportunity from the feed creates both a bookmark and a `saved` tracker item. Tracker statuses are `saved`, `applied`, `interview`, `offer`, `rejected`, and `withdrawn`.

Notification endpoints include:

- `GET/PUT /notifications/preferences`
- `GET /notifications/deadline-alerts` and `POST /notifications/deadline-alerts/send`
- `GET /notifications/digest` and `POST /notifications/digest/send`
- `GET /notifications/history`

Sends are recorded as `preview` when credentials are absent, which keeps local development safe. Configure real delivery with `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, `TELEGRAM_BOT_TOKEN`, and a Telegram chat ID saved in notification preferences. A production deployment should call the send endpoints from a daily scheduler or worker.

## Stack

Frontend:
- Next.js + TypeScript
- React
- Plain CSS for Phase 1 simplicity

Backend:
- FastAPI + Python
- SQLAlchemy
- SQLite locally
- JWT authentication
- Pydantic
- Optional Sentence Transformers for enhanced semantic matching

## Run

### 1. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

python -m app.seed
uvicorn app.main:app --reload
```

Backend: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs

The API uses a deterministic token-similarity fallback by default. For the
optional enhanced semantic model, install Sentence Transformers separately:

```bash
pip install sentence-transformers
```

The first personalized-feed request may then download the `all-MiniLM-L6-v2`
model. If it cannot be downloaded or loaded, the API continues using the
deterministic fallback.

### 2. Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:3000

## Git workflow

Keep `node_modules`, `.next`, Python caches, virtual environments, and local
database files out of Git. They are covered by the repository `.gitignore` and
should not be deleted before committing.

```bash
git status
git add .
git commit -m "Build Phase 2 semantic opportunity matching"
git push origin main
```

If your branch is not `main`, replace `main` with the current branch name.

