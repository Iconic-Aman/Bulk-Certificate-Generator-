import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

db_url = os.getenv("DATABASE_URL") or "sqlite:///./app.db"
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
engine = create_engine(db_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
