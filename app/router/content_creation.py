import json, os, uuid, datetime, requests
from datetime import date, time, timezone
from io import BytesIO
from typing import Optional

from fastapi import WebSocket, Depends, File, UploadFile, Form, status
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse
from langchain.chains.summarize import load_summarize_chain
from langchain_core.documents import Document
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.get_db import get_async_db, get_db
from app.models.model import User
from app.models.content_creation_agent import (
    ContentCreationChatHistory, 
    Content,
    LinkedInPost, 
    XPost, 
    YoutubeScript, 
    ScheduledContent
)
from app.models.social_media_integrations import Instagram, LinkedIn
from app.schemas.content_creation import (NameUpdate, PredisCheck, ContentCreateSchema,
                                          LinkedInPostSchema, ContentUpdateSchema, XPostSchema,
                                          YoutubeScriptSchema)
from app.prompts.content_creation import (content_creation_agent_prompt, linked_post_prompt_generation,
                                          x_post_prompt_generator, youtube_script_prompt_generator)
from app.utils.user_auth import get_user_id_from_websocket, get_current_user
from app.ai_agents.content_creation_agent import initialise_agent, message_reply_by_agent, text_content_generation
from app.ai_agents.email_agent import llm
from app.services.babel import get_translator_dependency
from app.services.aws_boto3 import aws_client, get_upload_args
from app.utils.chatbots import summarizing_initial_chat
from app.utils.current_user import current_user
from app.utils.instagram import publish_content_instagram
from app.utils.linkedin import publish_content_linkedin
from app.utils.attachment_kb import process_attachment_to_pinecone

router = APIRouter(tags=["content-creation-agent"])

