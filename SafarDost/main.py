from fastapi import FastAPI
import models
from database import engine
from routers import auth, places, reviews, hotels, restaurants, weather, ai_recommend

# Initialize your core app service cleanly
app = FastAPI(
    title="Safardost API Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None
)

models.Base.metadata.create_all(bind=engine)

@app.get("/")
def first_api():
    return {"Hello": "World"}

app.include_router(auth.router)
app.include_router(places.router)
app.include_router(hotels.router)
app.include_router(restaurants.router)
app.include_router(reviews.router)
app.include_router(weather.router)
app.include_router(ai_recommend.router)



