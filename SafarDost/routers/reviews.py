from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List
from sqlalchemy.orm import Session
from database import get_db
from models.review import Reviews
from models.place import Places
from models.hotel import Hotels
from models.restaurant import Restaurants
from schemas import review_schemas
from utils.auth_utils import get_current_user

router = APIRouter(prefix="/reviews", tags=["Reviews Management"])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.post("/", response_model=review_schemas.ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(review_request: review_schemas.ReviewCreate, db: db_dependency, current_user: user_dependency):
    """
    Submits a review for a Hotel, Place, or Restaurant. Requires a valid traveler login token.
    """
    # 1. Count how many entity targets were passed in the payload
    targets = [review_request.place_id, review_request.hotel_id, review_request.restaurant_id]
    active_targets = len([t for t in targets if t is not None])

    # Defensive Validation Check: Enforce targeting exactly one parent profile entity
    if active_targets != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A review must target exactly one entity. Provide exactly one: place_id, hotel_id, OR restaurant_id."
        )

    # 2. Defensive Integrity Checks: Confirm targeted entity exists in the active table row index
    if review_request.place_id:
        if not db.query(Places).filter(Places.id == review_request.place_id).first():
            raise HTTPException(status_code=404, detail=f"Tourist place ID {review_request.place_id} does not exist.")

    if review_request.hotel_id:
        if not db.query(Hotels).filter(Hotels.id == review_request.hotel_id).first():
            raise HTTPException(status_code=404,
                                detail=f"Hotel accommodation ID {review_request.hotel_id} does not exist.")

    if review_request.restaurant_id:
        if not db.query(Restaurants).filter(Restaurants.id == review_request.restaurant_id).first():
            raise HTTPException(status_code=404,
                                detail=f"Restaurant profile ID {review_request.restaurant_id} does not exist.")

    # 3. Map values via dictionary unpacking and explicitly append the token user identification
    db_review = Reviews(
        **review_request.model_dump(),
        user_id=current_user.get("id")
    )

    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


@router.get("/place/{place_id}", response_model=List[review_schemas.ReviewResponse], status_code=status.HTTP_200_OK)
def get_reviews_for_place(place_id: int, db: db_dependency):
    """
    Fetches the public review stream linked to a specific tourist destination.
    """
    reviews = db.query(Reviews).filter(Reviews.place_id == place_id).all()
    return reviews


@router.get("/hotel/{hotel_id}", response_model=List[review_schemas.ReviewResponse], status_code=status.HTTP_200_OK)
def get_reviews_for_hotel(hotel_id: int, db: db_dependency):
    """
    Fetches the public review stream linked to a specific hotel accommodation.
    """
    reviews = db.query(Reviews).filter(Reviews.hotel_id == hotel_id).all()
    return reviews


@router.get("/restaurant/{restaurant_id}", response_model=List[review_schemas.ReviewResponse],
            status_code=status.HTTP_200_OK)
def get_reviews_for_restaurant(restaurant_id: int, db: db_dependency):
    """
    Fetches the public review stream linked to a specific Pakistani restaurant profile.
    """
    reviews = db.query(Reviews).filter(Reviews.restaurant_id == restaurant_id).all()
    return reviews


@router.put("/{review_id}", response_model=review_schemas.ReviewResponse, status_code=status.HTTP_200_OK)
def update_review(review_id: int, review_request: review_schemas.ReviewUpdate, db: db_dependency,
                  current_user: user_dependency):
    """
    Allows a traveler to dynamically alter their own review comment or score.
    """
    db_review = db.query(Reviews).filter(Reviews.id == review_id).first()

    if not db_review:
        raise HTTPException(status_code=404, detail="Review record item not found.")

    # Ownership Validation Guard Clause: Ensure a traveler cannot modify another person's submission
    if db_review.user_id != current_user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not maintain adequate ownership permissions to update this review."
        )

    update_data = review_request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_review, key, value)

    db.commit()
    db.refresh(db_review)
    return db_review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int, db: db_dependency, current_user: user_dependency):
    """
    Removes a review record permanently from the database cache. Restricted to the original author.
    """
    db_review = db.query(Reviews).filter(Reviews.id == review_id).first()

    if not db_review:
        raise HTTPException(status_code=404, detail="Review record item not found.")

    # Ownership Guard Clause
    if db_review.user_id != current_user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not maintain adequate ownership permissions to delete this review."
        )

    db.delete(db_review)
    db.commit()
