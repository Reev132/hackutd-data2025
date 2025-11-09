from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.orm import Base

DATABASE_URL = "postgresql://user:password@localhost:5432/yourdb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database if not using Alembic migrations
def init_db():
    Base.metadata.create_all(bind=engine)
