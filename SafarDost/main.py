from fastapi import FastAPI
import models
from database import engine
from routers import auth, places, reviews, hotels, restaurants, weather, ai_recommend
import models.ai_history

app = FastAPI()

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



