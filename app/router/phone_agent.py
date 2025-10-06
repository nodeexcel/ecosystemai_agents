import base64, json, os, uuid, asyncio
from datetime import datetime, timezone
import websockets
from fastapi import Depends, HTTPException, WebSocket, Form
from fastapi.websockets import WebSocketDisconnect
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse, HTMLResponse

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.get_db import get_async_db

from twilio.twiml.voice_response import VoiceResponse, Connect

from app.models.model import User
from app.models.phone_agent import PhoneAgent, PhoneCampaign, AgentPhoneNumbers, CallRecord
from app.models.get_db import get_db, SessionLocal
from app.prompts.phone_agent import phone_agent_prompt
from app.schemas.phone_agent import (AddPhoneNumber, CreatePhoneAgent,
                                     AddCampaigns, AgentFilterParams, UpdateCampaign)
from app.utils.user_auth import get_current_user
from app.services.babel import get_translator_dependency
from app.services.twilio_rest import twilio_client, outgoing_buy_number, incoming_buy_number
from app.utils.phone_agent import initialize_session
from app.utils.knowledge_base import fetch_text

router = APIRouter(tags=["phone-agents"])

LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated', 'response.done',
    'input_audio_buffer.committed', 'input_audio_buffer.speech_stopped',
    'input_audio_buffer.speech_started', 'session.created'
]

