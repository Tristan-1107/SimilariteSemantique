# app/models/schemas.py
from pydantic import BaseModel, Field


class SimilarityRequest(BaseModel):
    phrase1: str = Field(..., min_length=0)
    phrase2: str = Field(..., min_length=0)
    metrics: list[str] = Field(default_factory=lambda: ["jaccard"])


class SimilarityResponse(BaseModel):
    scores: dict[str, float]
    metadata: dict = Field(default_factory=dict)
