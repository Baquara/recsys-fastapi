from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    userId: int = Field(..., example=7)
    itemId: int = Field(..., example=42)
    rating: float = Field(..., example=1.0, description="Implicit signal strength (e.g. 1 = clicked, 5 = purchased)")
    timestamp: int = Field(..., example=1716300000)

    model_config = {
        "json_schema_extra": {
            "example": {"userId": 7, "itemId": 42, "rating": 1.0, "timestamp": 1716300000}
        }
    }


class EventRead(BaseModel):
    id: int
    userId: int
    itemId: int
    rating: float
    timestamp: int

    model_config = {"from_attributes": True}
