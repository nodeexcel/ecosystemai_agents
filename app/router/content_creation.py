import os, uuid, datetime, time, requests

from fastapi import WebSocket, Depends
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.get_db import get_async_db, get_db
from app.models.model import User
from app.models.content_creation_agent import ContentCreationChatHistory, Content
from app.schemas.content_creation import NameUpdate, PredisCheck, ContentCreateSchema
from app.prompts.content_creation import content_creation_agent_prompt
from app.utils.user_auth import get_user_id_from_websocket, get_current_user
from app.ai_agents.content_creation_agent import initialise_agent, message_reply_by_agent
from app.services.babel import get_translator_dependency
from app.utils.chatbots import summarizing_initial_chat

router = APIRouter(tags=["content-creation-agent"])

@router.websocket("/content-creation-agent/{id}")
async def content_creation_chat(id: int, websocket: WebSocket):
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
                chat = await db.get(ContentCreationChatHistory, id)
                if not chat:
                    await websocket.send_json({"error": "This conversation does not exist"})
                    await websocket.close()
                    return
    
                thread_id = chat.thread_id
                prompt = content_creation_agent_prompt(language)
                content_creation_agent = await initialise_agent(prompt)
                ai_response = await message_reply_by_agent(content_creation_agent, data, thread_id)

                async with get_async_db() as db:
                    chat = await db.get(ContentCreationChatHistory, id)
                    chat_history = chat.chat_history
                    chat_history.append({'user': data, 'message_at': str(datetime.datetime.now(datetime.timezone.utc))})
                    time_now = datetime.datetime.now(datetime.timezone.utc)
                    chat_history.append({'agent': ai_response, 'message_at': str(time_now)})
                    chat.chat_history = chat_history
                    await db.commit()

                await websocket.send_json({'agent': ai_response, 'message_at': str(time_now)})

        except Exception as e:
            await websocket.close()
            break

            
@router.websocket("/new-content-creation-agent-chat")
async def new_content_creation_chat(websocket: WebSocket):
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
        chat = ContentCreationChatHistory(thread_id=str(thread_id), name="Content Creation Chat", user_id=user_id, chat_history=[])
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        chat_id = chat.id
        
    while True:
        try:
            data = await websocket.receive_text()
            
            chat_title = await summarizing_initial_chat(data)

            async with get_async_db() as db:
                chat = await db.get(ContentCreationChatHistory, chat_id)
                chat_history = chat.chat_history
                chat_history.append({'user': data, 'message_at': str(datetime.datetime.now(datetime.timezone.utc))})
                chat.chat_history = chat_history
                chat.name = chat_title
                await db.commit()

                prompt = content_creation_agent_prompt(language)
                content_creation_agent = await initialise_agent(prompt)
                ai_response = await message_reply_by_agent(content_creation_agent, data, thread_id)

                async with get_async_db() as db:
                    chat = await db.get(ContentCreationChatHistory, chat_id)
                    chat_history = chat.chat_history
                    time_now = datetime.datetime.now(datetime.timezone.utc)
                    chat_history.append({'agent': ai_response, 'message_at': str(time_now)})
                    chat.chat_history = chat_history
                    await db.commit()

                await websocket.send_json({'agent': ai_response, 'message_at': str(time_now)})

        except Exception as e:
            await websocket.close()
            break
        

@router.get("/get-content-creation-chats")
def get_content_creation_chats(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)
                  , _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    chats = db.query(ContentCreationChatHistory).filter_by(user_id=user_id).all()
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

@router.get("/get-content-creation-chat/{chat_id}")
def get_content_creation_chat_history(chat_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user),
                         _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    chat = db.query(ContentCreationChatHistory).filter_by(id=chat_id).first()
    
    if not chat:
        return JSONResponse(content={'error': 'Chat does not exist'}, status_code=404)
            
    return JSONResponse(content={'success': chat.chat_history}, status_code=200)
        
        