@router.post("/add-phone-number")
def add_phone_number(payload: AddPhoneNumber, db: Session = Depends(get_db),
                     user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    """This endpoint is used to add a verified phone number."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    allowed_countries = {'United States': '+1', 'France': '+33', 'United Kingdom': '+44'}
    
    if payload.country not in allowed_countries:
         return JSONResponse(content={'error': ("country code provided does not exist")}, status_code=409)
     
    country_code = allowed_countries[payload.country]
    
    payload.phone_number = country_code + payload.phone_number
    
    phone_number = db.query(AgentPhoneNumbers).filter_by(phone_number=payload.phone_number).first()
    if phone_number:
        return JSONResponse(content={'error': _("phone number is already added")}, status_code=409)
    
    if payload.number_type == "outbound":
    
        twilio_number = outgoing_buy_number() 
    
    if payload.number_type == "inbound":
    
        twilio_number = incoming_buy_number() 
        
    add_phone_number = AgentPhoneNumbers(**payload.model_dump(), twilio_number=twilio_number,
                                         created_at = datetime.now(timezone.utc), user_id=user_id)
    db.add(add_phone_number)
    db.commit()
    db.refresh(add_phone_number)
    return JSONResponse(content={'success': _("Phone Number added to the list")}, status_code=201)

@router.post("/create-phone-agent")
def create_phone_agent(payload: CreatePhoneAgent, db: Session = Depends(get_db),
                       user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    """This endpoint is used to create a phone agent."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    phone_number = db.query(AgentPhoneNumbers).filter_by(phone_number=payload.phone_number).first()
    if not phone_number:
        return JSONResponse(content={'error': _("phone number does not exists")}, status_code=404)
    print(payload.phone_number)
    phone_number = db.query(PhoneAgent).filter_by(phone_number=payload.phone_number).first()
    if phone_number:
        return JSONResponse(content={'error': ("phone number already associated with a agent")}, status_code=404)
        
    add_agent = PhoneAgent(**payload.model_dump(), user_id=user_id)
    db.add(add_agent)
    db.commit()
    db.refresh(add_agent)
    return JSONResponse(content={'success': _("The phone agent is created successfully")}, status_code=201)

@router.post("/create-phone-campaign")
def create_phone_campaign(payload: AddCampaigns, db: Session = Depends(get_db),
                          user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    """This endpoint is used to create a phone agent campiagn."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    phone_number = db.query(AgentPhoneNumbers).filter_by(phone_number=payload.phone_number).first()
    if not phone_number:
        return JSONResponse(content={'error': _("phone number does not exists")}, status_code=404)
    
    phone_agent = db.query(PhoneAgent).filter_by(id=payload.agent).first()
    if not phone_agent:
        return JSONResponse(content={'error': _("agent does not exists")}, status_code=404)
    
    phone_agent = db.query(PhoneCampaign).filter_by(agent=payload.agent).first()
    if phone_agent:
        return JSONResponse(content={'error': _("agent already connected to another campaign")}, status_code=404)
        
    add_campaign = PhoneCampaign(**payload.model_dump(), user_id=user_id)
    db.add(add_campaign)
    db.commit()
    db.refresh(add_campaign)
    return JSONResponse(content={'success': _("The phone agent is created successfully")}, status_code=201)

@router.get("/get-phone-numbers")
def get_phone_numbers(db: Session = Depends(get_db), user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    phone_numbers = db.query(AgentPhoneNumbers).filter_by(user_id=user_id).all()
    if not phone_numbers:
        return JSONResponse(content={'error': _("No Phone Numbers are added")}, status_code=404)
    
    numbers_info = []
    
    for phone_number in phone_numbers:
        number_data = {}
        number_data['id'] = phone_number.id
        number_data['phone_number'] = phone_number.phone_number
        number_data['country'] = phone_number.country
        number_data['status'] = phone_number.status
        number_data['total_calls'] = 0
        number_data['direction'] = phone_number.number_type
        number_data['creation_date'] = str(phone_number.created_at)
        numbers_info.append(number_data)
        
    return JSONResponse(content={'phone_numbers': numbers_info}, status_code=200)

@router.get("/get-phone-agents")
def get_phone_agents(params: AgentFilterParams = Depends(), db: Session = Depends(get_db),
                     user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    agents = db.query(PhoneAgent).filter_by(user_id=user_id).all()
    if not agents:
        return JSONResponse(content={'error': _("first create agents")}, status_code=404)
    
    agents_info = []
    
    for agent in agents:
        agent_data = {}
        agent_data['id'] = agent.id
        agent_data['agent_name'] = agent.agent_name
        agent_data['status'] = agent.status
        agent_data['language'] = agent.language
        agent_data['voice'] = agent.voice
        agent_data['phone_numbers'] = agent.phone_number
        agents_info.append(agent_data)
        
    return JSONResponse(content={'agents_info': agents_info}, status_code=200)

@router.get("/get-phone-campaigns")
def get_phone_campaigns(params: AgentFilterParams = Depends(), db: Session = Depends(get_db),
                        user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    campaigns = db.query(PhoneCampaign).filter_by(user_id=user_id).all()
    if not campaigns:
        return JSONResponse(content={'error': _("No campaigns created")}, status_code=404)
    
    campaigns_info = []
    
    for campaign in campaigns:
        campaign_data = {}
        agent = db.query(PhoneAgent).filter_by(id=campaign.agent).first()
        campaign_data['id'] = campaign.id
        campaign_data['campaign_name'] = campaign.campaign_name
        campaign_data['agent_name'] = agent.agent_name
        campaign_data['status'] = campaign.status
        campaign_data['language'] = campaign.language
        campaign_data['total_calls'] = 0
        campaign_data['creation_date'] = str(campaign.created_at)
        campaigns_info.append(campaign_data)
        
    return JSONResponse(content={'campaigns_info': campaigns_info}, status_code=200)

@router.get("/phone-campaign-detail/{campaign_id}")
def get_phone_campaign_detail(campaign_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    campaign = db.query(PhoneCampaign).filter_by(id=campaign_id, user_id=user_id).first()
    if not campaign:
        return JSONResponse(content={'error': _("Campaign does not exist")}, status_code=404)
    
    campaign_data = {}
    agent = db.query(PhoneAgent).filter_by(id=campaign.agent).first()
    campaign_data['id'] = campaign.id
    campaign_data['campaign_name'] = campaign.campaign_name
    campaign_data['language'] = campaign.language
    campaign_data['voice'] = campaign.voice
    campaign_data['target_lists'] = campaign.target_lists
    campaign_data['choose_calendar'] = campaign.choose_calendar
    campaign_data['max_call_time'] = campaign.max_call_time
    campaign_data['agent'] = agent.id
    campaign_data['tom_engages'] = campaign.tom_engages
    campaign_data['phone_number'] = campaign.phone_number
    campaign_data['country'] = campaign.country
    campaign_data['catch_phrase'] = campaign.catch_phrase
    campaign_data['call_script'] = campaign.call_script
        
    return JSONResponse(content={'campaign_data': campaign_data}, status_code=200)

@router.patch("/phone-number-status/{phone_number_id}")
def updating_status_of_phone_number(phone_number_id,  db: Session = Depends(get_db),
                                    user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    number = db.query(AgentPhoneNumbers).filter_by(id=phone_number_id, user_id=user_id).first()
    if number:
        if number.status == False:
            number.status = True
            db.commit()
            return JSONResponse(content={'success': _('status updated for number')}, status_code=200)
        
        if number.status == True:
            number.status = False
            db.commit()
            return JSONResponse(content={'success': _('status updated for number')}, status_code=200)
    return JSONResponse(content={'error': _('Phone Number does not exist')}, status_code=404)

@router.patch("/phone-agent-status/{agent_id}")
def updating_status_of_phone_agent(agent_id,  db: Session = Depends(get_db),
                                   user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    agent = db.query(PhoneAgent).filter_by(id=agent_id, user_id=user_id).first()
    if agent:
        if agent.status == False:
            agent.status = True
            db.commit()
            return JSONResponse(content={'success': _('status updated for agent')}, status_code=200)
        
        if agent.status == True:
            agent.status = False
            db.commit()
            return JSONResponse(content={'success': _('status updated for agent')}, status_code=200)
    return JSONResponse(content={'error': _('Phone Number does not exist')}, status_code=404)

@router.delete("/phone-number/{phone_number_id}")
def delete_phone_number(phone_number_id,  db: Session = Depends(get_db), 
                        user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    number = db.query(AgentPhoneNumbers).filter_by(id=phone_number_id, user_id=user_id).first()
    if number:
        db.delete(number)
        db.commit()
        return JSONResponse(content={'success': _('Phone Number deleted successfully')}, status_code=200)
    return JSONResponse(content={'error': _('Phone Number does not exist')}, status_code=404)

@router.delete("/phone-campaign/{campaign_id}")
def delete_campaign(campaign_id,  db: Session = Depends(get_db), 
                    user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    
    campaign = db.query(PhoneCampaign).filter_by(id=campaign_id, user_id=user_id).first()
    if campaign:
        db.delete(campaign)
        db.commit()
        return JSONResponse(content={'success': _('Campaign deleted successfully')}, status_code=200)
    return JSONResponse(content={'error': _('Campaign does not exist')}, status_code=404)


@router.put("/update-phone-campaign/{campaign_id}")
def update_phone_campign(campaign_id, payload: UpdateCampaign,  db: Session = Depends(get_db),
                         user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
        
    campaign = db.query(PhoneCampaign).filter_by(id=campaign_id, user_id=user_id).first()
    
    if campaign:
        phone_campaign = payload.model_dump(exclude_unset=True)
        for key, value in phone_campaign.items():
            setattr(campaign, key, value)
        db.commit()
        return JSONResponse(content={'success': _('Campaign updated successfully')}, status_code=200)
    return JSONResponse(content={'error': _('Not authorized to update this campaign')}, status_code=404)

@router.post("/duplicate-phone-campaign/{campaign_id}")
def duplicate_a_campaign(campaign_id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user),
                         _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)  
    
    campaign = db.query(PhoneCampaign).filter_by(id=campaign_id, user_id=user_id).first()
    
    if campaign:
        campaign_info = {
            "campaign_name": campaign.campaign_name,
            "language": campaign.language,
            "voice": campaign.voice,
            "choose_calendar": campaign.choose_calendar,
            "max_call_time": campaign.max_call_time,
            "target_lists": campaign.target_lists,
            "country": campaign.country,
            "phone_number": campaign.phone_number,
            "status": campaign.status,
            "catch_phrase": campaign.catch_phrase,
            "call_script": campaign.call_script,
            "agent": campaign.agent}
                
        new_campaign = PhoneCampaign(**campaign_info, user_id=user_id)
        db.add(new_campaign)
        db.commit()
        return JSONResponse(content={'success': _("campaign duplicated")}, status_code=201)
    return JSONResponse(content={'error': _('Campaign does not exist')}, status_code=404) 


@router.get('/make-call')
def make_call(call_record: dict):
    
    try:
        
        db = SessionLocal()
        
        DOMAIN = os.getenv('DOMAIN')
        
        url = f"https://{DOMAIN}/outgoing-call"

        call = twilio_client.calls.create(
            from_=call_record['from_contact_number'],
            to=call_record['contact_number'],
            url=url,
            time_limit=600,
        )
        
        call_record['call_sid'] = call.sid
        call_record['call_type'] = "outgoing"
        
        call_record_instance = CallRecord(**call_record)
        db.add(call_record_instance)
        db.commit()
        
    finally:
        db.close()
    
    return JSONResponse(content={"call_id": call.sid}, status_code=201)

@router.post('/outgoing-call')
def answer(From: str = Form(...),
    To: str = Form(...),
    db: Session = Depends(get_db)):
    response = VoiceResponse()
    
    To = "+91 " + To[3:]
    
    twilio_phone_number = db.query(AgentPhoneNumbers).filter_by(twilio_number=From).first()
    number = twilio_phone_number.phone_number
    user_id = twilio_phone_number.user_id
    
    agent = db.query(PhoneAgent).filter_by(phone_number=number).first()
    campaign = db.query(PhoneCampaign).filter_by(phone_number=number).first()
    
    call_record = db.query(CallRecord).filter_by(from_contact_number=twilio_phone_number.twilio_number, contact_number=To).first()
    call_record.campaign_name = agent.agent_name
    call_record.agent_name = campaign.campaign_name
    call_record.language = campaign.language
    call_record.voice = campaign.voice
    db.commit()
    
    response.say("Connecting to a AI agent. Wait for 10 seconds")
    
    response.pause(length=1)
    connect = Connect()
    DOMAIN = os.getenv('DOMAIN')
    
    connect.stream(url=f'wss://{DOMAIN}/media-stream/{user_id}/{campaign.id}/{agent.id}')
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")

@router.post('/incoming-call')
def incoming_call(From: str = Form(...),
    To: str = Form(...),
    db: Session = Depends(get_db)):
    response = VoiceResponse()
    
    twilio_phone_number = db.query(AgentPhoneNumbers).filter_by(twilio_number=To).first()
    number = twilio_phone_number.phone_number
    user_id = twilio_phone_number.user_id
    
    if twilio_phone_number.number_type != "inbound":
        return
    
    agent = db.query(PhoneAgent).filter_by(phone_number=number).first()
    campaign = db.query(PhoneCampaign).filter_by(phone_number=number).first()

    call_record = {"from_contact_number": From,
                    "contact_number": To}

    call_record['call_type'] = 'incoming'
    call_record['user_id'] = user_id
    call_record['campaign_name'] = campaign.campaign_name
    call_record['agent_name'] = agent.agent_name
    call_record['langauage'] = campaign.language
    call_record['voice'] = campaign.voice
    
    call_record_instance = CallRecord(**call_record)
    db.add(call_record_instance)
    db.commit()
    
    response.say("Connecting to a AI agent. Wait for 10 seconds")
    
    response.pause(length=1)
    connect = Connect()
    DOMAIN = os.getenv('DOMAIN')
    
    connect.stream(url=f'wss://{DOMAIN}/media-stream/{user_id}/{campaign.id}/{agent.id}')
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")

@router.websocket('/media-stream/{user_id}/{campaign_id}/{agent_id}')
async def handle_media_stream(websocket: WebSocket, user_id, campaign_id, agent_id):
    
    await websocket.accept()
    
    async with get_async_db() as db:
        result = await db.execute(select(PhoneCampaign).where(PhoneCampaign.id == int(campaign_id)))
        campaign = result.scalars().first()
        result = await db.execute(select(PhoneAgent).where(PhoneAgent.id == int(agent_id)))
        agent = result.scalars().first()
        prompt = phone_agent_prompt(agent, campaign)
        voice="alloy"

    openai_key = os.getenv("OPENAI_API_KEY")
    async with websockets.connect(
        'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
        additional_headers={
            "Authorization": f"Bearer {openai_key}",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as openai_ws:
        await initialize_session(openai_ws, prompt, voice)
        stream_sid = None

        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data['event'] == 'media' and openai_ws:
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        await openai_ws.send(json.dumps(audio_append))
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        print(f"Incoming stream has started {stream_sid}")
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws:
                    await openai_ws.close()

        async def send_to_twilio():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            nonlocal stream_sid
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    event_type = response.get("type")
                    

                    if event_type == "conversation.item.input_audio_transcription.completed":
                        user_text = response.get("transcript", "")
                        print("Transcript final (user):", user_text)
                        
                        knowledge_base = fetch_text(user_text, user_id)
                    
                        payload = {"knowledge_base": knowledge_base,
                                        "text": user_text}
                        
                        payload = json.dumps(payload)
                        
                        conversation_item = {
                            "type": "conversation.item.create",
                            "item": {
                                "type": "message",
                                "role": "user",
                                "content": [
                                    {
                                        "type": "input_text",
                                        "text": payload
                                    }
                                ]
                            }
                        }
                        await openai_ws.send(json.dumps(conversation_item))
                        await openai_ws.send(json.dumps({"type": "response.create", "response": {"modalities": ["text", "audio"]}}))
                        
                        # async for openai_message in openai_ws:
                        #     response = json.loads(openai_message)
                        #     print(openai_message)
                        #     event_type = response.get("type")
                    
                    # if event_type == "response.done":
                    #     outputs = response['response']['output']
                    #     for output in outputs:
                    #         if output.get('name') == "generate_horoscope":
                    #             {
                    #             "type": "conversation.item.create",
                    #             "item": {
                    #                 "type": "function_call_output",
                    #                 "call_id": output.get('call_id'),
                    #                 "output": "{\"output\": \"20\"}"
                    #             }
                    #             }
                    #             await openai_ws.send(json.dumps(conversation_item))
                                
                    
                    if event_type == "response.audio.delta" and response.get("delta"):
                        try:
                            audio_payload = base64.b64encode(
                                base64.b64decode(response["delta"])
                            ).decode("utf-8")

                            audio_delta = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {"payload": audio_payload}
                            }
                            await websocket.send_json(audio_delta)
                        except Exception as e:
                            print(f"Error processing audio data: {e}")
                            
            except Exception as e:
                print(f"Error in send_to_twilio: {e}")
        await asyncio.gather(receive_from_twilio(), send_to_twilio())
        
@router.post("/call-status")
def call_status(from_number: str = Form(...),
    to_number: str = Form(...),
   call_sid: str = Form(...),
   call_status: str = Form(...)):
    
    print(from_number, to_number, call_sid, call_status)
    
    return 

@router.get("/get-phone-agent-details")
def get_phone_agent_details(db: Session = Depends(get_db),
                         user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404) 
    
    agents = db.query(PhoneAgent).filter_by(user_id=user_id).count()
    
    campaigns = db.query(PhoneCampaign).filter_by(user_id=user_id).count()
    
    outbound_calls = db.query(CallRecord).filter_by(call_type='outbound', user_id=user_id).count()
    
    inbound_calls = db.query(CallRecord).filter_by(call_type='inbound', user_id=user_id).count()
    
    return JSONResponse(content={'success': {"agents": agents,
                                             "campaigns": campaigns,
                                             "outbound_calls": outbound_calls,
                                             "inbound_calls": inbound_calls}}, status_code=200)

@router.get("/outbound-call-details")
def outbound_call_details(db: Session = Depends(get_db),
                         user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404) 
    
    records = db.query(CallRecord).filter_by(call_type='outgoing', user_id=user_id).all()
    
    response = []
    
    for record in records:
        record_info = {}
        
        record_info['campaign_name'] = record.campaign_name
        record_info['agent_name'] = record.agent_name
        record_info['langauage'] = record.language
        record_info['voice'] = record.voice
        record_info['date'] = str(record.created_at)
        record_info['status'] = "replied"
        record_info['recipient_no'] = record.call_sid
        record_info['duration'] = 600 
        response.append(record_info)
        
    
    return JSONResponse(content={'success': response}, status_code=200)

@router.get("/inbound-call-details")
def inbound_call_details(db: Session = Depends(get_db),
                         user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404) 
    
    records = db.query(CallRecord).filter_by(call_type='inbound', user_id=user_id).all()
    
    response = []
    
    for record in records:
        record_info = {}
        
        record_info['campaign_name'] = record.campaign_name
        record_info['agent_name'] = record.agent_name
        record_info['langauage'] = record.language
        record_info['voice'] = record.voice
        record_info['date'] = str(record.created_at)
        record_info['status'] = "replied"
        record_info['recipient_no'] = record.call_sid
        record_info['duration'] = 600 
        response.append(record_info)
        
    
    return JSONResponse(content={'success': response}, status_code=200)
    