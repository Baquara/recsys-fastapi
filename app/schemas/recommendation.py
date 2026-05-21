from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CollaborativeResult(BaseModel):
    execution_time: Dict[str, float] = Field(
        ..., description="Breakdown of time spent in data processing vs. KNN inference (seconds)"
    )
    recommendations: List[Dict[str, Any]] = Field(
        ..., description="Ranked items — each entry contains item metadata, `rank`, and cosine `distance`"
    )


class ContentBasedResult(BaseModel):
    item_index: int = Field(..., description="Row index of the target item used as query")
    api_exec_time: str = Field(..., description="Total endpoint execution time in seconds")
    items: List[Dict[str, Any]] = Field(
        ..., description="Similar items ordered by TF-IDF cosine similarity score"
    )


class SystemInfo(BaseModel):
    uptime: str
    total_ram_mb: str
    available_ram_mb: str
    cpu_model: str
    cpu_clock_mhz: str
    database_size: str
