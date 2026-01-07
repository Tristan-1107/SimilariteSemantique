# tests/test_metrics.py

# Pour lancer ce pgm, se placer dans le repertoire racine "SimilariteSemantique" et exécuter la commande "python3 -m tests.testMetrics"

from app.core.metrics import jaccard_similarity, JaccardMetric

def test_jaccard_math():
    # Cas simple : "a b" et "a c" -> intersection="a", union="a b c" -> 1/3
    tokens1 = ["a", "b"]
    tokens2 = ["a", "c"]
    assert jaccard_similarity(tokens1, tokens2) == 1/3
    print("Test Jaccard maths, ok.")

def test_jaccard_identical():
    # Identiques -> 1.0
    tokens = ["test", "unitaire"]
    assert jaccard_similarity(tokens, tokens) == 1.0
    print("Test Jaccard identique, ok.")

def test_jaccard_empty():
    # Vide -> 0.0 ou 1.0 selon la logique (ici le code dit 1.0 si les deux sont vides)
    assert jaccard_similarity([], []) == 1.0
    assert jaccard_similarity(["a"], []) == 0.0
    print("Test Jaccard phrase vide, ok.")
    

def test_jaccard_metric_class():
    metric = JaccardMetric()
    result = metric.compute("Bonjour le monde", "Bonjour tout le monde")
    assert result.name == "jaccard"
    assert 0 < result.score < 1
    print("Test global pour deux phrases différentes, ok.")

test_jaccard_math()

test_jaccard_identical()

test_jaccard_empty()

test_jaccard_metric_class()