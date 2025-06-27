import uuid

from fastapi import WebSocket, Depends
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from pydantic import BaseModel
from app.models.get_db import get_async_db, get_db
from app.models.model import User
from app.models.account_agent import AccountChatHistory
from app.ai_agents.prompts import Prompts
from app.utils.user_auth import get_user_id_from_websocket, get_current_user
from app.ai_agents.account_agent import check_message, initialise_agent, message_reply_by_agent

router = APIRouter(tags=["account"])

class NameUpdate(BaseModel):
    name: str

@router.websocket("/accounting/{id}")
async def accounting_chat(id: int, websocket: WebSocket):
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

    while True:
        try:
            data = await websocket.receive_text()

            async with get_async_db() as db:
                chat = await db.get(AccountChatHistory, id)
                if not chat:
                    await websocket.send_json({"error": "This conversation does not exist"})
                    await websocket.close()
                    return
                thread_id = chat.thread_id

            message_check_prompt = Prompts.accounting_agent_query_check()
            is_valid = await check_message(message_check_prompt, data)

            if is_valid == "True":
                prompt = Prompts.accounting_agent(user.language)
                accounting_agent = await initialise_agent(prompt)
                response = await message_reply_by_agent(accounting_agent, data, thread_id)

                async with get_async_db() as db:
                    chat = await db.get(AccountChatHistory, id)
                    chat_history = chat.chat_history
                    chat_history.append({'user': data})
                    chat_history.append({'agent': response})
                    chat.chat_history = chat_history
                    await db.commit()

                await websocket.send_text(response)
            else:
                async with get_async_db() as db:
                    chat = await db.get(AccountChatHistory, id)
                    chat_history = chat.chat_history
                    chat_history.append({'user': data})
                    chat.chat_history = chat_history
                    await db.commit()

                await websocket.send_text(is_valid)

        except Exception as e:
            await websocket.close()
            break

            
@router.websocket("/new-accounting-chat")
async def new_accounting_chat(websocket: WebSocket):
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

        thread_id = uuid.uuid4()
        chat = AccountChatHistory(thread_id=str(thread_id), name="Accounting Chat", user_id=user_id)
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        chat_id = chat.id
        
    while True:
        try:
            data = await websocket.receive_text()

            async with get_async_db() as db:
                chat = await db.get(AccountChatHistory, chat_id)
                chat_history = chat.chat_history
                chat_history.append({'user': data})
                chat.chat_history = chat_history
                await db.commit()

            message_check_prompt = Prompts.accounting_agent_query_check()
            response = await check_message(message_check_prompt, data)

            if response == "True":
                prompt = Prompts.accounting_agent(user.language)
                accounting_agent = await initialise_agent(prompt)
                ai_response = await message_reply_by_agent(accounting_agent, data, thread_id)

                async with get_async_db() as db:
                    chat = await db.get(AccountChatHistory, chat_id)
                    chat_history = chat.chat_history
                    chat_history.append({'agent': ai_response})
                    chat.chat_history = chat_history
                    await db.commit()

                await websocket.send_text(ai_response)
            else:
                await websocket.send_text(response)

        except Exception as e:
            await websocket.close()
            break
        

@router.get("/get-accounting-chats")
def get_accounting_chat_history(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    chats = db.query(AccountChatHistory).filter_by(user_id=user_id).all()
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

@router.get("/get-accounting-chat/{chat_id}")
def get_accounting_chat_history(chat_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    chat = db.query(AccountChatHistory).filter_by(id=chat_id).first()
    
    if not chat:
        return JSONResponse(content={'error': 'Chat does not exist'}, status_code=404)
            
    return JSONResponse(content={'success': chat.chat_history}, status_code=200)
        
        
@router.patch("/update-chat-name/{chat_id}")
def update_chat_name(chat_id, payload: NameUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    chat = db.query(AccountChatHistory).filter_by(id=chat_id).first()
    
    if not chat:
        return JSONResponse(content={'error': 'Chat does not exist'}, status_code=404)
    
    chat.name = payload.name
    db.commit()
            
    return JSONResponse(content={'success': "name updated successfully"}, status_code=200)

@router.delete("/delete-chat/{chat_id}")
def update_chat_name(chat_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    chat = db.query(AccountChatHistory).filter_by(id=chat_id).first()
    
    if not chat:
        return JSONResponse(content={'error': 'Chat does not exist'}, status_code=404)
    
    db.delete(chat)
    db.commit()
            
    return JSONResponse(content={'success': "chat deleted successfully"}, status_code=200)
