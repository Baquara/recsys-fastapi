import json
from typing import List
from pydantic import BaseModel, Field, field_validator


class ItemCreate(BaseModel):
    itemId: int = Field(..., example=1, description="Unique integer identifier for the item")
    title: str = Field(..., example="Inception", description="Display name shown to users")
    description: str = Field(
        ...,
        example="A mind-bending thriller about dreams within dreams.",
        description="Full-text description used by the content-based recommender (TF-IDF input)",
    )
    tag: List[str] = Field(
        ...,
        example=["sci-fi", "thriller"],
        description="Labels/genres combined with description for content similarity scoring",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "itemId": 1,
                "title": "Inception",
                "description": "A mind-bending thriller about dreams within dreams.",
                "tag": ["sci-fi", "thriller", "christopher-nolan"],
            }
        }
    }


class ItemUpdate(BaseModel):
    title: str = Field(..., example="Inception")
    description: str = Field(..., example="A mind-bending thriller about dreams within dreams.")
    tag: List[str] = Field(..., example=["sci-fi", "thriller"])


class ItemRead(BaseModel):
    itemId: int
    title: str
    description: str
    tag: List[str]

    model_config = {"from_attributes": True}

    @field_validator("tag", mode="before")
    @classmethod
    def parse_tag(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


class ItemBatchCreate(BaseModel):
    items: List[ItemCreate] = Field(..., description="Batch of items to insert into the catalogue")

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {
                        "itemId": 1,
                        "title": "Inception",
                        "description": "A mind-bending thriller about dreams within dreams.",
                        "tag": ["sci-fi", "thriller"],
                    },
                    {
                        "itemId": 2,
                        "title": "The Matrix",
                        "description": "A hacker discovers reality is a simulation.",
                        "tag": ["sci-fi", "action", "cyberpunk"],
                    },
                ]
            }
        }
    }
