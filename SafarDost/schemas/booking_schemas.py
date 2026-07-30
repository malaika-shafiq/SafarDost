from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

class BookingCreate(BaseModel):
    hotel_id: int = Field(gt=0)
    check_in_date: date       # Input format from mobile client: YYYY-MM-DD
    check_out_date: date      # Input format from mobile client: YYYY-MM-DD

class BookingUpdate(BaseModel):
    check_in_date: Optional[date] = None   # Optional field for flexible mobile client modifications
    check_out_date: Optional[date] = None  # Optional field for flexible mobile client modifications

class BookingResponse(BaseModel):
    id: int
    hotel_id: int
    user_id: int
    check_in_date: date
    check_out_date: date
    total_price: int          # Calculated nightly price saved in PKR
    created_at: datetime

    class Config:
        from_attributes = True  # Allows Pydantic to cleanly serialize standard SQLAlchemy row instances
