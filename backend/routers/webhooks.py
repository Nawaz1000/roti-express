from fastapi import APIRouter, Request, HTTPException, Depends, Header
from datetime import datetime, timezone
import json

from ..database import get_database
from ..services.payment import verify_razorpay_signature
from ..services.whatsapp import notify_payment_confirmed
from ..models import PaymentStatus

router = APIRouter(prefix="/api/webhook", tags=["Webhooks"])

@router.post("/payment")
async def razorpay_webhook(request: Request, x_razorpay_signature: str = Header(None), db=Depends(get_database)):
    payload_body = await request.body()
    
    # Verify Signature
    if not verify_razorpay_signature(payload_body.decode('utf-8'), x_razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
        
    try:
        data = json.loads(payload_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid payload")
        
    event = data.get("event")
    
    if event == "order.paid":
        payload_entity = data.get("payload", {}).get("order", {}).get("entity", {})
        receipt = payload_entity.get("receipt") # This is our order_code
        
        if not receipt:
            return {"status": "ignored", "reason": "No receipt"}
            
        # Update order in DB
        updated_order = await db.orders.find_one_and_update(
            {"order_code": receipt},
            {"$set": {
                "payment_status": PaymentStatus.PAID,
                "payment.verified_by": "gateway_webhook",
                "payment.verified_at": datetime.now(timezone.utc)
            }},
            return_document=True
        )
        
        if updated_order:
            customer_phone = updated_order.get("customer", {}).get("phone")
            if customer_phone:
                await notify_payment_confirmed(receipt, customer_phone)
                
    return {"status": "ok"}
