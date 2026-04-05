import json
import os
import re
from pathlib import Path

from app.core.language_manager import language_manager
from app.core.loader_utils import PROJECT_ROOT
from app.core.registry import registry
from app.services.similarity import compute_scores_for_context


SAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
RESULT_FILENAME_PATTERN = re.compile(r"^result_[A-Za-z0-9][A-Za-z0-9._-]*\.json$")


def _parse_batch_payload(data, default_language: str) -> tuple[list[str], list[list[str]], str]:
    if isinstance(data, dict):
        metrics = data.get("metrics")
        pairs = data.get("pairs")
        language = data.get("language", default_language)
    elif isinstance(data, list):
        if len(data) < 2:
            raise ValueError("Format invalide. Besoin des métriques et d'au moins un couple.")
        metrics = data[0]
        pairs = data[1:]
        language = default_language
    else:
        raise ValueError("Format JSON invalide. Attendu: liste ou objet JSON.")

    if not isinstance(metrics, list) or not metrics or not all(isinstance(name, str) for name in metrics):
        raise ValueError("Le champ 'metrics' doit être une liste non vide de chaînes.")

    if not isinstance(pairs, list) or not pairs:
        raise ValueError("Le champ 'pairs' doit contenir au moins un couple de phrases.")

    return metrics, pairs, language


def get_data_dir() -> Path:
    return Path(os.environ.get("SIMILARITY_DATA_DIR", PROJECT_ROOT / "data"))


def load_uploaded_json(filename: str | None, content: bytes) -> tuple[str, object]:
    normalized_filename = normalize_upload_filename(filename)

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON invalide: {e.msg}") from e

    return normalized_filename, data


def save_batch_results(results: dict, source_filename: str) -> tuple[str, Path]:
    output_dir = get_data_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    output_filename = f"result_{normalize_upload_filename(source_filename)}"
    output_path = output_dir / output_filename
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=4, ensure_ascii=False)

    return output_filename, output_path


def validate_result_filename(filename: str) -> str:
    candidate = Path(filename).name
    if candidate != filename or not RESULT_FILENAME_PATTERN.fullmatch(candidate):
        raise ValueError("Nom de fichier invalide.")

    return candidate


def normalize_upload_filename(filename: str | None) -> str:
    candidate = Path(filename or "").name
    if not candidate.lower().endswith(".json"):
        raise ValueError("Seuls les fichiers .json sont acceptés")

    stem = Path(candidate).stem
    safe_stem = SAFE_FILENAME_CHARS.sub("_", stem).strip("._-")
    if not safe_stem:
        safe_stem = "upload"

    return f"{safe_stem}.json"


def process_minimal_json(data, default_language: str = "fr"):
    selected_metrics, pairs, language = _parse_batch_payload(data, default_language)

    unknown_metrics = [name for name in selected_metrics if registry.get(name) is None]
    if unknown_metrics:
        raise ValueError(f"Unknown metric(s): {', '.join(unknown_metrics)}")

    context = language_manager.get_context(language)
    batch_results = []

    for index, pair in enumerate(pairs, start=1):
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError(f"Couple invalide à l'index {index}: chaque entrée doit contenir exactement 2 phrases.")

        p1, p2 = pair
        if not isinstance(p1, str) or not isinstance(p2, str):
            raise ValueError(f"Couple invalide à l'index {index}: les phrases doivent être des chaînes.")

        scores = compute_scores_for_context(p1, p2, selected_metrics, context)

        batch_results.append({
            "p1": p1,
            "p2": p2,
            "scores": scores,
        })

    return {
        "results": batch_results,
        "metadata": {
            "selected_metrics": selected_metrics,
            "language": context.config.code,
        },
    }
