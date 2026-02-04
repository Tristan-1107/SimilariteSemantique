# app/api/endpoints.py
import os
import json

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi import Body

from app.core.registry import registry
from app.models.schemas import SimilarityRequest, SimilarityResponse
from app.services.processor import process_minimal_json

router = APIRouter()

# --- Route de base (avant Sprint 3) ---
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




# --- Nouvelle route : traitement du json + création du json de sortie (Sprint 3) ---
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)


@router.post("/similarity/upload")
async def upload_and_process_file(file: UploadFile = File(...)):
    # Vérifier que c'est bien un JSON
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers .json sont acceptés")

    try:
        # Lecture des données
        content = await file.read()
        data = json.loads(content)
        results = process_minimal_json(data)

        # Création du fichier et affichage dans l'API
        output_filename = f"result_{file.filename}"
        output_path = os.path.join(DATA_DIR, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

        return {
            "message": "Fichier traité et sauvegardé",
            "output_file": output_filename,
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement : {str(e)}")