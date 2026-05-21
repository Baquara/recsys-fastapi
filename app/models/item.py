from sqlalchemy import Column, Integer, String, Text
from app.database import Base


class Item(Base):
    __tablename__ = "items"

    itemId = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    tag = Column(Text, nullable=False)  # stored as JSON-encoded list
