import os
import uuid, datetime

from fastapi import WebSocket, Depends, File, UploadFile, Form
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from pydantic import BaseModel
from app.models.get_db import get_async_db, get_db
from app.models.model import User
from app.models.customer_support import (CustomerSupportChatHistory, SmartAgentIntegration,
                                         SmartCustomerSupportAgent, SmartBotAvatars)
from app.schemas.customer_support import (CreateSmartBotSchema, CreateWebsiteLinkSchema, 
                                          UpdateSmartBotSchema, UpdateWebsiteLinkSchema,
                                          Message)
from app.prompts.customer_support import (customer_support_agent, generate_faq,
                                          user_guide_generator, email_responder_agent,
                                          smartbot)
from app.utils.user_auth import get_user_id_from_websocket, get_current_user
from app.ai_agents.customer_support import initialise_agent, message_reply_by_agent
from app.services.babel import get_translator_dependency
from app.services.aws_boto3 import aws_client, get_upload_args
from app.utils.chatbots import summarizing_initial_chat

router = APIRouter(tags=["customer-support-agent"])

class NameUpdate(BaseModel):
    name: str

@router.websocket("/customer-support-agent/{id}")
async def customer_support_agent_chat(id: int, websocket: WebSocket):
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
                chat = await db.get(CustomerSupportChatHistory, id)
                if not chat:
                    await websocket.send_json({"error": "This conversation does not exist"})
                    await websocket.close()
                    return
    
                thread_id = chat.thread_id
                agent_type = chat.agent_type
                
                if not agent_type:
                    prompt = customer_support_agent(language)
                else:
                    if agent_type == "faq_generator":
                        prompt = generate_faq(language)
                    elif agent_type == "user_guide":
                        prompt = user_guide_generator(language)
                    elif agent_type == "email_responder":
                        prompt = email_responder_agent(language)
                    else:
                        prompt = customer_support_agent(language)
                customer_agent = await initialise_agent(prompt)
                ai_response = await message_reply_by_agent(customer_agent, data, thread_id)

                async with get_async_db() as db:
                    chat = await db.get(CustomerSupportChatHistory, id)
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

            
@router.websocket("/new-customer-support-agent-chat")
async def new_customer_agent_agent_chat(websocket: WebSocket):
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
        chat = CustomerSupportChatHistory(thread_id=str(thread_id), name="Customer Support Agent Chat", user_id=user_id, chat_history=[])
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        chat_id = chat.id
        
    while True:
        try:
            data = await websocket.receive_json()
            
            agent_type = "jgjgh"
            data = data.get("message")
            
            chat_name = await summarizing_initial_chat(data)

            async with get_async_db() as db:
                chat = await db.get(CustomerSupportChatHistory, chat_id)
                chat_history = chat.chat_history
                chat_history.append({'user': data, 'message_at': str(datetime.datetime.now(datetime.timezone.utc))})
                chat.chat_history = chat_history
                chat.name = chat_name
                if agent_type:
                    chat.agent_type = agent_type
                await db.commit()

                if not agent_type:
                    prompt = customer_support_agent(language)
                else:
                    if agent_type == "faq_generator":
                        prompt = generate_faq(language)
                    elif agent_type == "user_guide":
                        prompt = user_guide_generator(language)
                    elif agent_type == "email_responder":
                        prompt = email_responder_agent(language)
                    else:
                        prompt = customer_support_agent(language)
                        
                customer_agent = await initialise_agent(prompt)
                ai_response = await message_reply_by_agent(customer_agent, data, thread_id)

                async with get_async_db() as db:
                    chat = await db.get(CustomerSupportChatHistory, chat_id)
                    chat_history = chat.chat_history
                    time_now = datetime.datetime.now(datetime.timezone.utc)
                    chat_history.append({'agent': ai_response, 'message_at': str(time_now)})
                    chat.chat_history = chat_history
                    await db.commit()

            await websocket.send_json({'agent': ai_response})

        except Exception:
            await websocket.close()
            break
        

@router.get("/get-customer-support-chats")
def get_customer_support_chats(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)
                  , _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)

    chats = db.query(CustomerSupportChatHistory).filter_by(user_id=user_id).all()

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

@router.get("/get-customer-support-chat/{chat_id}")
def get_customer_support_chat_history(chat_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user),
                         _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    chat = db.query(CustomerSupportChatHistory).filter_by(id=chat_id).first()
    
    if not chat:
        return JSONResponse(content={'error': 'Chat does not exist'}, status_code=404)
            
    return JSONResponse(content={'success': chat.chat_history}, status_code=200)
        
        
