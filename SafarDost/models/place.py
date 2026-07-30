from database import Base
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship


class Places(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    category = Column(String)     # e.g., "Lake", "Fort", "Valley"
    description = Column(Text)
    image = Column(String)

    # Relational link: Connects a tourist place to its incoming reviews
    reviews = relationship("Reviews", back_populates="place")