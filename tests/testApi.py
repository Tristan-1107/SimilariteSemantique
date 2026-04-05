import asyncio
import json

import pytest
from fastapi import HTTPException

from app.main import app  # noqa: F401
from app.api.endpoints import list_languages, similarity, upload_and_process_file
from app.models.schemas import SimilarityRequest


class DummyUploadFile:
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self._content = content

    async def read(self) -> bytes:
        return self._content


def test_api_similarity_endpoint():
    payload = SimilarityRequest(
        phrase1="Le chat mange",
        phrase2="Le chien mange",
        metrics=["jaccard"],
    )

    response = similarity(payload)

    assert "jaccard" in response.scores
    assert isinstance(response.scores["jaccard"], float)


def test_api_unknown_metric():
    payload = SimilarityRequest(
        phrase1="a",
        phrase2="b",
        metrics=["super_metric_qui_nexiste_pas"],
    )

    with pytest.raises(HTTPException) as exc_info:
        similarity(payload)

    assert exc_info.value.status_code == 400
    assert "Unknown metric" in exc_info.value.detail


def test_api_languages_endpoint_lists_plugin_language():
    response = list_languages()

    codes = {language["code"] for language in response["languages"]}
    assert "fr" in codes
    assert "xx" in codes


def test_api_similarity_accepts_plugin_language():
    payload = SimilarityRequest(
        phrase1="bonjour",
        phrase2="bonjour",
        metrics=["jaccard"],
        language="xx",
    )

    response = similarity(payload)

    assert response.metadata["language"] == "xx"


def test_api_similarity_upload_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMILARITY_DATA_DIR", str(tmp_path))

    payload = {
        "metrics": ["jaccard", "levenshtein"],
        "language": "fr",
        "pairs": [
            ["Le chat mange", "Le chien mange"],
            ["bonjour", "bonjour"],
        ],
    }

    response = asyncio.run(
        upload_and_process_file(
            file=DummyUploadFile(
                "pairs.json",
                json.dumps(payload).encode("utf-8"),
            ),
        )
    )

    assert response["output_file"] == "result_pairs.json"
    assert len(response["results"]["results"]) == 2
    assert (tmp_path / "result_pairs.json").exists()


def test_api_similarity_upload_accepts_plugin_language(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMILARITY_DATA_DIR", str(tmp_path))

    payload = {
        "metrics": ["jaccard"],
        "language": "xx",
        "pairs": [
            ["bonjour", "bonjour"],
        ],
    }

    response = asyncio.run(
        upload_and_process_file(
            file=DummyUploadFile(
                "pairs_xx.json",
                json.dumps(payload).encode("utf-8"),
            ),
        )
    )

    assert response["results"]["metadata"]["language"] == "xx"
    assert (tmp_path / "result_pairs_xx.json").exists()


def test_api_similarity_upload_rejects_non_json():
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            upload_and_process_file(
                file=DummyUploadFile("pairs.txt", b"[]"),
            )
        )

    assert exc_info.value.status_code == 400
