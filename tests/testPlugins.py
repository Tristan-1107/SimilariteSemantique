# tests/testPlugins.py
import pytest
from pathlib import Path

from app.core.registry import registry
from app.core.language_manager import language_manager
from app.core.plugin_loader import load_plugins, _resolve_plugins_path

# On charge les plugins une seule fois pour tous les tests du module
@pytest.fixture(scope="module", autouse=True)
def load():
    load_plugins("plugins/metrics")

@pytest.fixture(scope="module")
def ctx():
    return language_manager.get_context("fr")


def test_plugins_path_resolution_is_stable(monkeypatch):
    project_root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(project_root / "tests")

    resolved = _resolve_plugins_path("plugins/metrics")

    assert resolved == (project_root / "plugins" / "metrics").resolve()
    assert resolved.is_dir()


# --- Présence dans le registre ---

def test_plugins_registered():
    names = [m["name"] for m in registry.list()]
    assert "word_overlap"    in names
    assert "length_ratio"    in names
    assert "prefix"          in names
    assert "common_bigrams"  in names


# --- Bornes des scores (0.0 – 1.0) ---

PLUGIN_NAMES = ["word_overlap", "length_ratio", "prefix", "common_bigrams"]

@pytest.mark.parametrize("name", PLUGIN_NAMES)
def test_score_range(name, ctx):
    metric = registry.get(name)
    result = metric.compute("le chat dort sur le canapé", "un félin repose sur le sofa", ctx)
    assert 0.0 <= result.score <= 1.0, f"{name}: score hors bornes ({result.score})"


# --- Cas limites ---

@pytest.mark.parametrize("name", PLUGIN_NAMES)
def test_identical_phrases(name, ctx):
    metric = registry.get(name)
    result = metric.compute("bonjour le monde", "bonjour le monde", ctx)
    assert result.score == 1.0, f"{name}: phrases identiques devrait donner 1.0"

@pytest.mark.parametrize("name", PLUGIN_NAMES)
def test_empty_phrases(name, ctx):
    metric = registry.get(name)
    result = metric.compute("", "", ctx)
    assert result.score == 1.0, f"{name}: deux phrases vides devrait donner 1.0"


# --- Validation : plugin mal formé rejeté proprement ---

def test_invalid_plugin_no_name():
    from app.core.metrics import BaseMetric
    from app.core.registry import MetricsRegistry

    class BadMetric(BaseMetric):
        name = ""  # invalide
        def compute(self, p1, p2, ctx): return None

    r = MetricsRegistry()
    with pytest.raises(ValueError, match="name"):
        r.register(BadMetric())

def test_invalid_plugin_no_compute():
    from app.core.registry import MetricsRegistry

    class NoCompute:
        name = "no_compute"

    r = MetricsRegistry()
    with pytest.raises(ValueError, match="compute"):
        r.register(NoCompute())
