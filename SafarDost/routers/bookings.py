import os
import smtplib
from email.mime.text import MIMEText
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List
from datetime import date
from sqlalchemy.orm import Session
from database import get_db
from models import Hotels
from models.booking import HotelBookings
from schemas import booking_schemas
from utils.auth_utils import get_current_user

router = APIRouter(prefix="/hotels/book", tags=["Hotel Bookings"])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


def send_vendor_booking_email(booking_id: int, hotel_name: str, location: str, check_in: date, check_out: date,
                              total_price: int, customer_email: str):
    """
    Synchronous utility helper that securely transmits a detailed reservation
    alert email directly to your management operations desk.
    """
    try:
        # 1. Draft the professional text content payload for the notification email
        email_body = f"""
Dear Hotel Management Operations Team,

A brand new guest reservation has been successfully confirmed via the SafarDost Platform.

=======================================================
RESERVATION DETAILS
=======================================================
Booking Reference ID: #{booking_id}
Target Property Name: {hotel_name}
Property Location:   {location}
Guest Account Email: {customer_email}
Check-In Date:       {check_in}
Check-Out Date:      {check_out}
Total Payout Amount: {total_price:,} PKR (Cash on Arrival)
=======================================================

Please cross-reference this Booking Reference ID inside your vendor administration dashboard panel on arrival.

Safe Travels,
The SafarDost/TravelMate Pakistan Backend System Automation
        """

        msg = MIMEText(email_body)
        msg['Subject'] = f"🔔 NEW RESERVATION ALERT - Booking Reference ID #{booking_id}"

        # Pull mail server environments securely matching your system database structure patterns
        smtp_sender = os.environ.get("SAFARDOST_EMAIL_USER", "notifications@safardost.com")
        smtp_receiver = os.environ.get("SAFARDOST_VENDOR_DESK", "vendor-desk@safardost.com")

        msg['From'] = smtp_sender
        msg['To'] = smtp_receiver

        # 2. Open a standard synchronous blocking connection to your mail server provider
        smtp_host = os.environ.get("SAFARDOST_SMTP_HOST", "://gmail.com")
        smtp_port = int(os.environ.get("SAFARDOST_SMTP_PORT", 587))
        smtp_password = os.environ.get("SAFARDOST_EMAIL_PASSWORD")

        # Establish connection securely using standard TLS wrappers
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_password:
                server.login(smtp_sender, smtp_password)
            server.send_message(msg)

    except Exception as email_error:
        # Caught defensively so mail provider server timeouts do not cancel database transactions
        print(f"[SECURITY/OPERATIONS WARNING]: Automated reservation alert email execution failed: {email_error}")


@router.post("/", response_model=booking_schemas.BookingResponse, status_code=status.HTTP_201_CREATED)
def reserve_hotel_room(booking_request: booking_schemas.BookingCreate, db: db_dependency,
                       current_user: user_dependency):
    """
    Creates a brand-new hotel accommodation reservation in Pakistan and triggers an automated notification email.
    """
    # 1. Past-Date Security Guard: Blocks corrupt historical user input selections
    if booking_request.check_in_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create a reservation for a date that has already passed."
        )

    # 2. Timeline Guard Clause: Ensure checkout happens after check-in day boundary
    if booking_request.check_out_date <= booking_request.check_in_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The check-out date must occur after your selected check-in date."
        )

    # 3. Defensive Integrity Guard: Verify target hotel row exists on disk
    target_hotel = db.query(Hotels).filter(Hotels.id == booking_request.hotel_id).first()
    if not target_hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hotel record item not found for ID: {booking_request.hotel_id}"
        )

    # 4. Compute duration delta and auto-calculate cumulative financial costs
    delta_days = (booking_request.check_out_date - booking_request.check_in_date).days
    calculated_cost = delta_days * target_hotel.price_per_night

    # 5. Map values via dictionary unpacking and attach calculated data properties
    db_booking = HotelBookings(
        **booking_request.model_dump(),
        user_id=current_user.get("id"),
        total_price=calculated_cost
    )

    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    # 6. TRIGGER AUTOMATED EMAIL NOTIFICATION
    send_vendor_booking_email(
        booking_id=db_booking.id,
        hotel_name=target_hotel.name,
        location=target_hotel.location,
        check_in=db_booking.check_in_date,
        check_out=db_booking.check_out_date,
        total_price=db_booking.total_price,
        customer_email=current_user.get("email")
    )

    return db_booking


