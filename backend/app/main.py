from fastapi import FastAPI
from app.routes import catalyst
from app.services.db_service import init_db

app = FastAPI(title="AI Project Manager Backend")

# Initialize DB on startup
init_db()

app.include_router(catalyst.router)
