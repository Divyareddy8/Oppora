from .database import Base, SessionLocal, engine
from .ingestion import ingest_configured
from . import models

Base.metadata.create_all(bind=engine)
db = SessionLocal()
try:
    print(ingest_configured(db))
finally:
    db.close()
