
import requests, os, datetime, uuid
import redis
from fastapi import Depends, Query, Request
from fastapi.routing import APIRouter
from fastapi.responses import PlainTextResponse, JSONResponse, RedirectResponse

from sqlalchemy.orm import Session

from app.models.get_db import get_db
from app.models.model import User
from app.models.appointment_setter import (AppointmentSetter, AppointmentAgentLeads,
                                           LeadAnalytics)
from app.models.social_media_integrations import Whatsapp
from app.schemas.social_media_integration import (FacebookCallback,
                                                InstagramMessageAlert)
from app.utils.whatsapp import (generate_short_lived_access_token, long_lived_access_token,
                                get_phone_number, whatsapp_send_messages, get_image_url, image_to_text,
                                invalid_whatsapp_send_messages)
from app.utils.user_auth import get_current_user
from app.ai_agents.prompts import Prompts
from app.ai_agents.appointment_setter import initialise_agent, message_reply_by_agent
from app.utils.knowledge_base import fetch_text

router = APIRouter(tags=["whatsapp"])

@router.get("/whatsapp/webhook")
def whatsapp_verify_webhook(mode: str = Query(..., alias="hub.mode"),
    verify_token: str = Query(..., alias="hub.verify_token"),
    challenge: str = Query(..., alias="hub.challenge")):
    
    if verify_token == "token":
        return PlainTextResponse(content=challenge, status_code=200)
    else:
        return JSONResponse(content={"error": "You are not authorized to access the url."}, status_code=403)
    
@router.get("/auth/facebook/callback")
def facebook_callback_url(request: FacebookCallback = Depends(), db: Session = Depends(get_db)):
    code = request.code
    state = request.state
    
    try:
        user_id = int(state)
    except:
        return JSONResponse(content={"error": "wrong creds"}, status_code=400)

    if not code:
        return JSONResponse(content={"error": "Missing code from Whatsapp"}, status_code=400)
    
    response, status = generate_short_lived_access_token(code)
    
    if status != 200:
        return RedirectResponse(url="https://www.app.ecosysteme.ai/dashboard/brain", status_code=303)
    
    short_lived_access_token = response.get('access_token')
    
    response, status = long_lived_access_token(short_lived_access_token)
    
    access_token = response.get('access_token')
    expiry_time = response.get('expires_in')
    
    if status != 200:
        return RedirectResponse(url="https://www.app.ecosysteme.ai/dashboard/brain", status_code=303)
    
    time_delta = datetime.timedelta(seconds=expiry_time)
    
    expiry_time = datetime.datetime.now(datetime.timezone.utc) + time_delta
    
    data, whatsapp_business_id = get_phone_number(access_token)
    
    phone_number = data.get('display_phone_number')
    name = data.get('verified_name')
    phone_id = data.get('id')

    whatsapp_number = db.query(Whatsapp).filter_by(whatsapp_phone_id=phone_id).first()
    
    if whatsapp_number:
        return RedirectResponse(url="https://www.app.ecosysteme.ai/dashboard/brain", status_code=303)
    
    whatsapp_number = Whatsapp(whatsapp_business_id=whatsapp_business_id, whatsapp_phone_id=phone_id, name=name, phone_number=phone_number,
                            expiry_time=expiry_time, access_token=access_token, user_id=user_id)
    db.add(whatsapp_number)
    db.commit()
    return RedirectResponse(url="https://www.app.ecosysteme.ai/dashboard/brain", status_code=303)

