from fastapi import APIRouter, HTTPException, UploadFile, File

from app.core.language_manager import language_manager
from app.models.schemas import SimilarityRequest, SimilarityResponse
from app.services.processor import (
    load_uploaded_json,
    process_minimal_json,
    save_batch_results,
)
from app.services.similarity import compute_similarity_response

router = APIRouter()


@router.get("/languages")
def list_languages():
    """Liste les langues supportées par le service."""
    return {"languages": language_manager.list_languages()}


@router.post("/similarity", response_model=SimilarityResponse)
def similarity(payload: SimilarityRequest):
    try:
        result = compute_similarity_response(
            phrase1=payload.phrase1,
            phrase2=payload.phrase2,
            metric_names=payload.metrics,
            language=payload.language,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return SimilarityResponse(**result)


@router.post("/similarity/upload")
async def upload_and_process_file(file: UploadFile = File(...), language: str = "fr"):
    try:
        filename, data = load_uploaded_json(file.filename, await file.read())
        results = process_minimal_json(data, default_language=language)
        output_filename, _ = save_batch_results(results, filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "Fichier traité et sauvegardé",
        "output_file": output_filename,
        "results": results,
    }
