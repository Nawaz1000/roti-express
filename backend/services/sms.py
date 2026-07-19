import logging
import asyncio
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from ..config import settings

logger = logging.getLogger(__name__)

async def send_completion_otp_sms(phone: str, otp: str):
    """
    Sends an OTP via SMS. Uses Twilio if configured, otherwise falls back to printing.
    """
    message = f"Your RotiExpress order completion OTP is: {otp}. This code is valid for 1 minute."
    
    if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_FROM_NUMBER:
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            # Ensure phone number has country code. Assuming India (+91) if not provided.
            to_phone = phone if phone.startswith('+') else f"+91{phone}"
            
            # Twilio's client.messages.create is synchronous, so we run it in a thread if needed, 
            # but since it's just a simple API call we can run it here (or use run_in_executor)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: client.messages.create(
                body=message,
                from_=settings.TWILIO_FROM_NUMBER,
                to=to_phone
            ))
            print(f"==== TWILIO SMS SENT TO {to_phone} ====")
            return True
        except TwilioRestException as e:
            print(f"Twilio Error: {e}")
            return False
        except Exception as e:
            print(f"Error sending SMS: {e}")
            return False
    else:
        # Mock behavior
        print(f"==== MOCK SMS TO {phone} ====")
        print(message)
        print("========================")
        await asyncio.sleep(1)
        return True
