from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import jwt

from ..models import AdminLogin, Token, OrderStatus, PaymentStatus
from ..database import get_database
from ..config import settings
router = APIRouter(prefix="/api/admin", tags=["Admin"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_admin(token: str = Depends(oauth2_scheme), db=Depends(get_database)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    admin = await db.admins.find_one({"username": username})
    if admin is None:
        raise credentials_exception
    return admin

@router.post("/login", response_model=Token)
async def login(login_data: AdminLogin, db=Depends(get_database)):
    admin = await db.admins.find_one({"username": login_data.username})
    if not admin or not pwd_context.verify(login_data.password, admin["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": admin["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/orders")
async def get_orders(status: str = "ONGOING", db=Depends(get_database), admin=Depends(get_current_admin)):
    orders = await db.orders.find({"order_status": status}).sort("created_at", -1).to_list(1000)
    for o in orders:
        o["_id"] = str(o["_id"])
        if "customer" in o and "customer_id" in o["customer"]:
            o["customer"]["customer_id"] = str(o["customer"]["customer_id"])
    return orders

@router.patch("/orders/{order_code}/complete")
async def mark_order_complete(order_code: str, db=Depends(get_database), admin=Depends(get_current_admin)):
    result = await db.orders.find_one_and_update(
        {"order_code": order_code},
        {"$set": {
            "order_status": OrderStatus.COMPLETED.value,
            "completed_at": datetime.now(timezone.utc)
        }},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Order not found")
    result["_id"] = str(result["_id"])
    return result

@router.patch("/orders/{order_code}/payment")
async def mark_order_paid(order_code: str, db=Depends(get_database), admin=Depends(get_current_admin)):
    result = await db.orders.find_one_and_update(
        {"order_code": order_code},
        {"$set": {
            "payment_status": PaymentStatus.PAID.value,
            "payment.verified_by": "admin_manual",
            "payment.verified_at": datetime.now(timezone.utc)
        }},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Order not found")
    result["_id"] = str(result["_id"])
    return result

@router.get("/stats")
async def get_stats(db=Depends(get_database), admin=Depends(get_current_admin)):
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Ongoing count
    ongoing_count = await db.orders.count_documents({"order_status": OrderStatus.ONGOING})
    # Completed count
    completed_count = await db.orders.count_documents({"order_status": OrderStatus.COMPLETED})
    
    # Total revenue today
    pipeline_today = [
        {"$match": {
            "created_at": {"$gte": today},
            "payment_status": PaymentStatus.PAID
        }},
        {"$group": {"_id": None, "revenue": {"$sum": "$total_amount"}, "count": {"$sum": 1}}}
    ]
    res_today = await db.orders.aggregate(pipeline_today).to_list(1)
    revenue_today = res_today[0]["revenue"] if res_today else 0
    orders_today = res_today[0]["count"] if res_today else 0
    
    # Total revenue all-time
    pipeline_all = [
        {"$match": {
            "payment_status": PaymentStatus.PAID
        }},
        {"$group": {"_id": None, "revenue": {"$sum": "$total_amount"}, "count": {"$sum": 1}}}
    ]
    res_all = await db.orders.aggregate(pipeline_all).to_list(1)
    revenue_all = res_all[0]["revenue"] if res_all else 0
    orders_all = res_all[0]["count"] if res_all else 0
    
    return {
        "ongoing_orders": ongoing_count,
        "completed_orders": completed_count,
        "orders_today": orders_today,
        "revenue_today": revenue_today,
        "total_orders_all_time": orders_all,
        "total_revenue_all_time": revenue_all
    }
