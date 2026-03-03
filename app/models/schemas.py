# app/models/schemas.py
from pydantic import BaseModel, Field


class SimilarityRequest(BaseModel):
    phrase1: str = Field(..., min_length=0)
    phrase2: str = Field(..., min_length=0)
    metrics: list[str] = Field(default_factory=lambda: ["jaccard"])
    language: str = Field(default="fr", description="Code langue ISO 639-1 (ex: 'fr', 'en')")


class SimilarityResponse(BaseModel):
    scores: dict[str, float]
    metadata: dict = Field(default_factory=dict)