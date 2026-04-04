from unittest.mock import MagicMock

import pytest

import app.core.metrics as metrics_module
import app.core.model_definition as model_definition_module
from app.core.language_manager import language_manager
from app.core.metrics import (
    CamembertMetric,
    DiceMetric,
    JaccardMetric,
    LevenshteinMetric,
)
from app.core.model_definition import SentenceTransformerModelDefinition
from app.core.model_registry import CAMEMBERT_MODEL_NAME, ModelRegistry


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
    result = LevenshteinMetric().compute("bonjour", "bonjour", fr_context)
    assert result.score == 1.0


def test_levenshtein_range(fr_context):
    result = LevenshteinMetric().compute("chat", "chien", fr_context)
    assert 0.0 <= result.score <= 1.0


def test_scores_in_range(fr_context):
    phrases = [("je mange une pomme", "il dévore une poire")]
    for p1, p2 in phrases:
        for metric in [JaccardMetric(), DiceMetric(), LevenshteinMetric()]:
            result = metric.compute(p1, p2, fr_context)
            assert 0.0 <= result.score <= 1.0, f"{metric.name} hors bornes"


def test_camembert_metric_with_mocked_model_registry(monkeypatch, fr_context):
    class DummyEmbeddings:
        shape = (2, 3)

        def __getitem__(self, index):
            return [index]

    class DummyModel:
        def encode(self, texts, convert_to_tensor=True):
            assert len(texts) == 2
            assert convert_to_tensor is True
            return DummyEmbeddings()

    class DummyScore:
        def item(self):
            return 0.75

    dummy_resource = type(
        "DummyResource",
        (),
        {
            "model_name": CAMEMBERT_MODEL_NAME,
            "encoder": DummyModel(),
            "util": MagicMock(cos_sim=lambda left, right: DummyScore()),
        },
    )()

    monkeypatch.setattr(
        metrics_module,
        "model_registry",
        type("InlineRegistry", (), {"get": lambda self, name: dummy_resource})(),
    )

    result = CamembertMetric().compute("bonjour", "salut", fr_context)

    assert result.score == 0.75
    assert result.detail["model"] == CAMEMBERT_MODEL_NAME
    assert result.detail["vector_dim"] == 3


@pytest.mark.parametrize(
    ("raw_score", "expected_score"),
    [(1.7, 1.0), (-0.3, 0.0)],
)
def test_camembert_metric_clamps_score_to_unit_interval(
    monkeypatch,
    fr_context,
    raw_score,
    expected_score,
):
    class DummyEmbeddings:
        shape = (2, 2)

        def __getitem__(self, index):
            return [index]

    class DummyModel:
        def encode(self, texts, convert_to_tensor=True):
            return DummyEmbeddings()

    class DummyScore:
        def item(self):
            return raw_score

    dummy_resource = type(
        "DummyResource",
        (),
        {
            "model_name": CAMEMBERT_MODEL_NAME,
            "encoder": DummyModel(),
            "util": MagicMock(cos_sim=lambda left, right: DummyScore()),
        },
    )()

    monkeypatch.setattr(
        metrics_module,
        "model_registry",
        type("InlineRegistry", (), {"get": lambda self, name: dummy_resource})(),
    )

    result = CamembertMetric().compute("bonjour", "salut", fr_context)

    assert result.score == expected_score
    assert 0.0 <= result.score <= 1.0


def test_camembert_metric_raises_runtime_error_without_sentence_transformers(
    monkeypatch,
    fr_context,
):
    local_registry = ModelRegistry()
    local_registry.register(
        SentenceTransformerModelDefinition(
            name=CAMEMBERT_MODEL_NAME,
            model_name=CAMEMBERT_MODEL_NAME,
            description="Definition de test",
        )
    )

    original_import_module = model_definition_module.importlib.import_module

    def fake_import_module(name: str):
        if name == "sentence_transformers":
            raise ImportError("No module named 'sentence_transformers'")
        return original_import_module(name)

    monkeypatch.setattr(
        model_definition_module.importlib,
        "import_module",
        fake_import_module,
    )
    monkeypatch.setattr(metrics_module, "model_registry", local_registry)

    with pytest.raises(RuntimeError, match="sentence-transformers"):
        CamembertMetric().compute("bonjour", "salut", fr_context)
