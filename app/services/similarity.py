from app.core.language_manager import LanguageContext, language_manager
from app.core.registry import registry


def list_available_metrics() -> list[dict]:
    return sorted(registry.list(), key=lambda metric: metric["name"])


def list_available_languages() -> list[dict]:
    return sorted(
        language_manager.list_languages(),
        key=lambda language: language["code"],
    )


def compute_scores_for_context(
    phrase1: str,
    phrase2: str,
    metric_names: list[str],
    context: LanguageContext,
) -> dict[str, float]:
    scores = {}
    for metric_name in metric_names:
        metric = registry.get(metric_name)
        if metric is None:
            raise ValueError(f"Unknown metric: {metric_name}")

        result = metric.compute(phrase1, phrase2, context)
        scores[metric_name] = result.score

    return scores


def compute_similarity_response(
    phrase1: str,
    phrase2: str,
    metric_names: list[str],
    language: str = "fr",
) -> dict:
    context = language_manager.get_context(language)
    scores = compute_scores_for_context(phrase1, phrase2, metric_names, context)

    return {
        "scores": scores,
        "metadata": {
            "selected_metrics": metric_names,
            "language": context.config.code,
        },
    }
