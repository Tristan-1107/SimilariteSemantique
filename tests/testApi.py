import json

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_api_similarity_endpoint():
    payload = {
        "phrase1": "Le chat mange",
        "phrase2": "Le chien mange",
        "metrics": ["jaccard"],
    }
    response = client.post("/similarity", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "jaccard" in data["scores"]
    assert isinstance(data["scores"]["jaccard"], float)


def test_api_unknown_metric():
    payload = {
        "phrase1": "a",
        "phrase2": "b",
        "metrics": ["super_metric_qui_nexiste_pas"],
    }
    response = client.post("/similarity", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "unknown_metric",
        "message": "Métrique inconnue : super_metric_qui_nexiste_pas",
    }


def test_api_languages_endpoint_lists_plugin_language():
    response = client.get("/languages")

    assert response.status_code == 200
    codes = {language["code"] for language in response.json()["languages"]}
    assert "fr" in codes
    assert "xx" in codes


def test_api_metrics_endpoint_lists_native_and_plugin_metrics():
    response = client.get("/metrics")

    assert response.status_code == 200
    metrics = response.json()["metrics"]
    names = {metric["name"] for metric in metrics}
    assert "jaccard" in names
    assert "bert_score" in names


def test_api_similarity_accepts_plugin_language():
    payload = {
        "phrase1": "bonjour",
        "phrase2": "bonjour",
        "metrics": ["jaccard"],
        "language": "xx",
    }
    response = client.post("/similarity", json=payload)

    assert response.status_code == 200
    assert response.json()["metadata"]["language"] == "xx"


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

    response = client.post(
        "/similarity/upload",
        files={
            "file": (
                "pairs.json",
                json.dumps(payload).encode("utf-8"),
                "application/json",
            )
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["output_file"] == "result_pairs.json"
    assert len(data["results"]["results"]) == 2
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

    response = client.post(
        "/similarity/upload",
        files={
            "file": (
                "pairs_xx.json",
                json.dumps(payload).encode("utf-8"),
                "application/json",
            )
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["results"]["metadata"]["language"] == "xx"
    assert (tmp_path / "result_pairs_xx.json").exists()


def test_api_similarity_upload_rejects_non_json():
    response = client.post(
        "/similarity/upload",
        files={"file": ("pairs.txt", b"[]", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "invalid_file_type",
        "message": "Seuls les fichiers .json sont acceptés",
    }


def test_api_similarity_upload_rejects_invalid_json_content():
    response = client.post(
        "/similarity/upload",
        files={"file": ("pairs.json", b"{invalid json}", "application/json")},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_json"
    assert "JSON invalide" in response.json()["detail"]["message"]


def test_api_similarity_upload_rejects_unknown_language():
    payload = {
        "metrics": ["jaccard"],
        "pairs": [
            ["bonjour", "salut"],
        ],
    }

    response = client.post(
        "/similarity/upload?language=zz",
        files={
            "file": (
                "pairs.json",
                json.dumps(payload).encode("utf-8"),
                "application/json",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_request"
    assert "Langue non supportée" in response.json()["detail"]["message"]


def test_api_similarity_upload_rejects_unknown_metric_in_batch():
    payload = {
        "metrics": ["mystery_metric"],
        "pairs": [
            ["bonjour", "salut"],
        ],
    }

    response = client.post(
        "/similarity/upload",
        files={
            "file": (
                "pairs.json",
                json.dumps(payload).encode("utf-8"),
                "application/json",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {
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

    response = client.post(
        "/similarity/upload",
        files={
            "file": (
                "pairs.json",
                json.dumps(payload).encode("utf-8"),
                "application/json",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "invalid_request",
        "message": "Couple invalide à l'index 1: chaque entrée doit contenir exactement 2 phrases.",
    }
