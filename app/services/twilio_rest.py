import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect
from dotenv import load_dotenv

load_dotenv()

twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

def buy_number():
    domain = os.getenv('DOMAIN')
    available_numbers = twilio_client.available_phone_numbers("US").local.list(limit=1)
    for available_number in available_numbers:
        number = available_number.phone_number
        purchased_number = twilio_client.incoming_phone_numbers.create(phone_number=number,
                                                                       status_callback=f"https://{domain}/call-status",
              status_callback_event=["initiated", "ringing", "answered", "completed"])
    return purchased_number.phone_number


    

