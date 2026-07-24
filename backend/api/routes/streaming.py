import io
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.session import get_db
from database.models import Lecture, Document
from utils.security import get_current_user

router = APIRouter()

async def get_tg_client(request: Request):
    return request.app.state.telegram_client

@router.get("/video/{message_id}")
async def stream_video(message_id: int, request: Request, db: AsyncSession = Depends(get_db),
                       user=Depends(get_current_user), tg=Depends(get_tg_client)):
    lec = (await db.execute(select(Lecture).where(Lecture.telegram_message_id == message_id))).scalar_one_or_none()
    if not lec:
        raise HTTPException(404, "Lecture not found")
    msgs = await tg.get_channel_messages(lec.chapter.telegram_channel_id, limit=1)
    if not msgs:
        raise HTTPException(404, "File not in Telegram")
    msg = msgs[0]
    file_size = lec.file_size or 0
    range_header = request.headers.get("range")
    start, end = 0, file_size - 1
    if range_header:
        range_str = range_header.replace("bytes=", "")
        parts = range_str.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1

    async def gen():
        offset = start
        async for chunk in tg.stream_file(msg, offset=offset, chunk_size=1024*1024):
            yield chunk

    headers = {
        "Content-Type": lec.mime_type or "video/mp4",
        "Accept-Ranges": "bytes",
        "Content-Length": str(end - start + 1),
    }
    status_code = 206 if range_header else 200
    if range_header:
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
    return StreamingResponse(gen(), status_code=status_code, headers=headers)

@router.get("/pdf/{message_id}")
async def serve_pdf(message_id: int, request: Request, db: AsyncSession = Depends(get_db),
                    user=Depends(get_current_user), tg=Depends(get_tg_client)):
    doc = (await db.execute(select(Document).where(Document.telegram_message_id == message_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")
    msgs = await tg.get_channel_messages(doc.chapter.telegram_channel_id, limit=1)
    if not msgs:
        raise HTTPException(404, "File not in Telegram")
    pdf_bytes = io.BytesIO()
    async for chunk in tg.stream_file(msgs[0]):
        pdf_bytes.write(chunk)
    pdf_bytes.seek(0)
    return Response(pdf_bytes.read(), media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{doc.file_name}"'})
