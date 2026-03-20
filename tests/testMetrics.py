# tests/testMetrics.py
import pytest
from unittest.mock import MagicMock

import app.core.metrics as metrics_module
from app.core.metrics import JaccardMetric, DiceMetric, LevenshteinMetric, SpacyVectorMetric, CamembertMetric
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


def test_camembert_metric_with_mocked_model(monkeypatch, fr_context):
    class DummyEmbeddings:
        shape = (2, 3)

        def __getitem__(self, index):
            return [index]

    class DummyModel:
        def encode(self, texts, convert_to_tensor=True):
            assert len(texts) == 2
            return DummyEmbeddings()

    class DummyScore:
        def item(self):
            return 0.75

    monkeypatch.setattr(metrics_module, "get_bert_model", lambda: DummyModel())
    monkeypatch.setattr(
        metrics_module,
        "util",
        MagicMock(cos_sim=lambda left, right: DummyScore()),
    )

    result = CamembertMetric().compute("bonjour", "salut", fr_context)

    assert result.score == 0.75
    assert result.detail["model"] == metrics_module.CAMEMBERT_MODEL_NAME
