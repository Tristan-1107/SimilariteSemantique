# app/api/endpoints.py
from fastapi import APIRouter, HTTPException

from app.core.registry import registry
from app.core.language_manager import language_manager
from app.models.schemas import SimilarityRequest, SimilarityResponse

router = APIRouter()


@router.get("/languages")
def list_languages():
    """Liste les langues supportées par le service."""
    return {"languages": language_manager.list_languages()}


@router.post("/similarity", response_model=SimilarityResponse)
def similarity(payload: SimilarityRequest):

    # Résolution du contexte linguistique (valide la langue, charge le pipeline si besoin)
    try:
        context = language_manager.get_context(payload.language)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    scores = {}
    for metric_name in payload.metrics:
        metric = registry.get(metric_name)
        if not metric:
            raise HTTPException(status_code=400, detail=f"Unknown metric: {metric_name}")

        result = metric.compute(payload.phrase1, payload.phrase2, context)
        scores[metric_name] = result.score

    return SimilarityResponse(
        scores=scores,
        metadata={
            "selected_metrics": payload.metrics,
            "language": context.config.code,
        },
    )