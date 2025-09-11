import uuid, datetime

from fastapi import WebSocket, Depends
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from pydantic import BaseModel
from app.models.get_db import get_async_db, get_db
from app.models.model import User
from app.models.coo_agent import CooChatHistory
from app.prompts.coo_agent import coo_agent_prompt
from app.utils.user_auth import get_user_id_from_websocket, get_current_user
from app.ai_agents.coo_agent import initialise_agent, message_reply_by_agent
from app.services.babel import get_translator_dependency
from app.utils.chatbots import summarizing_initial_chat

router = APIRouter(tags=["coo-agent"])

class NameUpdate(BaseModel):
    name: str

@router.websocket("/coo-agent/{id}")
async def coo_agent_chat(id: int, websocket: WebSocket):
    await websocket.accept()
    token = websocket.query_params.get("token")
    user_id = await get_user_id_from_websocket(websocket, token)
    async with get_async_db() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            await websocket.send_json({"error": "User does not exist"})
            await websocket.close()
            return
        language = user.language

    while True:
        try:
            data = await websocket.receive_text()

            async with get_async_db() as db:
                chat = await db.get(CooChatHistory, id)
                if not chat:
                    await websocket.send_json({"error": "This conversation does not exist"})
                    await websocket.close()
                    return
    
                thread_id = chat.thread_id
                prompt = coo_agent_prompt(language)
                coo_agent = await initialise_agent(prompt)
                ai_response = await message_reply_by_agent(coo_agent, data, thread_id)

                async with get_async_db() as db:
                    chat = await db.get(CooChatHistory, id)
                    chat_history = chat.chat_history
                    chat_history.append({'user': data, 'message_at': str(datetime.datetime.now(datetime.timezone.utc))})
                    time_now = datetime.datetime.now(datetime.timezone.utc)
                    chat_history.append({'agent': ai_response, 'message_at': str(time_now)})
                    chat.chat_history = chat_history
                    await db.commit()

                await websocket.send_json({'agent': ai_response, 'language': language, 'message_at': str(time_now)})

        except Exception as e:
            await websocket.close()
            break

            
@router.websocket("/new-coo-agent-chat")
async def new_coo_agent_chat(websocket: WebSocket):
    await websocket.accept()

    token = websocket.query_params.get("token")
    user_id = await get_user_id_from_websocket(websocket, token)

    async with get_async_db() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            await websocket.send_json({"error": "User does not exist"})
            await websocket.close()
            return

        language = user.language
        thread_id = uuid.uuid4()
        chat = CooChatHistory(thread_id=str(thread_id), name="Coo Agent Chat", user_id=user_id, chat_history=[])
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        chat_id = chat.id
        
    while True:
        try:
            data = await websocket.receive_text()
            
            chat_name = await summarizing_initial_chat(data)

            async with get_async_db() as db:
                chat = await db.get(CooChatHistory, chat_id)
                chat_history = chat.chat_history
                chat_history.append({'user': data, 'message_at': str(datetime.datetime.now(datetime.timezone.utc))})
                chat.chat_history = chat_history
                chat.name = chat_name
                await db.commit()

                prompt = coo_agent_prompt(language)
                coo_agent = await initialise_agent(prompt)
                ai_response = await message_reply_by_agent(coo_agent, data, thread_id)

                async with get_async_db() as db:
                    chat = await db.get(CooChatHistory, chat_id)
                    chat_history = chat.chat_history
                    time_now = datetime.datetime.now(datetime.timezone.utc)
                    chat_history.append({'agent': ai_response, 'message_at': str(time_now)})
                    chat.chat_history = chat_history
                    await db.commit()

                await websocket.send_json({'agent': ai_response, 'message_at': str(time_now)})

        except Exception as e:
            await websocket.close()
            break
        

@router.get("/get-coo-chats")
def get_coo_chats(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)
                  , _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    chats = db.query(CooChatHistory).filter_by(user_id=user_id).all()
    response = []
    if chats:
        for chat in chats:
            chat_instance = {}
            chat_instance['name'] = chat.name
            chat_instance['chat_id'] = chat.id
            chat_instance['created_at'] = str(chat.created_at)
            response.append(chat_instance)
            
        return JSONResponse(content={'success': response}, status_code=200)
    return JSONResponse(content={'success': []}, status_code=200)

@router.get("/get-coo-chat/{chat_id}")
def get_coo_chat_history(chat_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user),
                         _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    chat = db.query(CooChatHistory).filter_by(id=chat_id).first()
    
    if not chat:
        return JSONResponse(content={'error': 'Chat does not exist'}, status_code=404)
            
    return JSONResponse(content={'success': chat.chat_history}, status_code=200)
        
        
@router.patch("/update-coo-chat-name/{chat_id}")
def update_coo_chat_name(chat_id, payload: NameUpdate, db: Session = Depends(get_db),
                         user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    chat = db.query(CooChatHistory).filter_by(id=chat_id).first()
    
    if not chat:
        return JSONResponse(content={'error': _('Chat does not exist')}, status_code=404)
    
    chat.name = payload.name
    db.commit()
            
    return JSONResponse(content={'success': _("name updated successfully")}, status_code=200)

@router.delete("/delete-coo-chat/{chat_id}")
def delete_coo_chat(chat_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user),
                    _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    chat = db.query(CooChatHistory).filter_by(id=chat_id).first()
    
    if not chat:
        return JSONResponse(content={'error': _('Chat does not exist')}, status_code=404)
    
    db.delete(chat)
    db.commit()
            
    return JSONResponse(content={'success': _("chat deleted successfully")}, status_code=200)
