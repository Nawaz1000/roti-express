from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import random
from typing import Optional

from ..models import OrderCreate, Order, OrderStatus, PaymentStatus, PaymentMethod, PaymentDetails
from ..database import get_database
from ..config import settings
from ..services.whatsapp import notify_order_placed
from ..services.payment import generate_upi_qr_base64, create_razorpay_order

router = APIRouter(prefix="/api/orders", tags=["Orders"])

def generate_order_code() -> str:
    date_str = datetime.now().strftime("%Y%m%d")
    random_digits = f"{random.randint(0, 9999):04d}"
    return f"RE-{date_str}-{random_digits}"

@router.post("", response_model=dict)
async def create_order(order_req: OrderCreate, db=Depends(get_database)):
    # 1. Fetch settings for price and capacity
    app_settings = await db.settings.find_one({"_id": "app_settings"})
    if not app_settings:
        raise HTTPException(status_code=500, detail="Settings not configured")

    price_per_roti = app_settings.get("price_per_roti", 10.0)
    max_rotis = app_settings.get("max_rotis_per_slot", 50)


    # 3. Create Order Document
    order_code = generate_order_code()
    total_amount = order_req.quantity * price_per_roti

    # Save customer (upsert based on phone)
    customer_doc = {
        "name": order_req.customer.name,
        "phone": order_req.customer.phone,
        "address": order_req.customer.address,
        "created_at": datetime.now(timezone.utc)
    }
    
    customer_result = await db.customers.find_one_and_update(
        {"phone": order_req.customer.phone},
        {"$set": customer_doc},
        upsert=True,
        return_document=True
    )

    new_order = {
        "order_code": order_code,
        "customer": {
            "customer_id": customer_result["_id"],
            "name": order_req.customer.name,
            "phone": order_req.customer.phone,
            "address": order_req.customer.address
        },
        "quantity": order_req.quantity,
        "price_per_roti": price_per_roti,
        "total_amount": total_amount,
        "delivery_slot": None,
        "payment_method": order_req.payment_method,
        "payment_status": PaymentStatus.PENDING,
        "order_status": OrderStatus.ONGOING,
        "payment": {
            "upi_ref_id": None,
            "razorpay_order_id": None,
            "verified_by": None,
            "verified_at": None
        },
        "notes": order_req.notes,
        "created_at": datetime.now(timezone.utc),
        "completed_at": None
    }

    # If Razorpay, generate razorpay order id
    qr_code_base64 = None
    if order_req.payment_method == PaymentMethod.UPI:
        if settings.PAYMENT_MODE == "razorpay":
            rzp_order = create_razorpay_order(order_code, total_amount)
            new_order["payment"]["razorpay_order_id"] = rzp_order.get("id")
        else:
            qr_code_base64 = generate_upi_qr_base64(order_code, total_amount)

    # Insert order
    result = await db.orders.insert_one(new_order)
    
    # 4. Notify via WhatsApp
    await notify_order_placed(
        order_code=order_code,
        customer_name=order_req.customer.name,
        phone=order_req.customer.phone,
        quantity=order_req.quantity,
        total_amount=total_amount,
        payment_method=order_req.payment_method,
        delivery_slot=order_req.delivery_slot.isoformat() if order_req.delivery_slot else "N/A",
        address=order_req.customer.address
    )

    return {
        "message": "Order created successfully",
        "order_code": order_code,
        "total_amount": total_amount,
        "payment_method": order_req.payment_method,
        "payment_status": PaymentStatus.PENDING,
        "qr_code_base64": qr_code_base64,
        "razorpay_order_id": new_order["payment"]["razorpay_order_id"]
    }

@router.get("/{order_code}", response_model=Order)
async def get_order(order_code: str, db=Depends(get_database)):
    order = await db.orders.find_one({"order_code": order_code})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
