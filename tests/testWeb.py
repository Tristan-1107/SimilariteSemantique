import asyncio
import json

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.main import app  # noqa: F401
from app.web.routes import compare, download, home, upload


class DummyUploadFile:
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self._content = content

    async def read(self) -> bytes:
        return self._content


def build_request(path: str, method: str = "GET") -> Request:
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "root_path": "",
        "scheme": "http",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_web_home_page_renders_forms():
    response = home(build_request("/"))
    body = response.body.decode("utf-8")

    assert response.status_code == 200
    assert 'action="/web/compare"' in body
    assert 'action="/web/upload"' in body
    assert "Comparer des phrases depuis le navigateur" in body


def test_web_compare_displays_scores():
    response = compare(
        build_request("/web/compare", method="POST"),
        phrase1="bonjour",
        phrase2="bonjour",
        metrics=["levenshtein"],
        language="fr",
    )
    body = response.body.decode("utf-8")

    assert response.status_code == 200
    assert "Résultats de la comparaison" in body
    assert "levenshtein" in body
    assert "1.0000" in body


def test_web_upload_displays_results_and_download_link(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMILARITY_DATA_DIR", str(tmp_path))

    payload = {
        "metrics": ["levenshtein"],
        "language": "fr",
        "pairs": [
            ["bonjour", "bonjour"],
            ["chat", "chien"],
        ],
    }

    response = asyncio.run(
        upload(
            build_request("/web/upload", method="POST"),
            file=DummyUploadFile(
                "pairs.json",
                json.dumps(payload).encode("utf-8"),
            ),
            language="fr",
        )
    )
    body = response.body.decode("utf-8")

    assert response.status_code == 200
    assert "Résultats du batch" in body
    assert "result_pairs.json" in body
    assert (tmp_path / "result_pairs.json").exists()


def test_web_download_returns_generated_file(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMILARITY_DATA_DIR", str(tmp_path))
    output_path = tmp_path / "result_pairs.json"
    output_path.write_text('{"message":"ok"}', encoding="utf-8")

    response = download("result_pairs.json")

    assert response.status_code == 200
    assert response.media_type == "application/json"
    assert response.path == output_path


def test_web_download_rejects_invalid_filename():
    with pytest.raises(HTTPException) as exc_info:
        download("result_pairs.txt")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Nom de fichier invalide."
