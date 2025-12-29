# app/api/endpoints.py
from fastapi import APIRouter, HTTPException

from app.core.registry import registry
from app.models.schemas import SimilarityRequest, SimilarityResponse

router = APIRouter()


@router.post("/similarity", response_model=SimilarityResponse)
def similarity(payload: SimilarityRequest):
    scores = {}

    for metric_name in payload.metrics:
        metric = registry.get(metric_name)
        if not metric:
            raise HTTPException(status_code=400, detail=f"Unknown metric: {metric_name}")
        result = metric.compute(payload.phrase1, payload.phrase2)
        scores[metric_name] = result.score

    return SimilarityResponse(scores=scores, metadata={"selected_metrics": payload.metrics})
