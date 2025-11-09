"""
Main FastAPI application for AutoCut
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .api.routes import router as phase1_router
# Phase 2 routes disabled - simplified version (no shorts, no OpenAI optimization)
# from .api.routes_phase2 import router as phase2_router
from .config import settings
from .database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AutoCut API - Simplified",
    description="Automatic silence and filler words detection with local AI title generation",
    version="2.1.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(phase1_router, prefix="/api")
# Phase 2 routes disabled - simplified version
# app.include_router(phase2_router, prefix="/api")

# Mount static files for outputs (thumbnails, etc.)
app.mount("/outputs", StaticFiles(directory=str(settings.OUTPUT_DIR)), name="outputs")

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AutoCut",
        "version": "1.0.0"
    }


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting AutoCut API server")
    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")
    logger.info(f"Output directory: {settings.OUTPUT_DIR}")
    logger.info(f"Temp directory: {settings.TEMP_DIR}")

    # Ensure directories exist
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize database
    logger.info("Initializing database...")
    init_db()

    logger.info("AutoCut API server started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down AutoCut API server")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level="info"
    )
