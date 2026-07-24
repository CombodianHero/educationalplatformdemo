from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_db
from utils.security import get_admin_user
from services.sync_service import TelegramSyncService

router = APIRouter()

@router.post("/telegram/sync")
async def sync_telegram(request: Request, db: AsyncSession = Depends(get_db), admin=Depends(get_admin_user)):
    tg = request.app.state.telegram_client
    sync_svc = TelegramSyncService(db, tg)
    result = await sync_svc.sync_all()
    return {"status": "ok", **result}
