from sqlalchemy import Column, Integer, Float
from app.database import Base


class UserRating(Base):
    __tablename__ = "users"

    # Composite primary key: one rating per (user, item) pair
    userId = Column(Integer, primary_key=True)
    itemId = Column(Integer, primary_key=True)
    rating = Column(Float, nullable=False)
    timestamp = Column(Integer, nullable=False)
