from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional

from ..database import get_database
from ..models import OrderStatus

router = APIRouter(prefix="/api/slots", tags=["Slots"])

@router.get("", response_model=List[Dict])
async def get_available_slots(date: Optional[str] = None, db=Depends(get_database)):
    """
    Returns available slots. If date is not provided, returns slots for today and tomorrow.
    A slot is available if it's > 2 hours from now and capacity hasn't been reached.
    """
    app_settings = await db.settings.find_one({"_id": "app_settings"})
    if not app_settings:
        raise HTTPException(status_code=500, detail="Settings not configured")
        
    max_rotis = app_settings.get("max_rotis_per_slot", 50)
    min_advance = app_settings.get("min_advance_hours", 2)
    
    now = datetime.now(timezone.utc)
    cutoff_time = now + timedelta(hours=min_advance)

    dates_to_check = []
    if date:
        try:
            query_date = datetime.strptime(date, "%Y-%m-%d").date()
            dates_to_check.append(query_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        # Default: check today and tomorrow
        dates_to_check.append(now.date())
        dates_to_check.append((now + timedelta(days=1)).date())

    operating_hours = range(10, 23)
    available_slots = []

    for query_date in dates_to_check:
        for hour in operating_hours:
            slot_time = datetime(
                query_date.year, query_date.month, query_date.day, 
                hour, 0, 0, tzinfo=timezone.utc
            )
            
            if slot_time < cutoff_time:
                continue
                
            # Check current booked capacity
            pipeline = [
                {"$match": {
                    "delivery_slot": slot_time,
                    "order_status": {"$ne": OrderStatus.CANCELLED}
                }},
                {"$group": {"_id": None, "total_ordered": {"$sum": "$quantity"}}}
            ]
            aggr_result = await db.orders.aggregate(pipeline).to_list(1)
            current_ordered = aggr_result[0]["total_ordered"] if aggr_result else 0
            
            remaining = max_rotis - current_ordered
            
            if remaining > 0:
                available_slots.append({
                    "time": slot_time.isoformat(),
                    "remaining_capacity": remaining
                })
            
    return available_slots
