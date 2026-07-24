import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.session import engine, Base
from telegram.client import TelegramClient
from utils.config import settings
from utils.session_manager import SessionManager
from api.routes import auth, courses, streaming, admin

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    session_mgr = SessionManager(settings.api_id, settings.api_hash)
    settings.session_string = await session_mgr.get_or_create_session()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.telegram_client = TelegramClient()
    await app.state.telegram_client.start()
    logger.info("🚀 Platform started")
    yield
    # Shutdown
    await app.state.telegram_client.stop()
    await engine.dispose()

app = FastAPI(title="Telegram MTProto Streaming", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(courses.router, prefix="/api", tags=["Courses"])
app.include_router(streaming.router, prefix="/api", tags=["Streaming"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])

@app.get("/")
def root():
    return {"status": "running", "telegram": app.state.telegram_client.is_connected()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)
