import logging
from pathlib import Path

import pytest

import app.core.model_loader as model_loader_module
from app.core.model_definition import BaseModelDefinition
from app.core.model_registry import ModelRegistry


class DummyDefinition(BaseModelDefinition):
    name = "dummy_for_tests"
    description = "Definition de test."

    def __init__(self):
        self.load_calls = 0

    def load(self):
        self.load_calls += 1
        return {"loaded": self.load_calls}


def test_models_path_resolution_is_stable(monkeypatch):
    project_root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(project_root / "tests")

    resolved = model_loader_module._resolve_models_path("plugins/models")

    assert resolved == (project_root / "plugins" / "models").resolve()
    assert resolved.is_dir()


def test_model_registry_registers_definition_and_lists():
    registry = ModelRegistry()
    definition = DummyDefinition()

    registry.register(definition)

    listed = registry.list()
    assert len(listed) == 1
    assert listed[0]["name"] == "dummy_for_tests"
    assert listed[0]["loaded"] is False
    assert registry.get_definition("dummy_for_tests") is definition


def test_model_registry_loads_once_and_reuses_cache():
    registry = ModelRegistry()
    definition = DummyDefinition()
    registry.register(definition)

    first = registry.get("dummy_for_tests")
    second = registry.get("dummy_for_tests")

    assert definition.load_calls == 1
    assert first is second
    assert registry.list()[0]["loaded"] is True


def test_load_models_skips_broken_plugin_file(tmp_path, monkeypatch, caplog):
    valid_plugin = """
from app.core.model_definition import BaseModelDefinition

class TempModel(BaseModelDefinition):
    name = "temp_model"
    description = "Modele temporaire."

    def load(self):
        return {"ok": True}
"""
    broken_plugin = "raise RuntimeError('boom on import')\n"

    (tmp_path / "valid_model.py").write_text(valid_plugin, encoding="utf-8")
    (tmp_path / "broken_model.py").write_text(broken_plugin, encoding="utf-8")

    test_registry = ModelRegistry()
    monkeypatch.setattr(model_loader_module, "model_registry", test_registry)

    with caplog.at_level(logging.WARNING):
        model_loader_module.load_models(tmp_path)

    assert test_registry.get_definition("temp_model") is not None
    assert any("broken_model.py" in record.message for record in caplog.records)


def test_model_registry_raises_runtime_error_when_real_load_fails():
    class FailingDefinition(BaseModelDefinition):
        name = "failing_model"
        description = "Definition qui echoue au chargement."

        def load(self):
            raise OSError("missing runtime dependency")

    registry = ModelRegistry()
    registry.register(FailingDefinition())

    with pytest.raises(RuntimeError, match="failing_model"):
        registry.get("failing_model")

    with pytest.raises(RuntimeError, match="missing runtime dependency"):
        registry.get("failing_model")
