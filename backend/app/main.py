# CRITICAL: Load .env BEFORE any app imports
# Otherwise services initialize without environment variables
from dotenv import load_dotenv
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(backend_dir, ".env")
print(f"[ENV] Loading from: {env_path}")
print(f"[ENV] File exists: {os.path.exists(env_path)}")
loaded = load_dotenv(env_path)
print(f"[ENV] Loaded successfully: {loaded}")
print(f"[ENV] DEEPGRAM_API_KEY present: {bool(os.getenv('DEEPGRAM_API_KEY'))}")

# NOW import app modules (they can read env vars)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import catalyst, voice
from app.services.firebase_service import initialize_firebase, cleanup_firebase


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app.
    Handles startup and shutdown events.
    """
    # Startup: Initialize Firebase
    try:
        initialize_firebase()
        print("✓ Application started successfully")
    except FileNotFoundError as e:
        print(f"⚠ WARNING: {str(e)}")
        print("  The backend will not work until Firebase credentials are configured.")
    except Exception as e:
        print(f"✗ ERROR: Failed to initialize Firebase: {str(e)}")
        raise

    yield

    # Shutdown: Cleanup Firebase resources
    cleanup_firebase()
    print("✓ Application shutdown complete")


app = FastAPI(
    title="AI Project Manager Backend",
    lifespan=lifespan
)

# CORS middleware - allows frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, OPTIONS)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(catalyst.router)
app.include_router(voice.router)
