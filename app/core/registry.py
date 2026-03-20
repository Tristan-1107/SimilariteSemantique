# app/core/registry.py

from app.core.metrics import (
    JaccardMetric,
    DiceMetric,
    LevenshteinMetric,
    SpacyVectorMetric,
    CamembertMetric,
)


class MetricsRegistry:

    def __init__(self):
        self._metrics = {}

    def register(self, metric) -> None:
        """
        Enregistre une métrique après validation.
        Lève une ValueError explicite si le plugin est mal formé.
        Cela garantit qu'un plugin invalide fait crasher le démarrage,
        pas une requête utilisateur.
        """
        self._validate(metric)
        self._metrics[metric.name] = metric

    def get(self, name):
        return self._metrics.get(name)

    def list(self):
        return [
            {"name": m.name, "description": m.description}
            for m in self._metrics.values()
        ]

    @staticmethod
    def _validate(metric) -> None:
        """Vérifie qu'un plugin respecte le contrat BaseMetric."""

        # 1. name doit être une string non vide
        name = getattr(metric, "name", None)
        if not name or not isinstance(name, str):
            raise ValueError(
                f"Plugin invalide ({type(metric).__name__}) : "
                f"l'attribut 'name' doit être une string non vide."
            )

        # 2. description recommandée
        if not getattr(metric, "description", None):
            print(
                f"AVERTISSEMENT: Le plugin '{name}' n'a pas de description."
            )

        # 3. compute doit être callable
        if not callable(getattr(metric, "compute", None)):
            raise ValueError(
                f"Plugin invalide ('{name}') : "
                f"la méthode 'compute' est absente ou non callable."
            )


# Instance globale
registry = MetricsRegistry()

# Métriques natives (core)
registry.register(JaccardMetric())
registry.register(DiceMetric())
registry.register(LevenshteinMetric())
registry.register(SpacyVectorMetric())
registry.register(CamembertMetric())
