from database import Base  # Crucial: Import the central Base class first

# Explicitly load every single table file so SQLAlchemy discovers them
from .user import Users
from .hotel import Hotels
from .restaurant import Restaurants
from .place import Places
from .review import Reviews