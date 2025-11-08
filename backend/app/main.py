from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables BEFORE importing routes
# Look for .env in the backend directory (parent of app/)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.routes import catalyst

app = FastAPI(
    title="Catalyst API",
    description="AI PM productivity agent powered by NVIDIA Nemotron",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(catalyst.router, prefix="/api/catalyst", tags=["catalyst"])

@app.get("/")
async def root():
    return {"message": "Catalyst API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
