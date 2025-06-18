from fastapi import WebSocket, Depends
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.get_db import get_async_db

router = APIRouter(tags=["account"])


@router.websocket("accounting/{thread_id}")
async def accounting_chat(websocket: WebSocket, thread_id, db : AsyncSession = Depends(get_async_db)):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(data)