@router.patch("/update-customer-support-chat-name/{chat_id}")
def update_customer_support_chat_name(chat_id, payload: NameUpdate, db: Session = Depends(get_db),
                         user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    chat = db.query(CustomerSupportChatHistory).filter_by(id=chat_id).first()
    
    if not chat:
        return JSONResponse(content={'error': _('Chat does not exist')}, status_code=404)
    
    chat.name = payload.name
    db.commit()
            
    return JSONResponse(content={'success': _("name updated successfully")}, status_code=200)

@router.delete("/delete-customer-support-chat/{chat_id}")
def delete_customer_support_chat(chat_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user),
                    _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    chat = db.query(CustomerSupportChatHistory).filter_by(id=chat_id).first()
    
    if not chat:
        return JSONResponse(content={'error': _('Chat does not exist')}, status_code=404)
    
    db.delete(chat)
    db.commit()
            
    return JSONResponse(content={'success': _("chat deleted successfully")}, status_code=200)

@router.post("/create-smartbot")
def create_smartbot(
    payload: CreateSmartBotSchema,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
    _ = Depends(get_translator_dependency)):
    
    new_smart_chatbot_agent = SmartCustomerSupportAgent(id=str(uuid.uuid4()), **payload.model_dump(), user_id=user_id)
    db.add(new_smart_chatbot_agent)
    db.commit()
    
    return JSONResponse(content={"agent_id": new_smart_chatbot_agent.id}, status_code=201)

@router.post("/link-smartbot")
def link_smartbot(
    payload: CreateWebsiteLinkSchema,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
    _ = Depends(get_translator_dependency)):
    
    agent = db.query(SmartCustomerSupportAgent).filter_by(id=payload.agent_id).first()
    
    if not agent:
        return JSONResponse(content={"error": "smart chatbot does not exist"}, status_code=404)
    
    linked_website = db.query(SmartAgentIntegration).filter_by(agent_id=payload.agent_id).first()
    
    if linked_website:
        return JSONResponse(content={"error": "smart chatbot already linked"}, status_code=404)
        
    
    linked_website_instance = SmartAgentIntegration(**payload.model_dump())
    db.add(linked_website_instance)
    db.commit()
    
    return JSONResponse(content={"sucess": "Bot linked to a website."}, status_code=201)

@router.post('/add-avatar')
def add_avatar(
    avatar_name: str = Form(None),
    avatar_image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
    _ = Depends(get_translator_dependency)):
    
    # if not avatar_image.filename.endswith(".jpeg"):
    #     return JSONResponse(content={"sucess": "file extension should be jpeg, png."}, status_code=422)
    
    file_path = f"/customer_support/{user_id}/{avatar_name}"
    
    avatar = db.query(SmartBotAvatars).filter_by(avatar_url=file_path, user_id=user_id).first()
    
    if avatar:
        return JSONResponse(content={"sucess": "image is already uploaded"}, status_code=409)
        
    extra_args = get_upload_args(avatar_image.filename)
        
    try:
        aws_client.upload_fileobj(Fileobj=avatar_image.file, 
                    Bucket=os.getenv('BUCKET_NAME'), Key=file_path,
                    ExtraArgs=extra_args)
    except Exception as e:
        print(e)
        return JSONResponse(content={"error": "could not upload document"}, status_code=500)
        
    avatar_url = os.getenv("S3_BASE_URL") + file_path
    
    new_avatar = SmartBotAvatars(avatar_name=avatar_name, avatar_url=avatar_url, user_id=user_id)
    db.add(new_avatar)
    db.commit()
    return JSONResponse(content={"success": "new avatar added"}, status_code=201)

@router.put("/smartbot/{agent_id}")
def update_smartbot(
    agent_id,
    payload: UpdateSmartBotSchema,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
    _ = Depends(get_translator_dependency)):
    
    agent = db.query(SmartCustomerSupportAgent).filter_by(id=agent_id).first()
    
    if not agent:
        return JSONResponse(content={"error": "agent does not exist"}, status_code=404)
    
    data = payload.model_dump(exclude_unset=True)
    
    for key, value in data.items():
        setattr(agent, key, value)
        db.commit()
    
    return JSONResponse(content={"success": "Agent updated successfully"}, status_code=200)
        
@router.put("/update-link/{agent_id}")
def update_webiste_link(
    agent_id,
    payload: UpdateWebsiteLinkSchema,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
    _ = Depends(get_translator_dependency)):
    
    agent = db.query(SmartAgentIntegration).filter_by(agent_id=agent_id).first()
    
    if not agent:
        return JSONResponse(content={"error": "agent does not exist"}, status_code=404)
    
    data = payload.model_dump(exclude_unset=True)
    
    for key, value in data.items():
        setattr(agent, key, value)
        db.commit()
    
    return JSONResponse(content={"success": "Session updated successfully"}, status_code=200)
    
@router.get("/get-avatars")
def get_avatars(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
    _ = Depends(get_translator_dependency)):
    
    avatars = db.query(SmartBotAvatars).filter_by(user_id=user_id).all()
    
    response = []
    for avatar in avatars:
        avatar_info = {}
        avatar_info["avatar_name"] = avatar.avatar_name
        avatar_info["avatar_url"] = avatar.avatar_url
        avatar_info["id"] = avatar.id
        response.append(avatar_info)
    
    return JSONResponse(content={"success": response}, status_code=200)

@router.get("/get-smartbot/{agent_id}")
def get_smartbot_info(
    agent_id,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
    _ = Depends(get_translator_dependency)):
    
    bot = db.query(SmartCustomerSupportAgent).filter_by(id=agent_id).first()
    
    if not bot:
        return JSONResponse(content={"error": "bot does not exist"}, status_code=404)

    bot_info = {}
    bot_info["bot_name"] = bot.bot_name
    bot_info["personality"] = bot.personality
    bot_info["role"] = bot.role
    bot_info["prompt"] = bot.prompt
    bot_info["reference_text"] = bot.reference_text
    bot_info["reference_file"] = bot.reference_file
    bot_info["transfer_case"] = bot.transfer_case

    return JSONResponse(content={"success": bot_info}, status_code=200)

@router.get("/get-smartbots")
def get_smartbots(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
    _ = Depends(get_translator_dependency)):
    
    bots = db.query(SmartCustomerSupportAgent).filter_by(user_id=user_id).all()
    
    response = []
    for bot in bots:
        bot_info = {}
        bot_info["id"] = bot.id
        bot_info["bot_name"] = bot.bot_name
        bot_info["chats"] = 10
        response.append(bot_info)
    
    return JSONResponse(content={"success": response}, status_code=200)

@router.get("/get-website/{agent_id}")
def get_smartbot_info(
    agent_id,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
    _ = Depends(get_translator_dependency)):
    
    link = db.query(SmartAgentIntegration).filter_by(agent_id=agent_id).first()
    
    if not link:
        return JSONResponse(content={"error": "link does not exist"}, status_code=404)

    link_info = {}
    link_info["id"] = link.id
    link_info["agent_name"] = link.agent_name
    link_info["colour"] = link.colour
    link_info["domain"] = link.domain
    link_info["first_message"] = link.first_message
    link_info["selected_avatar_url"] = link.selected_avatar_url

    return JSONResponse(content={"success": link_info}, status_code=200)

@router.delete("/delete-smartbot/{agent_id}")
def delete_smartbot(agent_id,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
    _ = Depends(get_translator_dependency)):
    
    link = db.query(SmartAgentIntegration).filter_by(agent_id=agent_id).first()
    
    if link:
        db.delete(link)
        db.commit()
    
    bot = db.query(SmartCustomerSupportAgent).filter_by(id=agent_id).first()
    if not bot:
        return JSONResponse(content={"error": "bot does not exist"}, status_code=404)
    
    db.delete(bot)
    db.commit()
    
    return JSONResponse(content={"success": "bot deleted successfully"}, status_code=200)
    
@router.post("/test-chat/{agent_id}")
def test_chat(
    agent_id,
    payload: Message,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
    _ = Depends(get_translator_dependency)):
    
    message = payload.message
    thread_id = payload.thread_id
    
    bot = db.query(SmartCustomerSupportAgent).filter_by(id=agent_id).first()
    if not bot:
        return JSONResponse(content={"error": "bot does not exist"}, status_code=404)
    
    link = db.query(SmartAgentIntegration).filter_by(agent_id=agent_id).first()
    if not link:
        return JSONResponse(content={"error": "bot integration does not exist"}, status_code=404)
    
    prompt = smartbot(bot, link)
    
    test_agent = initialise_agent(prompt)
    ai_response = message_reply_by_agent(test_agent, message, thread_id)
    
    return JSONResponse(content={"success": ai_response}, status_code=200)

@router.post("/smartbot/{session_id}")
def smartbot_chat(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
    _ = Depends(get_translator_dependency)):
    
    print("fghjkl")