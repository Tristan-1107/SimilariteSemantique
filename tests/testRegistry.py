# tests/test_registry.py
# Pour lancer ce pgm, se placer dans le repertoire racine "SimilariteSemantique" et exécuter la commande "python3 -m tests.testRegistry"

from app.core.registry import registry, MetricsRegistry
from app.core.metrics import JaccardMetric

# Vérifie que la métrique Jaccard est bien enregistrée par défaut et que le système de récupération fonctionne.
def test_registry_contains_jaccard():
    # Vérifie que l'instance globale 'registry' a bien chargé Jaccard
    metric = registry.get("jaccard")
    assert metric is not None
    assert isinstance(metric, JaccardMetric)
    print("L'instance globale 'registry' a bien chargé Jaccard.")

def test_registry_unknown_metric():
    # Vérifie qu'une métrique inexistante renvoie None
    assert registry.get("cosinus_inconnu") is None
    print("Une métrique inexistance renvoie bien None.")

test_registry_contains_jaccard()

test_registry_unknown_metric()