@router.websocket("/content-creation-agent/{id}")
async def content_creation_chat(id: int, websocket: WebSocket):
    await websocket.accept()
    token = websocket.query_params.get("token")
    user_id = await get_user_id_from_websocket(websocket, token)
    async with get_async_db() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        current_user.set(user)
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
        current_user.set(user)
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
            data = await websocket.receive_json()
            
            data = data.get("message")
            
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
    
    if payload.post_type == 'quotes' and not payload.author:
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
 
 
@router.post("/linkedin-post")
def linked_post_generation(payload: LinkedInPostSchema,  db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    language = user.language
    prompt = linked_post_prompt_generation(payload.tone, payload.topic, payload.custom_instructions, language)
    generated_prompt, generated_content = text_content_generation(prompt)

    linkedin_post = LinkedInPost(**payload.model_dump(), generated_content=generated_content,
                                 prompt=generated_prompt, user=user_id)
    
    db.add(linkedin_post)
    db.commit()
    
    return JSONResponse(content={"success": "content generated successfully"}, status_code=201)

@router.get("/linkedin-post")
def get_linked_post(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    linkedin_posts = db.query(LinkedInPost).filter_by(user=user_id).all()
    
    response = []
    
    for linkedin_post in linkedin_posts:
        linkedin_post_data = {}
        linkedin_post_data['id'] = linkedin_post.id 
        linkedin_post_data['created_at'] = str(linkedin_post.created_at)
        linkedin_post_data['generated_content'] = linkedin_post.generated_content
        response.append(linkedin_post_data)
    return JSONResponse(content={"linkedin_posts": response}, status_code=200)

@router.patch("/linkedin-post/{post_id}")
def update_linked_post(post_id: int, payload: ContentUpdateSchema, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    linkedin_post = db.query(LinkedInPost).filter_by(id=post_id, user=user_id).first()
    
    if not linkedin_post:
        return JSONResponse(content={"error": "Post is not associated to you"}, status_code=404) 
    
    linkedin_post.generated_content = payload.content
    db.commit()    
    
    return JSONResponse(content={"success": "content updated successfully"}, status_code=200)

@router.post("/X-post")
def X_post_generation(payload: XPostSchema,  db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    language = user.language
    prompt = x_post_prompt_generator(payload.topic, payload.purpose, payload.custom_instructions, language)
    generated_prompt, generated_content = text_content_generation(prompt)

    x_post = XPost(**payload.model_dump(), generated_content=generated_content,
                                 prompt=generated_prompt, user=user_id)
    
    db.add(x_post)
    db.commit()
    
    return JSONResponse(content={"success": "content generated successfully"}, status_code=201)

@router.get("/X-post")
def get_x_post(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    x_posts = db.query(XPost).filter_by(user=user_id).all()
    
    response = []
    
    for x_post in x_posts:
        x_post_data = {}
        x_post_data['id'] = x_post.id 
        x_post_data['created_at'] = str(x_post.created_at)
        x_post_data['generated_content'] = x_post.generated_content
        response.append(x_post_data)
    return JSONResponse(content={"x_posts": response}, status_code=200)

@router.patch("/X-post/{post_id}")
def update_x_post(post_id: int, payload: ContentUpdateSchema, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    x_post = db.query(XPost).filter_by(id=post_id, user=user_id).first()
    
    if not x_post:
        return JSONResponse(content={"error": "Post is not associated to you"}, status_code=404) 
    
    x_post.generated_content = payload.content
    db.commit()    
    
    return JSONResponse(content={"success": "content updated successfully"}, status_code=200)


@router.post("/youtube-script-writer")
def youtube_script_generation(payload: YoutubeScriptSchema,  db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    language = user.language
    prompt = youtube_script_prompt_generator(payload.topic, payload.custom_instructions, language)
    generated_prompt, generated_content = text_content_generation(prompt)

    youtube_script = YoutubeScript(**payload.model_dump(), generated_content=generated_content,
                                 prompt=generated_prompt, user=user_id)
    
    db.add(youtube_script)
    db.commit()
    
    return JSONResponse(content={"success": "content generated successfully"}, status_code=201)

@router.get("/youtube-script-writer")
def get_youtube_script(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    youtube_scripts = db.query(YoutubeScript).filter_by(user=user_id).all()
    
    response = []
    
    for youtube_script in youtube_scripts:
        youtube_script_data = {}
        youtube_script_data['id'] = youtube_script.id 
        youtube_script_data['created_at'] = str(youtube_script.created_at)
        youtube_script_data['generated_content'] = youtube_script.generated_content
        response.append(youtube_script_data)
    return JSONResponse(content={"youtube_scripts": response}, status_code=200)

@router.patch("/youtube-script-writer/{post_id}")
def update_youtube_script(post_id: int, payload: ContentUpdateSchema, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    youtube_script = db.query(YoutubeScript).filter_by(id=post_id, user=user_id).first()
    
    if not youtube_script:
        return JSONResponse(content={"error": "Post is not associated to you"}, status_code=404) 
    
    youtube_script.generated_content = payload.content
    db.commit()    
    
    return JSONResponse(content={"success": "content updated successfully"}, status_code=200)


@router.post("/schedule-content/draft")
def schedule_content(text: str = Form(...),
                     document: Optional[UploadFile] = File(None),
                     platform: str = Form(...),
                     media_type: str = Form(...),
                     platform_unique_id: str = Form(...),
                     db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    if platform not in ('instagram', 'linkedin', 'X'):
        return JSONResponse(content={'error': "Platform not supported"}, status_code=400)
    
    if not platform_unique_id:
        return JSONResponse(content={'error': "account not selected"}, status_code=400)
    
    if platform=="instagram":
        if not document:
            return JSONResponse(content={'error': "image or video is madatory with instagram"}, status_code=400)
        if not document.filename.endswith((".jpeg", ".png", ".mp4")):
            return JSONResponse(content={'error': 'instagram does not support this media type'}, status_code=400)
        
    if platform == "linkedin":
        
        linkedin = db.query(LinkedIn).filter_by(linkedin_id=platform_unique_id).first()
        
        if not linkedin:
            return JSONResponse(content={'error': 'linkedin account not connected'}, status_code=400)
    
    try:
        file_path = ""
        if document:
            upload_args = get_upload_args(document.filename)
            
            file_path = f"content-document/{user.email}/{uuid.uuid4()}_{document.filename}"
            
            aws_client.upload_fileobj(Fileobj=document.file, 
                            Bucket=os.getenv('BUCKET_NAME'), Key=file_path,
                            ExtraArgs=upload_args)
    except Exception as e:
            print(e)
            return JSONResponse(content={"error": "could not upload document"}, status_code=500)
    
    content = ScheduledContent(text=text, document=file_path, platform=platform, platform_unique_id=platform_unique_id,
                               scheduled_type='draft', media_type=media_type, user_id=user_id) 
    db.add(content)
    db.commit()
    
    return JSONResponse(content={'success': "Content saved as draft"}, status_code=201)

@router.post("/schedule-content/publish")
def schedule_content(text: str = Form(...),
                     document: Optional[UploadFile] = File(None),
                     platform: str = Form(...),
                     media_type: str = Form(...),
                     platform_unique_id: str = Form(...),
                     db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    if platform not in ('instagram', 'linkedin', 'X'):
        return JSONResponse(content={'error': "Platform not supported"}, status_code=400)
    
    if not platform_unique_id:
        return JSONResponse(content={'error': "account not selected"}, status_code=400)
    
    if platform=="instagram":
        if not document:
            return JSONResponse(content={'error': "image or video is mandatory with instagram"}, status_code=400)
        if not document.filename.endswith((".jpeg", ".png", ".mp4")):
            return JSONResponse(content={'error': 'instagram does not support this media type'}, status_code=400)
    
    try:
        file_path = ""
        media_url = ""
        
        if document:
            upload_args = get_upload_args(document.filename)
        
            file_path = f"content-document/{user.email}/{uuid.uuid4()}_{document.filename}"
        
            aws_client.upload_fileobj(Fileobj=document.file, 
                        Bucket=os.getenv('BUCKET_NAME'), Key=file_path,
                        ExtraArgs=upload_args)
            
            media_url = os.getenv("S3_BASE_URL") + f"/{file_path}"
    except Exception as e:
            print(e)
            return JSONResponse(content={"error": "could not upload document"}, status_code=500)
        
    if platform == "instagram":
        
        instagram = db.query(Instagram).filter_by(instagram_user_id=platform_unique_id).first()
        
        if not instagram:
            return JSONResponse(content={'error': 'instagram account not connected'}, status_code=400)
        
        media_id = publish_content_instagram(instagram.access_token, instagram.refresh_token, platform_unique_id, media_type, media_url, text)
    
    if platform == "linkedin":
        
        linkedin = db.query(LinkedIn).filter_by(linkedin_id=platform_unique_id).first()
        
        if not linkedin:
            return JSONResponse(content={'error': 'linkedin account not connected'}, status_code=400)
        
        if media_url:
            response, status_code = publish_content_linkedin(linkedin.access_token, linkedin.linkedin_id, text, media_type, media_url)
        else:
            response, status_code = publish_content_linkedin(linkedin.access_token, linkedin.linkedin_id, text, media_type)
        
        if status_code != 201:
            return JSONResponse(content={"error": "could not publish"}, status_code=400)

        media_id = response.get("x-restli-id")
        
    published_time = datetime.datetime.now(timezone.utc)
    
    content = ScheduledContent(text=text, document=file_path, platform=platform, platform_unique_id=platform_unique_id,
                               scheduled_type='publish', media_id=media_id, media_type=media_type,
                               published_time=published_time, user_id=user_id)
    db.add(content)
    db.commit()
    
    return JSONResponse(content={'success': "Content published"}, status_code=201)

@router.post("/schedule-content/scheduled")
def schedule_content(text: str = Form(...),
                     document: Optional[UploadFile] = File(None),
                     platform: str = Form(...),
                     platform_unique_id: str = Form(...),
                     media_type: str = Form(...),
                     scheduled_date: date = Form(...),
                     scheduled_time: time = Form(...),
                     db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    if platform not in ('instagram', 'linkedin', 'X'):
        return JSONResponse(content={'error': "Platform not supported"}, status_code=400)
    
    if not platform_unique_id:
        return JSONResponse(content={'error': "account not selected"}, status_code=400)
    
    if platform == "instagram":
        if not document:
            return JSONResponse(content={'error': "image or video is mandatory with instagram"}, status_code=400)
        if not document.filename.endswith((".jpeg", ".png", ".mp4")):
            return JSONResponse(content={'error': 'instagram does not support this media type'}, status_code=400)
        
        instagram = db.query(Instagram).filter_by(instagram_user_id=platform_unique_id).first()
        
        if not instagram:
            return JSONResponse(content={'error': 'instagram account not connected'}, status_code=404)
    
    if platform == "linkedin":
        linkedin = db.query(LinkedIn).filter_by(linkedin_id=platform_unique_id).first()
        
        if not linkedin:
            return JSONResponse(content={'error': 'linkedin account not connected'}, status_code=400)
    
    try:
        file_path = ""
        if document:
            upload_args = get_upload_args(document.filename)
            file_path = f"content-document/{user.email}/{uuid.uuid4()}_{document.filename}"
            aws_client.upload_fileobj(Fileobj=document.file, 
                            Bucket=os.getenv('BUCKET_NAME'), Key=file_path,
                            ExtraArgs=upload_args)
    except Exception as e:
            print(e)
            return JSONResponse(content={"error": "could not upload document"}, status_code=500)
    
    content = ScheduledContent(text=text, document=file_path, platform=platform, platform_unique_id=platform_unique_id,
                               scheduled_type='schedule',scheduled_date=scheduled_date,
                               scheduled_time=scheduled_time, media_type=media_type, user_id=user_id)
    db.add(content)
    db.commit()
    
    return JSONResponse(content={'success': "Content is scheduled"}, status_code=201)
    
@router.get("/get-scheduled-content")
def get_scheduled_content(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    scheduled_contents = db.query(ScheduledContent).filter_by(user_id=user_id).all()
    
    response = []
    
    for content in scheduled_contents:
        content_detail = {}
        content_detail['scheduled_content_id'] = content.id
        content_detail['platform'] = content.platform
        content_detail['platform_unique_id'] = content.platform_unique_id
        content_detail['scheduled_type'] = content.scheduled_type
        content_detail['scheduled_date'] = str(content.scheduled_date)
        content_detail['scheduled_time'] = str(content.scheduled_time)
        content_detail['published_time'] = str(content.published_time)
        response.append(content_detail)
    return JSONResponse(content={"content_details": response}, status_code=200)        
    
