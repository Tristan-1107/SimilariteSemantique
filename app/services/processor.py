from app.core.language_manager import language_manager
from app.core.registry import registry


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

        scores = {}
        for name in selected_metrics:
            metric = registry.get(name)
            result = metric.compute(p1, p2, context)
            scores[name] = result.score

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
