import sys
from types import SimpleNamespace

from app.core.language_manager import language_manager
from app.core.model_registry import model_registry
from app.core.registry import registry


def test_english_language_plugin_is_registered():
    codes = {language["code"] for language in language_manager.list_languages()}
    assert "en" in codes


def test_bert_score_model_plugin_is_registered():
    assert model_registry.get_definition("bert_score_english") is not None
    assert model_registry.get_definition("bert_score_french") is not None


def test_french_language_uses_registered_bert_score_model():
    context = language_manager.get_context("fr")

    assert context.config.embedding_model == "bert_score_french"


def test_bert_score_metric_plugin_is_registered():
    metric = registry.get("bert_score")
    assert metric is not None
    assert metric.name == "bert_score"


def test_bert_score_metric_computes_f1_with_mocked_model(monkeypatch):
    metric = registry.get("bert_score")
    plugin_module = sys.modules[metric.__class__.__module__]

    class DummyTensor:
        def __init__(self, rows):
            self.rows = rows
            self.shape = (len(rows), len(rows[0]) if rows else 0)

        def __getitem__(self, mask):
            if isinstance(mask, DummyMask):
                return DummyTensor([row for row, keep in zip(self.rows, mask.values) if keep])
            return self.rows[mask]

        def __matmul__(self, other):
            matrix = []
            for left in self.rows:
                matrix.append([sum(a * b for a, b in zip(left, right)) for right in other.rows])
            return DummyMatrix(matrix)

        @property
        def T(self):
            columns = list(zip(*self.rows))
            return DummyTensor([list(column) for column in columns])

    class DummyMask:
        def __init__(self, values):
            self.values = values

        def bool(self):
            return self

        def __invert__(self):
            return DummyMask([not value for value in self.values])

        def __and__(self, other):
            return DummyMask([left and right for left, right in zip(self.values, other.values)])

    class DummyValue:
        def __init__(self, value):
            self._value = value

        def item(self):
            return self._value

    class DummyVector:
        def __init__(self, values):
            self.values = values

        def mean(self):
            return DummyValue(sum(self.values) / len(self.values))

    class DummyMatrix:
        def __init__(self, values):
            self.values = values

        def max(self, dim):
            if dim == 1:
                maxima = [max(row) for row in self.values]
            else:
                maxima = [max(column) for column in zip(*self.values)]
            return SimpleNamespace(values=DummyVector(maxima))

    class DummyNoGrad:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class DummyTokenizer:
        def __call__(self, text, **kwargs):
            return {
                "input_ids": [[101, 200, 201, 102]],
                "attention_mask": [DummyMask([True, True, True, True])],
                "special_tokens_mask": [DummyMask([True, False, False, True])],
            }

    class DummyModel:
        def __call__(self, **kwargs):
            return SimpleNamespace(
                last_hidden_state=[
                    DummyTensor(
                        [
                            [0.0, 0.0],
                            [1.0, 0.0],
                            [0.8, 0.6],
                            [0.0, 0.0],
                        ]
                    )
                ]
            )

    dummy_resource = SimpleNamespace(
        model_name="bert-base-uncased",
        tokenizer=DummyTokenizer(),
        model=DummyModel(),
        torch=SimpleNamespace(
            no_grad=lambda: DummyNoGrad(),
            nn=SimpleNamespace(
                functional=SimpleNamespace(normalize=lambda tensor, p, dim: tensor)
            ),
        ),
    )

    monkeypatch.setattr(
        plugin_module,
        "model_registry",
        SimpleNamespace(
            get_definition=lambda name: {"name": name},
            get=lambda name: dummy_resource,
        ),
    )

    context = language_manager.get_context("en")
    result = metric.compute("hello world", "hello there", context)

    assert 0.0 <= result.score <= 1.0
    assert result.score == result.detail["f1"]
    assert "precision" in result.detail
    assert "recall" in result.detail


def test_bert_score_metric_uses_french_model_when_language_is_fr(monkeypatch):
    metric = registry.get("bert_score")
    plugin_module = sys.modules[metric.__class__.__module__]
    requested_models = []

    class DummyTensor:
        def __init__(self, rows):
            self.rows = rows
            self.shape = (len(rows), len(rows[0]) if rows else 0)

        def __getitem__(self, mask):
            return DummyTensor([row for row, keep in zip(self.rows, mask.values) if keep])

        def __matmul__(self, other):
            matrix = []
            for left in self.rows:
                matrix.append([sum(a * b for a, b in zip(left, right)) for right in other.rows])
            return DummyMatrix(matrix)

        @property
        def T(self):
            columns = list(zip(*self.rows))
            return DummyTensor([list(column) for column in columns])

    class DummyMask:
        def __init__(self, values):
            self.values = values

        def bool(self):
            return self

        def __invert__(self):
            return DummyMask([not value for value in self.values])

        def __and__(self, other):
            return DummyMask([left and right for left, right in zip(self.values, other.values)])

    class DummyValue:
        def __init__(self, value):
            self._value = value

        def item(self):
            return self._value

    class DummyVector:
        def __init__(self, values):
            self.values = values

        def mean(self):
            return DummyValue(sum(self.values) / len(self.values))

    class DummyMatrix:
        def __init__(self, values):
            self.values = values

        def max(self, dim):
            if dim == 1:
                maxima = [max(row) for row in self.values]
            else:
                maxima = [max(column) for column in zip(*self.values)]
            return SimpleNamespace(values=DummyVector(maxima))

    class DummyNoGrad:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class DummyTokenizer:
        def __call__(self, text, **kwargs):
            return {
                "input_ids": [[101, 200, 201, 102]],
                "attention_mask": [DummyMask([True, True, True, True])],
                "special_tokens_mask": [DummyMask([True, False, False, True])],
            }

    class DummyModel:
        def __call__(self, **kwargs):
            return SimpleNamespace(
                last_hidden_state=[
                    DummyTensor(
                        [
                            [0.0, 0.0],
                            [1.0, 0.0],
                            [0.8, 0.6],
                            [0.0, 0.0],
                        ]
                    )
                ]
            )

    dummy_resource = SimpleNamespace(
        model_name="camembert-base",
        tokenizer=DummyTokenizer(),
        model=DummyModel(),
        torch=SimpleNamespace(
            no_grad=lambda: DummyNoGrad(),
            nn=SimpleNamespace(
                functional=SimpleNamespace(normalize=lambda tensor, p, dim: tensor)
            ),
        ),
    )

    def fake_get_definition(name):
        if name == "bert_score_french":
            return {"name": name}
        return None

    def fake_get(name):
        requested_models.append(name)
        return dummy_resource

    monkeypatch.setattr(
        plugin_module,
        "model_registry",
        SimpleNamespace(
            get_definition=fake_get_definition,
            get=fake_get,
        ),
    )

    context = language_manager.get_context("fr")
    result = metric.compute("bonjour monde", "salut monde", context)

    assert requested_models == ["bert_score_french"]
    assert 0.0 <= result.score <= 1.0
