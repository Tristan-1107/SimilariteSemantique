from app.core.metrics import (
    CamembertMetric,
    DiceMetric,
    JaccardMetric,
    LevenshteinMetric,
    SpacyVectorMetric,
)


class MetricsRegistry:
    def __init__(self):
        self._metrics = {}

    def register(self, metric) -> None:
        """
        Enregistre une métrique après validation.

        En cas de collision de nom, la dernière métrique enregistrée écrase
        la précédente.
        """
        self._validate(metric)
        self._metrics[metric.name] = metric

    def get(self, name):
        return self._metrics.get(name)

    def list(self):
        return [
            {"name": metric.name, "description": metric.description}
            for metric in self._metrics.values()
        ]

    @staticmethod
    def _validate(metric) -> None:
        """Vérifie qu'un plugin respecte le contrat BaseMetric."""
        name = getattr(metric, "name", None)
        if not name or not isinstance(name, str):
            raise ValueError(
                f"Plugin invalide ({type(metric).__name__}) : "
                f"l'attribut 'name' doit être une string non vide."
            )

        if not getattr(metric, "description", None):
            print(f"AVERTISSEMENT: Le plugin '{name}' n'a pas de description.")

        if not callable(getattr(metric, "compute", None)):
            raise ValueError(
                f"Plugin invalide ('{name}') : "
                f"la méthode 'compute' est absente ou non callable."
            )


registry = MetricsRegistry()

registry.register(JaccardMetric())
registry.register(DiceMetric())
registry.register(LevenshteinMetric())
registry.register(SpacyVectorMetric())
registry.register(CamembertMetric())
