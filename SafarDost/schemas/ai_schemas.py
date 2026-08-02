from pydantic import BaseModel, Field
from typing import List

class AIRecommendRequest(BaseModel):
    destination: str = Field(..., description="Target city or district query string (e.g., Murree, Swat)")
    budget_pkr: float = Field(..., description="Strict maximum total budget threshold allocation in PKR")
    total_days: int = Field(..., description="Duration of the trip plan itinerary in total days")
    travel_style: str = Field(..., description="Preferred trip category constraint: Adventure, Family, Cultural, or Relaxation")

class DailyItineraryItem(BaseModel):
    time_of_day: str = Field(..., description="Time classification block: Morning, Afternoon, or Evening")
    activity_title: str = Field(..., description="Name of the suggested tourist spot, venue, or activity milestone")
    activity_category: str = Field(..., description="The category classification of the spot (e.g., Viewpoint, Cafe, Museum)")
    estimated_cost_pkr: float = Field(..., description="Projected activity or entry overhead balance cost metric in PKR")
    justification: str = Field(..., description="Explicit context matching explanation based on weather, budget, and travel style")

class DailyPlan(BaseModel):
    day_number: int = Field(..., description="The sequence day count marker for the plan (e.g., Day 1, Day 2)")
    activities: List[DailyItineraryItem] = Field(..., description="Array of validated sequential milestones for this single day")

class AIRecommendResponse(BaseModel):
    destination_name: str = Field(..., description="The synchronized validated geopolitical marker name")
    chosen_style_applied: str = Field(..., description="The profile style layout used to structure this response payload")
    weather_advisory_applied: bool = Field(..., description="Indicates if dynamic climate criteria overrode the user style for safety")
    advisory_message: str = Field(..., description="Contextual safety warning description or positive climate status note")
    total_projected_cost_pkr: float = Field(..., description="Sum total accumulated cost balance of all planned activities")
    itinerary_days: List[DailyPlan] = Field(..., description="The synthesized multi-day itinerary array results")
