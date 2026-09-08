from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routes import applications, auth, governance, notifications, profile, opportunities

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Opportunity Radar API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(opportunities.router)
app.include_router(applications.router)
app.include_router(notifications.router)
app.include_router(governance.router)


@app.get("/")
def root():
    return {"message": "Opportunity Radar API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}
