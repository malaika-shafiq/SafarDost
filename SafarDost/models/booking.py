import datetime
from sqlalchemy import Column, Integer, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
from database import Base

class HotelBookings(Base):
    __tablename__ = "hotel_bookings"

    id = Column(Integer, primary_key=True, index=True)
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)
    total_price = Column(Integer, nullable=False)  # Automatically calculated rate in PKR
    # Enforces explicit timezone support inside your SQLite engine configuration
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Foreign Key tracking references
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)

    # Relational loops back to parent models
    user = relationship("Users", back_populates="bookings")
    hotel = relationship("Hotels", back_populates="bookings")
