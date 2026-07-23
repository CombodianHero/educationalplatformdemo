"""
Video and PDF streaming API routes
Core functionality for MTProto streaming
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.session import get_db
from database.models import Lecture, Document
from utils.security import get_current_user
from telegram.client import TelegramClient

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_telegram_client(request: Request) -> TelegramClient:
    """Dependency to get Telegram client from app state"""
    return request.app.state.telegram_client


@router.get("/video/{message_id}")
async def stream_video(
    message_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    telegram_client: TelegramClient = Depends(get_telegram_client)
):
    """
    Stream video from Telegram via MTProto
    
    Supports HTTP Range requests for seeking and partial content
    
    Args:
        message_id: Telegram message ID of the video
        request: FastAPI request object (for range headers)
        db: Database session
        current_user: Authenticated user
        telegram_client: Telegram MTProto client
        
    Returns:
        StreamingResponse with video data
    """
    logger.info(f"Video stream requested: message_id={message_id}, user={current_user['username']}")
    
    # Verify lecture exists in database
    result = await db.execute(
        select(Lecture).where(Lecture.telegram_message_id == message_id)
    )
    lecture = result.scalar_one_or_none()
    
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture not found"
        )
    
    try:
        # Get the message from Telegram
        messages = await telegram_client.get_channel_messages(
            channel_id=lecture.chapter.telegram_channel_id,
            limit=1,
            offset_id=message_id
        )
        
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found in Telegram"
            )
        
        message = messages[0]
        
        # Get file size
        file_size = lecture.file_size or await telegram_client.get_file_size(message)
        
        # Handle HTTP Range requests
        range_header = request.headers.get("range")
        start = 0
        end = file_size - 1
        
        if range_header:
            # Parse range header (e.g., "bytes=0-1023")
            range_str = range_header.replace("bytes=", "")
            ranges = range_str.split("-")
            
            start = int(ranges[0]) if ranges[0] else 0
            end = int(ranges[1]) if len(ranges) > 1 and ranges[1] else file_size - 1
            
            if start >= file_size or end >= file_size:
                raise HTTPException(
                    status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                    detail="Range not satisfiable"
                )
        
        # Create async generator for streaming
        async def video_stream_generator():
            chunk_size = 1024 * 1024  # 1MB chunks
            bytes_streamed = 0
            current_offset = start
            
            try:
                async for chunk in telegram_client.stream_file(
                    message=message,
                    offset=current_offset,
                    chunk_size=chunk_size
                ):
                    if bytes_streamed >= (end - start + 1):
                        break
                    yield chunk
                    bytes_streamed += len(chunk)
                    current_offset += len(chunk)
                    
            except Exception as e:
                logger.error(f"Error streaming video: {e}")
                raise
        
        content_length = end - start + 1
        
        headers = {
            "Content-Type": lecture.mime_type or "video/mp4",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Disposition": f'inline; filename="{lecture.file_name or "video.mp4"}"',
        }
        
        if range_header:
            headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            status_code = status.HTTP_206_PARTIAL_CONTENT
        else:
            status_code = status.HTTP_200_OK
        
        return StreamingResponse(
            video_stream_generator(),
            status_code=status_code,
            headers=headers,
            media_type=lecture.mime_type or "video/mp4"
        )
        
    except Exception as e:
        logger.error(f"Failed to stream video {message_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Streaming failed: {str(e)}"
        )


@router.get("/pdf/{message_id}")
async def serve_pdf(
    message_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    telegram_client: TelegramClient = Depends(get_telegram_client)
):
    """
    Serve PDF document from Telegram
    
    Args:
        message_id: Telegram message ID of the PDF
        request: FastAPI request object
        db: Database session
        current_user: Authenticated user
        telegram_client: Telegram MTProto client
        
    Returns:
        Response with PDF data
    """
    logger.info(f"PDF requested: message_id={message_id}, user={current_user['username']}")
    
    # Verify document exists in database
    result = await db.execute(
        select(Document).where(Document.telegram_message_id == message_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        # Get the message from Telegram
        messages = await telegram_client.get_channel_messages(
            channel_id=document.chapter.telegram_channel_id,
            limit=1,
            offset_id=message_id
        )
        
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found in Telegram"
            )
        
        message = messages[0]
        
        # Stream the PDF
        pdf_bytes = io.BytesIO()
        async for chunk in telegram_client.stream_file(message):
            pdf_bytes.write(chunk)
        
        pdf_bytes.seek(0)
        
        return Response(
            content=pdf_bytes.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{document.file_name or "document.pdf"}"',
                "Content-Length": str(document.file_size)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to serve PDF {message_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to serve PDF: {str(e)}"
        )
