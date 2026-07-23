"""
Main FastAPI application for Telegram MTProto Streaming Platform
Proof of Concept - Educational Video & PDF Streaming

Auto-generates session string on first run
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import auth, courses, streaming, admin
from database.session import engine, Base
from telegram.client import TelegramClient
from utils.config import settings, initialize_session

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
    Auto-generates Telegram session if needed
    """
    # Startup
    logger.info("="*60)
    logger.info("Starting Telegram MTProto Streaming Platform...")
    logger.info("="*60)
    
    try:
        # Auto-generate or validate session string
        logger.info("🔑 Checking Telegram session...")
        session = await initialize_session()
        logger.info("✅ Session ready")
        
        # Create database tables
        logger.info("📦 Initializing database...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables ready")
        
        # Initialize Telegram client
        logger.info("🔌 Connecting to Telegram MTProto...")
        app.state.telegram_client = TelegramClient()
        await app.state.telegram_client.start()
        logger.info("✅ Telegram client connected")
        
        logger.info("="*60)
        logger.info("🚀 Platform is ready!")
        logger.info(f"📡 API: http://{settings.host}:{settings.port}")
        logger.info(f"📚 Docs: http://{settings.host}:{settings.port}/docs")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("="*60)
    logger.info("Shutting down platform...")
    
    if hasattr(app.state, 'telegram_client'):
        await app.state.telegram_client.stop()
        logger.info("✅ Telegram client disconnected")
    
    await engine.dispose()
    logger.info("✅ Database connections closed")
    logger.info("👋 Goodbye!")
    logger.info("="*60)


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
        "documentation": "/docs",
        "telegram_connected": app.state.telegram_client.is_connected() if hasattr(app.state, 'telegram_client') else False
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    telegram_status = "disconnected"
    if hasattr(app.state, 'telegram_client'):
        telegram_status = "connected" if app.state.telegram_client.is_connected() else "disconnected"
    
    return {
        "status": "healthy",
        "telegram": telegram_status,
        "database": "connected",
        "timestamp": logging.Formatter().formatTime(logging.LogRecord(
            name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
        ))
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
