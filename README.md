# Opportunity Radar — Phase 1 (Local MVP)

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

### 2. Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:3000

## Demo account

After seeding:

- Email: `demo@student.com`
- Password: `password123`

## Phase 1 recommendation logic

The feed score is intentionally explainable and rule-based:

- role match: +30
- skill overlap: +25
- location match: +15
- opportunity type preference: +10
- company tier preference: +10
- verified source: +5
- deadline urgency: +5

Hard filters are applied before ranking.

Do NOT add embeddings/LLMs yet. Phase 2 will introduce semantic matching, skill extraction, deduplication and richer company tiering.
