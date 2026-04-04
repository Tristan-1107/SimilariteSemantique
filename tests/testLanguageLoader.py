import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.api.endpoints as endpoints_module
import app.core.language_loader as language_loader_module
from app.core.language_config import LanguageConfig
from app.core.language_manager import LanguageManager


def _build_language_manager() -> LanguageManager:
    manager = LanguageManager(default_language="fr")
    manager.register(
        LanguageConfig(
            code="fr",
            display_name="Français",
            spacy_model="fr_core_news_md",
            embedding_model="camembert-base",
        )
    )
    return manager


def _write_language_plugin(directory, filename="fake_language.py"):
    plugin_source = """
from app.core.language_config import LanguageConfig

FAKE_LANGUAGE = LanguageConfig(
    code="xx",
    display_name="Langue de test",
    spacy_model="xx_fake_md",
    embedding_model="dummy_echo_model",
)
"""
    (directory / filename).write_text(plugin_source, encoding="utf-8")


def test_load_languages_registers_language_config(tmp_path, monkeypatch):
    test_manager = _build_language_manager()
    monkeypatch.setattr(language_loader_module, "language_manager", test_manager)
    _write_language_plugin(tmp_path)

    language_loader_module.load_languages(tmp_path)

    context = test_manager.get_context("xx")
    assert context.config.code == "xx"
    assert context.config.display_name == "Langue de test"


def test_loaded_language_appears_in_languages_endpoint_and_fr_stays_available(
    tmp_path,
    monkeypatch,
):
    test_manager = _build_language_manager()
    monkeypatch.setattr(language_loader_module, "language_manager", test_manager)
    monkeypatch.setattr(endpoints_module, "language_manager", test_manager)
    _write_language_plugin(tmp_path)

    app = FastAPI()
    app.include_router(endpoints_module.router)

    language_loader_module.load_languages(tmp_path)

    client = TestClient(app)
    response = client.get("/languages")

    assert response.status_code == 200
    codes = {language["code"] for language in response.json()["languages"]}
    assert "fr" in codes
    assert "xx" in codes
    assert test_manager.get_context("fr").config.code == "fr"


def test_load_languages_skips_broken_plugin_file(tmp_path, monkeypatch, caplog):
    test_manager = _build_language_manager()
    monkeypatch.setattr(language_loader_module, "language_manager", test_manager)
    _write_language_plugin(tmp_path, filename="valid_language.py")
    (tmp_path / "broken_language.py").write_text(
        "raise RuntimeError('boom on import')\n",
        encoding="utf-8",
    )

    with caplog.at_level(logging.WARNING):
        language_loader_module.load_languages(tmp_path)

    assert test_manager.get_context("xx").config.code == "xx"
    assert any("broken_language.py" in record.message for record in caplog.records)
