"""
Gabarit de plugin de metrique.

Ce fichier est volontairement prefixe par "_" pour etre ignore par le loader.
Copiez-le sous un autre nom (sans "_") puis completez la classe.
"""

from app.core.metrics import BaseMetric, MetricResult


class ExampleMetric(BaseMetric):
    # Nom unique de la metrique tel qu'il apparaitra dans l'API.
    name = ""
    # Courte description lisible par un humain.
    description = ""

    def compute(self, phrase1, phrase2, context) -> MetricResult:
        # Retourner un MetricResult avec au minimum un score float.
        raise NotImplementedError("Remplacez ce gabarit par votre logique de calcul.")
