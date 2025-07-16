
import requests, os, datetime, uuid
from fastapi import Depends, Query
from fastapi.routing import APIRouter
from fastapi.responses import PlainTextResponse, JSONResponse, RedirectResponse

from sqlalchemy.orm import Session

from app.models.get_db import get_db
from app.models.model import User
from app.models.appointment_setter import (AppointmentSetter, AppointmentAgentLeads,
                                           LeadAnalytics)
from app.models.social_media_integrations import Instagram
from app.schemas.social_media_integration import (InstagramCallback,
                                                InstagramMessageAlert)
from app.utils.instagram import (user_authorization, long_lived_access_token, instagram_user_info,
                                instagram_send_message, image_to_text, instagram_message_invalid_type)
from app.utils.user_auth import get_current_user
from app.ai_agents.prompts import Prompts
from app.ai_agents.appointment_setter import initialise_agent, message_reply_by_agent
from app.utils.knowledge_base import fetch_text

router = APIRouter(tags=["instagram"])

@router.get("/instagram/webhook")
def instagram_verify_webhook(mode: str = Query(..., alias="hub.mode"),
    verify_token: str = Query(..., alias="hub.verify_token"),
    challenge: str = Query(..., alias="hub.challenge")):
    
    if verify_token == "token":
        return PlainTextResponse(content=challenge, status_code=200)
    else:
        return JSONResponse(content={"error": "You are not authorized to access the url."}, status_code=403)
    
@router.get("/auth/instagram/callback")
def instagram_callback_url(request: InstagramCallback = Depends(), db: Session = Depends(get_db)):
    code = request.code
    state = request.state
    
    try:
        user_id = int(state)
    except:
        return JSONResponse(content={"error": "wrong creds"}, status_code=400)

    if not code:
        return JSONResponse(content={"error": "Missing code from Instagram"}, status_code=400)
    
    token_response, status = user_authorization(code)
        
    if status != 200:
        return RedirectResponse(url="https://www.app.ecosysteme.ai/dashboard/brain", status_code=303)
    
    short_lived_access_token = token_response.get("access_token")

    response, status = long_lived_access_token(short_lived_access_token)
    
    if status != 200:
        return RedirectResponse(url="https://www.app.ecosysteme.ai/dashboard/brain", status_code=303)

    access_token = response.get("access_token")
    expiry_time = response.get("expires_in")    
    
    time_delta = datetime.timedelta(seconds=expiry_time)
    
    expiry_time = datetime.datetime.now(datetime.timezone.utc) + time_delta
    
    user_response, status = instagram_user_info(access_token)
    
    if status != 200:
        return RedirectResponse(url="https://www.app.ecosysteme.ai/dashboard/brain", status_code=303)
    
    instagram_user_id = user_response['user_id']
    instagram_id = user_response['id']
    username = user_response['username']
    name = user_response['name']
    
    instagram_user = db.query(Instagram).filter_by(instagram_user_id=instagram_user_id).first()
    
    if instagram_user:
        return RedirectResponse(url="https://www.app.ecosysteme.ai/dashboard/brain", status_code=303)
    
    instagram_user = Instagram(instagram_user_id=instagram_user_id, instagram_id=instagram_id, username=username, name=name,
                            expiry_time=expiry_time, access_token=access_token, user_id=user_id)
    db.add(instagram_user)
    db.commit()
    return RedirectResponse(url="https://www.app.ecosysteme.ai/dashboard/brain", status_code=303)

@router.post("/instagram/webhook")
def instagram_message_webhook(request: InstagramMessageAlert, db: Session = Depends(get_db)):
    print(request.entry)
    payload = request.entry
    payload = payload[0]
    id = payload['id']
    description = payload['messaging']
    message_info = description[0]
    sender_id = message_info["sender"]["id"]
    recipient_id = message_info["recipient"]["id"]
    
    if id == sender_id:
        return JSONResponse({"sucess": ""}, status_code=200)
    
    instagram_user = db.query(Instagram).filter_by(instagram_user_id=recipient_id).first()
    
    if not instagram_user:
        return ""
    
    message = message_info["message"]
    text = message.get("text")
    
    if not text:
        attachments = message.get("attachments")
        if attachments is None:
            return ("")
        attachments = attachments[0]
        if attachments.get("type") == 'image':
            text = image_to_text(attachments['payload']['url'])
        else:
            instagram_message_invalid_type(instagram_user.access_token, sender_id)
        
    agent = db.query(AppointmentSetter).filter_by(platform_unique_id=recipient_id).first()
    
    if not agent:
        return JSONResponse(content={'error': 'Not authorized to talk this agent'}, status_code=404)
    
    lead = db.query(AppointmentAgentLeads).filter_by(lead_id=sender_id).first()
    
    if not lead:
        lead = AppointmentAgentLeads(lead_id=sender_id)
        db.add(lead)
        db.commit()
        db.refresh(lead)
    
    agent_id = agent.id
    lead_chat = db.query(LeadAnalytics).filter_by(lead_id=lead.id, agent_id=agent_id).first()
    chat_history = {}
    chat_history['user'] = text
    if not lead_chat:
        thread_id = uuid.uuid4()
        lead_chat = LeadAnalytics(lead_id=lead.id, agent_id=agent_id, thread_id=thread_id, platform_unique_id=instagram_user.instagram_user_id)
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

    access_token = instagram_user.access_token
    instagram_send_message(access_token, sender_id, response)
    return JSONResponse({"sucess": ""}, status_code=200)

@router.get("/get-insta-accounts")
def get_connected_insta_accounts(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)

    accounts = db.query(Instagram).filter_by(user_id=user_id).all()
    account_info = []
    for account in accounts:
        insta_account_detail = {}
        insta_account_detail['username'] = account.username
        insta_account_detail['instagram_user_id'] = account.instagram_user_id
        account_info.append(insta_account_detail)
    return JSONResponse(content={"insta_account_info": account_info}, status_code=200)

@router.delete("/delete-insta-account/{instagram_id}")
def delete_connected_insta_accounts(instagram_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    
    agent = db.query(AppointmentSetter).filter_by(platform_unique_id=instagram_id).first()
    if agent:
        return JSONResponse(content={"success": f"""The id is linked with {agent.agent_name}.
                                     Either delete agent or relink with another account."""}, status_code=400)

    account = db.query(Instagram).filter_by(instagram_user_id=instagram_id, user_id=user_id).first()
    if not account:
        return JSONResponse(content={"success": "Not authorized to delete the account"}, status_code=403)
    db.delete(account)
    db.commit()
    return JSONResponse(content={"success": "account deleted successfully"}, status_code=200)
        

