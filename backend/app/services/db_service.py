from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.orm import Base, User  # Import User to ensure it's registered

DATABASE_URL = "sqlite:///./catalyst.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database if not using Alembic migrations
def init_db():
    # Create all tables including User table
    Base.metadata.create_all(bind=engine)
