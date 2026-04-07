from fastapi import APIRouter, HTTPException, UploadFile, File

from app.core.language_manager import language_manager
from app.models.schemas import SimilarityRequest, SimilarityResponse
from app.services.processor import (
    load_uploaded_json,
    process_minimal_json,
    save_batch_results,
)
from app.services.similarity import (
    compute_similarity_response,
    list_available_languages,
    list_available_metrics,
)

router = APIRouter()


def _api_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "code": code,
            "message": message,
        },
    )


def _translate_similarity_value_error(message: str) -> HTTPException:
    if message.startswith("Langue non supportée"):
        return _api_error(400, "unsupported_language", message)

    if message.startswith("Unknown metric: "):
        metric_name = message.split(": ", 1)[1]
        return _api_error(400, "unknown_metric", f"Métrique inconnue : {metric_name}")

    return _api_error(400, "invalid_request", message)


def _translate_upload_value_error(message: str) -> HTTPException:
    if message == "Seuls les fichiers .json sont acceptés":
        return _api_error(400, "invalid_file_type", message)

    if message.startswith("JSON invalide"):
        normalized = message.replace("JSON invalide:", "JSON invalide :", 1)
        return _api_error(400, "invalid_json", normalized)

    return _api_error(400, "invalid_request", message)


@router.get("/languages")
def list_languages():
    """Liste les langues supportées par le service."""
    return {
        "languages": sorted(
            language_manager.list_languages(),
            key=lambda language: language["code"],
        )
    }


@router.get("/metrics")
def list_metrics():
    """Liste les métriques actuellement enregistrées dans le service."""
    return {"metrics": list_available_metrics()}


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
        raise _translate_similarity_value_error(str(e))
    except RuntimeError as e:
        raise _api_error(500, "metric_runtime_error", str(e))

    return SimilarityResponse(**result)


@router.post("/similarity/upload")
async def upload_and_process_file(file: UploadFile = File(...), language: str = "fr"):
    try:
        filename, data = load_uploaded_json(file.filename, await file.read())
        results = process_minimal_json(data, default_language=language)
        output_filename, _ = save_batch_results(results, filename)
    except ValueError as e:
        raise _translate_upload_value_error(str(e))
    except RuntimeError as e:
        raise _api_error(500, "processing_error", str(e))

    return {
        "message": "Fichier traité et sauvegardé",
        "output_file": output_filename,
        "results": results,
    }
