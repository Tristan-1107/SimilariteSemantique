# tests/test_api.py

# Pour lancer ce pgm, se placer dans le repertoire racine "SimilariteSemantique" et exécuter la commande "python3 -m tests.testApi"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_similarity_endpoint():
    payload = {
        "phrase1": "Le chat mange",
        "phrase2": "Le chien mange",
        "metrics": ["jaccard"]
    }
    response = client.post("/similarity", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "jaccard" in data["scores"]
    assert isinstance(data["scores"]["jaccard"], float)
    print("Test API : Calcul de similarité réussi (HTTP 200)")

def test_api_unknown_metric():
    payload = {
        "phrase1": "a", 
        "phrase2": "b", 
        "metrics": ["super_metric_qui_nexiste_pas"]
    }
    response = client.post("/similarity", json=payload)
    assert response.status_code == 400
    assert "Unknown metric" in response.json()["detail"]
    print("Test API : Erreur métrique inconnue bien gérée (HTTP 400)")


test_api_similarity_endpoint()

test_api_unknown_metric()
