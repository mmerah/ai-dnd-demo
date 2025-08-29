"""
FastAPI application entry point for D&D 5e AI Dungeon Master.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Load environment variables
load_dotenv()

# Import configuration and API routes
from app.api.routes import router as api_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifecycle - startup and shutdown events.
    """
    # Startup
    print("Starting D&D 5e AI Dungeon Master...")

    # Initialize settings - this will validate all required environment variables
    try:
        settings = get_settings()
        print(f"Save directory: {settings.save_directory}")
        print(f"Using model: {settings.openrouter_model}")
    except Exception as e:
        raise RuntimeError(f"Configuration error: {e}")

    print("Application started successfully!")

    yield

    # Shutdown
    print("Shutting down D&D 5e AI Dungeon Master...")


# Create FastAPI app instance
app = FastAPI(
    title="D&D 5e AI Dungeon Master",
    description="AI-powered Dungeon Master for D&D 5e gameplay",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Serve static files (frontend)
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

    @app.get("/")
    async def serve_frontend() -> FileResponse:
        """Serve the main frontend HTML file."""
        index_path = frontend_path / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        else:
            raise HTTPException(status_code=404, detail="Frontend not found")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all uncaught exceptions.
    Follows fail-fast principle - no silent failures.
    """
    import traceback

    error_detail = {
        "error": str(exc),
        "type": type(exc).__name__,
        "traceback": traceback.format_exc() if get_settings().debug_ai else None,
    }

    # Log the error
    print(f"Unhandled exception: {error_detail}")

    return JSONResponse(status_code=500, content=error_detail)


# Health check endpoint
@app.get("/health")
async def health_check() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "D&D 5e AI Dungeon Master"}


if __name__ == "__main__":
    import uvicorn

    port = get_settings().port
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # Enable auto-reload during development
        log_level="info",
    )
