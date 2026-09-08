import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./opportunity_radar.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_schema():
    """Add small additive columns for existing local SQLite databases."""
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("opportunities")}
    if "eligible_branches" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE opportunities ADD COLUMN eligible_branches VARCHAR(30) DEFAULT ''"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
