# backend/sms_utils.py
from twilio.rest import Client
from backend.config import settings

def send_sms(to_number: str, body: str):
    if not settings.TWILIO_SID or not settings.TWILIO_TOKEN:
        raise RuntimeError("Twilio not configured")
    client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
    msg = client.messages.create(body=body, from_=settings.TWILIO_FROM, to=to_number)
    return msg.sid