@router.patch("/update-content-creation-chat-name/{chat_id}")
def update_content_creation_name(chat_id, payload: NameUpdate, db: Session = Depends(get_db),
                         user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    chat = db.query(ContentCreationChatHistory).filter_by(id=chat_id).first()
    
    if not chat:
        return JSONResponse(content={'error': _('Chat does not exist')}, status_code=404)
    
    chat.name = payload.name
    db.commit()
            
    return JSONResponse(content={'success': _("name updated successfully")}, status_code=200)

@router.delete("/delete-content-creation-chat/{chat_id}")
def delete_content_creation_chat(chat_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user),
                    _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    chat = db.query(ContentCreationChatHistory).filter_by(id=chat_id).first()
    
    if not chat:
        return JSONResponse(content={'error': _('Chat does not exist')}, status_code=404)
    
    db.delete(chat)
    db.commit()
            
    return JSONResponse(content={'success': _("chat deleted successfully")}, status_code=200)


@router.post("/check-predis")
def webhook_for_predis(payload: PredisCheck, db: Session = Depends(get_db)):
    
    post_id = payload.post_id
    content = db.query(Content).filter_by(post_id=post_id).first()
    if payload.status == "error":
        if content:
            content.post_status = "error"
            db.commit()
        return JSONResponse(content={'error': "Previous request of content creation could no proceed due to some issue. Please try again"}, status_code=500)
    
    if payload.status == "completed":
        content.media_urls = payload.generated_media
        content.caption = payload.caption
        content.post_status = 'completed'
        db.commit()
        
    return JSONResponse(content={"success": "conteent generated"}, status_code=200)

@router.post("/create-content")
def create_content(payload: ContentCreateSchema, db: Session = Depends(get_db),
                   user_id: str = Depends(get_current_user)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    if payload.post_type == 'quotes' and payload.author is None:
        return JSONResponse(content={"error": "please provide author for quotes"}, status_code=400)
    
    text = payload.text.split()
    if len(text) <= 3:
        return JSONResponse(content={"text": "Text length is too small"}, status_code=400)
    
    if payload.media_type == 'video':
        
        if payload.post_type == 'meme':
            return JSONResponse(content={"post_type": "meme post type is not supported for video"}, status_code=400)
        
        if not payload.video_duration:
            payload.video_duration = 'short'
            
        data = {'brand_id': os.getenv("BRAND_ID"),
        'text': payload.text,
        'post_type': payload.post_type,
        'video_duration': payload.video_duration,
        'media_type': 'video'}
    
    if payload.media_type == "single_image":
        data = {'brand_id': os.getenv("BRAND_ID"),
        'text': payload.text,
        'post_type': payload.post_type,
        'media_type': 'single_image'}
    
    if payload.media_type == "carousel":
        data = {'brand_id': os.getenv("BRAND_ID"),
        'text': payload.text,
        'post_type': payload.post_type,
        'media_type': 'carousel'}
        
    response = requests.post(os.getenv('CONTENT_GENERATE_API_URL'), data=data,
                             headers={'authorization':os.getenv('CONTENT_GENERATE_API_KEY')})
    
    if response.status_code != 200:
        time.sleep(30)
        response = requests.post(os.getenv('CONTENT_GENERATE_API_URL'), data=data,
                                 headers={'authorization': os.getenv('CONTENT_GENERATE_API_KEY')})
        if response.status_code == 400:
            return JSONResponse({'error': 'There is some processing issue. Please try again later'}, status_code=500)
        
    if response.status_code == 200:
        response_data = response.json()
        
        post_ids = response_data.get('post_ids')
        for post_id in post_ids:
            content = Content(**payload.model_dump(), post_id=post_id, user_id=user_id)
            db.add(content)
            db.commit()
            db.refresh(content)
            print(response.status_code, response.text)
            return JSONResponse(content={'content_id': content.id, 'status': 'in_progress',
                                        'message': 'content generation has started'}, status_code=200)

@router.get('/content-generation-status')
def content_generation_status(content_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    content = db.query(Content).filter_by(id=content_id).first()
    
    if not content:
        return JSONResponse(content={'error': 'content does not exist'}, status_code=404)
    
    if content.post_status == 'in_progress':
        return JSONResponse(content={'status': 'in_progress', 'message': 'content generation is in progress'}, status_code=200)
    
    if content.post_status == 'completed':
        return JSONResponse(content={'status': 'completed', 'message': 'content generation is completed', 'media_type': content.media_type,
                                     'media_urls': content.media_urls, 'caption': content.caption}, status_code=200)
    
    
    