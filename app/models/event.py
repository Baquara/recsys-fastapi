from sqlalchemy import Column, Integer, Float
from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, nullable=False, index=True)
    itemId = Column(Integer, nullable=False, index=True)
    rating = Column(Float, nullable=False)
    timestamp = Column(Integer, nullable=False)