@router.get("/history", response_model=List[booking_schemas.BookingResponse], status_code=status.HTTP_200_OK)
def get_user_booking_history(db: db_dependency, current_user: user_dependency):
    """
    Retrieves the entire chronological reservation list for the currently logged-in traveler account.
    """
    bookings = db.query(HotelBookings).filter(HotelBookings.user_id == current_user.get("id")).all()
    return bookings


@router.put("/{booking_id}", response_model=booking_schemas.BookingResponse, status_code=status.HTTP_200_OK)
def update_hotel_reservation(booking_id: int, booking_request: booking_schemas.BookingUpdate, db: db_dependency,
                             current_user: user_dependency):
    """
    Dynamically modifies an existing reservation's dates and automatically recalculates the total price in PKR.
    Restricted to the original reservation owner.
    """
    # 1. Integrity Guard: Fetch the existing booking record
    db_booking = db.query(HotelBookings).filter(HotelBookings.id == booking_id).first()
    if not db_booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hotel reservation record not found for ID: {booking_id}"
        )

    # 2. Ownership Guard Clause: Block travelers from editing other people's reservations
    if db_booking.user_id != current_user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not maintain adequate ownership permissions to modify this reservation."
        )

    # 3. Extract dynamic incoming data payload excluding unset variables
    incoming_data = booking_request.model_dump(exclude_unset=True)

    # 4. Determine final check-in and check-out dates to run calculations
    final_check_in = incoming_data.get("check_in_date", db_booking.check_in_date)
    final_check_out = incoming_data.get("check_out_date", db_booking.check_out_date)

    # 5. Past-Date Security Guard: Prevent shifting check-in dates into the past
    if "check_in_date" in incoming_data and final_check_in < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a reservation to a check-in date that has already passed."
        )

    # 6. Timeline Guard Clause: Ensure checkout occurs after check-in
    if final_check_out <= final_check_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The check-out date must occur after your selected check-in date."
        )

    # 7. Apply new date fields to our model record instance dynamically
    for key, value in incoming_data.items():
        setattr(db_booking, key, value)

    # 8. Fetch the parent hotel details to recalculate dynamic pricing shifts
    target_hotel = db.query(Hotels).filter(Hotels.id == db_booking.hotel_id).first()

    # 9. Compute new stay duration delta and update cumulative financial costs
    new_delta_days = (final_check_out - final_check_in).days
    db_booking.total_price = new_delta_days * target_hotel.price_per_night

    db.commit()
    db.refresh(db_booking)

    # 10. TRIGGER UPDATED EMAIL NOTIFICATION
    send_vendor_booking_email(
        booking_id=db_booking.id,
        hotel_name=target_hotel.name,
        location=target_hotel.location,
        check_in=db_booking.check_in_date,
        check_out=db_booking.check_out_date,
        total_price=db_booking.total_price,
        customer_email=current_user.get("email")
    )

    return db_booking


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_hotel_reservation(booking_id: int, db: db_dependency, current_user: user_dependency):
    """
    Permanently cancels and removes a reservation record from the database. Restricted to the reservation owner.
    """
    db_booking = db.query(HotelBookings).filter(HotelBookings.id == booking_id).first()

    if not db_booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hotel reservation record not found for ID: {booking_id}"
        )

    # Ownership Guard Clause
    if db_booking.user_id != current_user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not maintain adequate ownership permissions to cancel this reservation."
        )

    db.delete(db_booking)
    db.commit()