@router.post("/whatsapp/webhook")
def whatsapp_message_webhook(request: InstagramMessageAlert, db: Session = Depends(get_db)):
    payload = request.entry
    
    
    payload = payload[0]
    agent_number = payload['changes']
    agent_number = agent_number[0]
    phone_id = agent_number['value']['metadata']['phone_number_id']
    
    whatsapp_number = db.query(Whatsapp).filter_by(whatsapp_phone_id=phone_id).first()
    
    if not whatsapp_number:
        return ""
    
    access_token = whatsapp_number.access_token
    status_check = agent_number['value']
    if status_check.get('statuses'):
        return ""
    messages = agent_number['value']['messages']
    messages = messages[0]
    lead_id = messages.get('from')
    message_type = messages.get('type')
    if message_type == "text":
        text =  messages['text']['body']
    elif message_type == 'image':
        image_id = messages['image']['id']
        encoded_image = get_image_url(image_id, access_token)
        response = image_to_text(encoded_image)
    else:
        invalid_whatsapp_send_messages(access_token, phone_id, lead_id)
        
    agent = db.query(AppointmentSetter).filter_by(platform_unique_id=phone_id).first()
    
    if not agent:
        return JSONResponse(content={'error': 'Not authorized to talk this agent'}, status_code=404)
    
    lead = db.query(AppointmentAgentLeads).filter_by(lead_id=lead_id).first()
    
    if not lead:
        lead = AppointmentAgentLeads(lead_id=lead_id)
        db.add(lead)
        db.commit()
        db.refresh(lead)
    
    agent_id = agent.id
    lead_chat = db.query(LeadAnalytics).filter_by(lead_id=lead.id, agent_id=agent_id).first()
    chat_history = {}
    chat_history['user'] = text
    if not lead_chat:
        thread_id = uuid.uuid4()
        lead_chat = LeadAnalytics(lead_id=lead.id, agent_id=agent_id, thread_id=thread_id, platform_unique_id=whatsapp_number.whatsapp_phone_id)
        db.add(lead_chat)
        db.commit()
        
    if lead_chat:
        thread_id = lead_chat.thread_id
        db.commit()
    chat = lead_chat.chat_history
    chat.append(chat_history)
    lead_chat.chat_history = chat
    db.commit()
    
    if lead_chat.agent_is_enabled == False:
        return JSONResponse({"sucess": ""}, status_code=200)
    
    knowledge_base = fetch_text(text, agent.user_id)
    prompt = Prompts.appointment_setter_prompt(agent, knowledge_base)
    appointment_agent = initialise_agent(prompt)
    ai_message = message_reply_by_agent(appointment_agent, text, thread_id)
    
    response = ai_message.get('response')
    chat_history = {}
    chat_history['agent'] = response
    chat = lead_chat.chat_history
    lead_chat.status = ai_message.get('lead_qualification_status')
    chat.append(chat_history)
    lead_chat.chat_history = chat
    lead_chat.updated_at = datetime.date.today()
    db.commit()

    access_token = whatsapp_number.access_token
    whatsapp_send_messages(access_token, phone_id, lead_id, response)
    return JSONResponse({"sucess": ""}, status_code=200)


@router.get("/get-whatsapp-accounts")
def get_connected_whatsapp_accounts(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)

    accounts = db.query(Whatsapp).filter_by(user_id=user_id).all()
    account_info = []
    for account in accounts:
        whatsapp_account_detail = {}
        whatsapp_account_detail['username'] = account.phone_number
        whatsapp_account_detail['whatsapp_phone_id'] = account.whatsapp_phone_id
        account_info.append(whatsapp_account_detail)
    return JSONResponse(content={"whatsapp_account_info": account_info}, status_code=200)

@router.delete("/delete-whatsapp-account/{whatsapp_id}")
def delete_connected_whatsapp_accounts(whatsapp_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    agent = db.query(AppointmentSetter).filter_by(platform_unique_id=whatsapp_id).first()
    if agent:
        return JSONResponse(content={"success": f"""The id is linked with {agent.agent_name}.
                                     Either delete agent or relink with another account."""}, status_code=400)

    account = db.query(Whatsapp).filter_by(whatsapp_phone_id=whatsapp_id, user_id=user_id).first()
    if not account:
        return JSONResponse(content={"success": "Not authorized to delete the account"}, status_code=403)
    db.delete(account)
    db.commit()
    return JSONResponse(content={"success": "account deleted successfully"}, status_code=200)

@router.get("/test-redis")
def test_redis_connection():
    redis_url = os.getenv("REDIS_BROKER_URL")
    try:
        r = redis.Redis.from_url(redis_url, socket_connect_timeout=3)
        pong = r.ping()
        if pong:
            return {"status": "success", "message": "PONG"}
        else:
            return {"status": "error", "message": "No PONG received"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

