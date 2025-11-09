from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import catalyst
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
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, OPTIONS)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(catalyst.router)
