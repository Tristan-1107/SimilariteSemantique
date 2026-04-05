# app/api/endpoints.py
import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.core.registry import registry
from app.core.language_manager import language_manager
from app.models.schemas import SimilarityRequest, SimilarityResponse
from app.services.processor import process_minimal_json

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _get_data_dir() -> Path:
    return Path(os.environ.get("SIMILARITY_DATA_DIR", PROJECT_ROOT / "data"))


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

        try:
            result = metric.compute(payload.phrase1, payload.phrase2, context)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))
        scores[metric_name] = result.score

    return SimilarityResponse(
        scores=scores,
        metadata={
            "selected_metrics": payload.metrics,
            "language": context.config.code,
        },
    )


@router.post("/similarity/upload")
async def upload_and_process_file(file: UploadFile = File(...), language: str = "fr"):
    filename = Path(file.filename or "").name
    if not filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers .json sont acceptés")

    try:
        content = await file.read()
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON invalide: {e.msg}")

    try:
        results = process_minimal_json(data, default_language=language)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    output_dir = _get_data_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    output_filename = f"result_{filename}"
    output_path = output_dir / output_filename
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    return {
        "message": "Fichier traité et sauvegardé",
        "output_file": output_filename,
        "results": results,
    }
