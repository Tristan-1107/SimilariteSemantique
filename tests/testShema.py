# Pour lancer ce pgm, se placer dans le repertoire racine "SimilariteSemantique" et exécuter la commande "python3 -m tests.testShema"

# tests/test_schemas.py

import pytest
from pydantic import ValidationError
from app.models.schemas import SimilarityRequest

def test_request_validation_valid():
    req = SimilarityRequest(phrase1="abc", phrase2="def")
    assert req.metrics == ["jaccard"]  # Valeur par défaut
    print("valeure par défaut bien générée")

def test_request_validation_missing():
    with pytest.raises(ValidationError):
        SimilarityRequest(phrase1="abc") # phrase2 manque
    print("ValidationError a bien été levée si une phrase manque")

test_request_validation_valid()

test_request_validation_missing()