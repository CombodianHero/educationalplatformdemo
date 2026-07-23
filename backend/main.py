"""
Main FastAPI application for Telegram MTProto Streaming Platform
Proof of Concept - Educational Video & PDF Streaming
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import auth, courses, streaming, admin
from database.session import engine, Base
from telegram.client import TelegramClient
from utils.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting Telegram MTProto Streaming Platform...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")
    
    # Initialize Telegram client
    app.state.telegram_client = TelegramClient()
    await app.state.telegram_client.start()
    logger.info("Telegram client initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await app.state.telegram_client.stop()
    await engine.dispose()


# Create FastAPI application
app = FastAPI(
    title="Telegram MTProto Streaming Platform",
    description="Educational Video & PDF Streaming via Telegram MTProto",
    version="1.0.0-PoC",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(courses.router, prefix="/api", tags=["Courses"])
app.include_router(streaming.router, prefix="/api", tags=["Streaming"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])


@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "healthy",
        "service": "Telegram MTProto Streaming Platform",
        "version": "1.0.0-PoC",
        "documentation": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "telegram_connected": app.state.telegram_client.is_connected()
    }
