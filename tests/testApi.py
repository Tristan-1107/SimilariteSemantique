import asyncio
import json

import pytest
from fastapi import HTTPException

from app.main import app  # noqa: F401
from app.api.endpoints import (
    list_languages,
    list_metrics,
    similarity,
    upload_and_process_file,
)
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
    assert exc_info.value.detail == {
        "code": "unknown_metric",
        "message": "Métrique inconnue : super_metric_qui_nexiste_pas",
    }


def test_api_languages_endpoint_lists_plugin_language():
    response = list_languages()

    codes = {language["code"] for language in response["languages"]}
    assert "fr" in codes
    assert "xx" in codes


def test_api_metrics_endpoint_lists_native_and_plugin_metrics():
    response = list_metrics()

    names = {metric["name"] for metric in response["metrics"]}
    assert "jaccard" in names
    assert "bert_score" in names


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
    assert exc_info.value.detail == {
        "code": "invalid_file_type",
        "message": "Seuls les fichiers .json sont acceptés",
    }


def test_api_similarity_upload_rejects_invalid_json_content():
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            upload_and_process_file(
                file=DummyUploadFile("pairs.json", b"{invalid json}"),
            )
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "invalid_json"
    assert "JSON invalide" in exc_info.value.detail["message"]


def test_api_similarity_upload_rejects_unknown_language():
    payload = {
        "metrics": ["jaccard"],
        "pairs": [
            ["bonjour", "salut"],
        ],
    }

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            upload_and_process_file(
                file=DummyUploadFile(
                    "pairs.json",
                    json.dumps(payload).encode("utf-8"),
                ),
                language="zz",
            )
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "invalid_request"
    assert "Langue non supportée" in exc_info.value.detail["message"]


def test_api_similarity_upload_rejects_unknown_metric_in_batch():
    payload = {
        "metrics": ["mystery_metric"],
        "pairs": [
            ["bonjour", "salut"],
        ],
    }

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            upload_and_process_file(
                file=DummyUploadFile(
                    "pairs.json",
                    json.dumps(payload).encode("utf-8"),
                ),
            )
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == {
        "code": "invalid_request",
        "message": "Unknown metric(s): mystery_metric",
    }


def test_api_similarity_upload_rejects_invalid_pair_shape():
    payload = {
        "metrics": ["jaccard"],
        "pairs": [
            ["bonjour", "salut", "extra"],
        ],
    }

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            upload_and_process_file(
                file=DummyUploadFile(
                    "pairs.json",
                    json.dumps(payload).encode("utf-8"),
                ),
            )
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == {
        "code": "invalid_request",
        "message": "Couple invalide à l'index 1: chaque entrée doit contenir exactement 2 phrases.",
    }
