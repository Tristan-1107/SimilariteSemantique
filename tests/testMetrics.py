# tests/testMetrics.py
import pytest
from unittest.mock import MagicMock

from app.core.metrics import JaccardMetric, DiceMetric, LevenshteinMetric, SpacyVectorMetric
from app.core.language_manager import language_manager


# On utilise le vrai context français pour tous les tests
@pytest.fixture(scope="module")
def fr_context():
    return language_manager.get_context("fr")


def test_jaccard_identical(fr_context):
    result = JaccardMetric().compute("le chat mange", "le chat mange", fr_context)
    assert result.score == 1.0

def test_jaccard_disjoint(fr_context):
    result = JaccardMetric().compute("chat", "voiture", fr_context)
    assert result.score == 0.0

def test_dice_identical(fr_context):
    result = DiceMetric().compute("bonjour monde", "bonjour monde", fr_context)
    assert result.score == 1.0

def test_levenshtein_identical(fr_context):
    # Levenshtein n'utilise pas le pipeline, on passe fr_context par cohérence
    result = LevenshteinMetric().compute("bonjour", "bonjour", fr_context)
    assert result.score == 1.0

def test_levenshtein_range(fr_context):
    result = LevenshteinMetric().compute("chat", "chien", fr_context)
    assert 0.0 <= result.score <= 1.0

def test_scores_in_range(fr_context):
    phrases = [("je mange une pomme", "il dévore une poire")]
    for p1, p2 in phrases:
        for metric in [JaccardMetric(), DiceMetric(), LevenshteinMetric()]:
            r = metric.compute(p1, p2, fr_context)
            assert 0.0 <= r.score <= 1.0, f"{metric.name} hors bornes"