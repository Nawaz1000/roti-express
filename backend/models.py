from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from enum import Enum

class OrderStatus(str, Enum):
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"

class PaymentMethod(str, Enum):
    UPI = "UPI"
    COD = "COD"

class Customer(BaseModel):
    name: str
    phone: str
    address: str

class OrderItem(BaseModel):
    name: str
    price: float
    quantity: int = Field(gt=0)

class PaymentDetails(BaseModel):
    upi_ref_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None

class OrderCreate(BaseModel):
    customer: Customer
    items: List[OrderItem]
    delivery_slot: Optional[datetime] = None
    payment_method: PaymentMethod
    notes: Optional[str] = ""

class Order(BaseModel):
    id: str = Field(alias="_id")
    order_code: str
    customer: Customer
    items: List[OrderItem]
    total_amount: float
    delivery_slot: Optional[datetime] = None
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    order_status: OrderStatus
    payment: PaymentDetails
    notes: str
    created_at: datetime
    completed_at: Optional[datetime] = None

class AdminLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class AppSettings(BaseModel):
    price_per_roti: float
    max_rotis_per_slot: int
    min_advance_hours: int
