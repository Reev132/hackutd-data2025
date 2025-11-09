from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import catalyst
from app.services.db_service import init_db

app = FastAPI(title="AI Project Manager Backend")

# CORS middleware - allows frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, OPTIONS)
    allow_headers=["*"],  # Allow all headers
)

# Initialize DB on startup
init_db()

app.include_router(catalyst.router)
