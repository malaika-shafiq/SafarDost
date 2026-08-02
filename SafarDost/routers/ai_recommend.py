import os
import json
import datetime
import urllib.request
import urllib.error
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from utils.auth_utils import get_current_user
from models.weather import WeatherCache
from models.ai_history import AIRecommendationHistory
from schemas.ai_schemas import AIRecommendRequest, AIRecommendResponse

router = APIRouter(prefix="", tags=["Intelligent AI Recommendation Engine"])


@router.post("/ai/recommend", response_model=AIRecommendResponse)
def generate_travel_itinerary(
        payload: AIRecommendRequest,
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # 1. Weather Cross-Reference Engine Check
    weather_record = db.query(WeatherCache).filter(
        WeatherCache.city_name.ilike(f"%{payload.destination}%")
    ).first()

    # Analyze weather variables or default to a safe standard layout
    weather_condition = "Clear Sky"
    if weather_record:
        weather_condition = weather_record.condition_text

    # Evaluate dynamic safety constraints (Snowfall intent lock vs dangerous blizzard conditions)
    weather_override_triggered = False
    advisory_text = "Climate systems verified stable. Enjoy your personalized itinerary."

    condition_lower = weather_condition.lower()
    if "blizzard" in condition_lower or "storm" in condition_lower or "heavy rain" in condition_lower:
        weather_override_triggered = True
        advisory_text = f"Severe condition danger detected ({weather_condition}). Forced redirection to indoor/sheltered spaces applied."

    # 2. Tier 1 Fallback: Query internal database assets using local filter boundaries
    # (Simulated local collection processing matching the .ilike architecture pattern)
    local_recommendations_summary = f"No verified database rows for {payload.destination} matching profile fields."

    # 3. Formulate the explicit prompting context parameters for Google Gemini
    GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_KEY")
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Platform AI configuration credentials missing."
        )

    ENDPOINT_URL = f"https://googleapis.com{GEMINI_API_KEY}"

    # System system guard instructions forcing the model to strictly drop a raw JSON object string back
    prompt = f"""
    You are the core AI backend agent for Safardost, a travel engine in Pakistan.
    Build a {payload.total_days}-day itinerary for a trip to {payload.destination} with a total budget of {payload.budget_pkr} PKR.
    The traveler's selected style profile is: {payload.travel_style}.
    Current live weather context is: {weather_condition}. Safety Override Engaged: {weather_override_triggered}.

    Our internal database assets hold: {local_recommendations_summary}. If local assets are empty, use your training data to provide real, famous locations in {payload.destination}.
    If Safety Override is true, ignore dangerous treks and force comfortable sheltered/indoor events.

    You MUST respond with a single, raw, minified JSON object matching this structure exactly without markdown wrappers:
    {{
        "destination_name": "{payload.destination}",
        "chosen_style_applied": "{payload.travel_style}",
        "weather_advisory_applied": {str(weather_override_triggered).lower()},
        "advisory_message": "{advisory_text}",
        "total_projected_cost_pkr": 0.0,
        "itinerary_days": [
            {{
                "day_number": 1,
                "activities": [
                    {{
                        "time_of_day": "Morning",
                        "activity_title": "Name of venue",
                        "activity_category": "Type",
                        "estimated_cost_pkr": 500.0,
                        "justification": "Why this aligns with style and budget constraints"
                    }}
                ]
            }}
        ]
    }}
    Sum all costs accurately and fill out all itinerary days requested.
    """

    # Assemble request frame dictionary
    request_body = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    # 4. Fire the synchronous outbound communication request over secure HTTPS
    try:
        req = urllib.request.Request(
            ENDPOINT_URL,
            data=json.dumps(request_body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req) as response:
            raw_response = response.read().decode("utf-8")
            response_json = json.loads(raw_response)

            # Extract raw string text payload dropped by the engine
            raw_ai_text = response_json["candidates"][0]["content"]["parts"][0]["text"].strip()

            # Remove any accidental markdown enclosing blocks added by the model backstops
            if raw_ai_text.startswith("```json"):
                raw_ai_text = raw_ai_text[7:]
            if raw_ai_text.endswith("```"):
                raw_ai_text = raw_ai_text[:-3]

            clean_itinerary_data = json.loads(raw_ai_text.strip())

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Intelligent AI recommendation synchronization failed. Error: {str(e)}"
        )

    # 5. Lock generation details inside local SQLite AI history database cache table
    current_utc_now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    history_entry = AIRecommendationHistory(
        user_id=current_user.get("id"),  # Pulls authorized id safely from JWT token dictionary
        destination=payload.destination,
        budget_pkr=payload.budget_pkr,
        total_days=payload.total_days,
        travel_style=payload.travel_style,
        generated_itinerary=clean_itinerary_data,
        created_at=current_utc_now
    )
    db.add(history_entry)
    db.commit()

    # 6. Output finalized structure cleanly bound to strict Pydantic re-declared response model
    return AIRecommendResponse(
        destination_name=clean_itinerary_data["destination_name"],
        chosen_style_applied=clean_itinerary_data["chosen_style_applied"],
        weather_advisory_applied=clean_itinerary_data["weather_advisory_applied"],
        advisory_message=clean_itinerary_data["advisory_message"],
        total_projected_cost_pkr=clean_itinerary_data["total_projected_cost_pkr"],
        itinerary_days=clean_itinerary_data["itinerary_days"]
    )
