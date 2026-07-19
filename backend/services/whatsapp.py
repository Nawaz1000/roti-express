import httpx
import logging
from ..config import settings

logger = logging.getLogger(__name__)

async def send_whatsapp_message(to_phone: str, template: str, context: dict):
    """
    Interface to send a WhatsApp message.
    If WHATSAPP_API_TOKEN is 'mock_token' or empty, it will just log the message.
    """
    if not settings.WHATSAPP_API_TOKEN or settings.WHATSAPP_API_TOKEN == "mock_token":
        logger.info(f"[MOCK WHATSAPP] To: {to_phone} | Template: {template} | Context: {context}")
        return {"status": "mocked", "message": "Mock WhatsApp message logged."}

    # Meta Cloud API Integration
    url = f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json"
    }

    # Format the context into Meta's template parameter structure
    # This assumes template is a utility template with numbered parameters.
    # In a real scenario, you'd map context to the specific template's parameter order.
    # We will pass context values as text parameters.
    parameters = [{"type": "text", "text": str(v)} for v in context.values()]

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone.replace("+", ""),
        "type": "template",
        "template": {
            "name": template,
            "language": {
                "code": "en"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": parameters
                }
            ]
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"[WHATSAPP SUCCESS] To: {to_phone}")
            return response.json()
    except Exception as e:
        logger.error(f"[WHATSAPP FAILED] To: {to_phone} | Error: {str(e)}")
        # We don't raise here so it doesn't break the order flow
        return {"status": "failed", "error": str(e)}

async def notify_order_placed(order_code: str, customer_name: str, phone: str, quantity: int, total_amount: float, payment_method: str, delivery_slot: str, address: str):
    context_customer = {
        "order_code": order_code,
        "name": customer_name,
        "quantity": quantity,
        "total_amount": total_amount,
        "payment_method": payment_method,
        "delivery_slot": delivery_slot
    }
    
    context_admin = {
        "order_code": order_code,
        "name": customer_name,
        "phone": phone,
        "address": address,
        "quantity": quantity,
        "total_amount": total_amount,
        "payment_method": payment_method,
        "delivery_slot": delivery_slot
    }

    # Send to customer
    await send_whatsapp_message(phone, settings.WHATSAPP_TEMPLATE_NAME, context_customer)
    
    # Send to admin
    if settings.WHATSAPP_ADMIN_NUMBER:
        await send_whatsapp_message(settings.WHATSAPP_ADMIN_NUMBER, settings.WHATSAPP_TEMPLATE_NAME + "_admin", context_admin)

async def notify_payment_confirmed(order_code: str, phone: str):
    context = {"order_code": order_code}
    await send_whatsapp_message(phone, "payment_confirmed", context)
