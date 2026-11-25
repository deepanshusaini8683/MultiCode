import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Load environment variables from backend/.env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from the .env file")

# PostgreSQL connection
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# Database session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

# Base class for database models
class Base(DeclarativeBase):
    pass


# Dependency for FastAPI endpoints
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()