# app/core/registry.py

from app.core.metrics import (
    JaccardMetric, 
    DiceMetric, 
    LevenshteinMetric, 
    SpacyVectorMetric
)

class MetricsRegistry:
    def __init__(self):
        self._metrics = {}

    def register(self, metric):
        self._metrics[metric.name] = metric

    def get(self, name):
        return self._metrics.get(name)

    def list(self):
        return [
            {"name": m.name, "description": m.description}
            for m in self._metrics.values()
        ]


# Instanciation du registre et enregistrement des métriques disponibles
registry = MetricsRegistry()

# Métriques Lexicales (Améliorées avec spaCy pour le nettoyage)
registry.register(JaccardMetric())
registry.register(DiceMetric())

# Métrique Morphologique (Caractères)
registry.register(LevenshteinMetric())

# Métrique Sémantique (Vecteurs - Nouveauté Sprint 3)
registry.register(SpacyVectorMetric())