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

No deployment is included.

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

