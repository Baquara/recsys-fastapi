from typing import List
from pydantic import BaseModel, Field


class UserRatingCreate(BaseModel):
    userId: int = Field(..., example=7, description="Unique identifier for the user")
    itemId: int = Field(..., example=42, description="Unique identifier for the rated item")
    rating: float = Field(..., ge=0, le=5, example=4.5, description="Rating score from 0 to 5")
    timestamp: int = Field(..., example=1716300000, description="Unix timestamp of the rating event")


class UserRatingUpdate(BaseModel):
    itemId: int = Field(..., example=42, description="Item being re-rated")
    rating: float = Field(..., ge=0, le=5, example=3.0)
    timestamp: int = Field(..., example=1716300000)


class UserRatingRead(BaseModel):
    userId: int
    itemId: int
    rating: float
    timestamp: int

    model_config = {"from_attributes": True}


class UserRatingsPayload(BaseModel):
    items: List[UserRatingCreate] = Field(..., description="Batch of user–item ratings to insert")

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {"userId": 7, "itemId": 1, "rating": 4.5, "timestamp": 1716300000},
                    {"userId": 7, "itemId": 2, "rating": 3.0, "timestamp": 1716300001},
                ]
            }
        }
    }


class UserRatingsUpdatePayload(BaseModel):
    items: List[UserRatingUpdate] = Field(..., description="Ratings to update for the given user")
