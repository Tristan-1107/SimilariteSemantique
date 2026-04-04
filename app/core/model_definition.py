import importlib
from dataclasses import dataclass
from typing import Any


@dataclass
class SentenceTransformerResource:
    """Ressource runtime minimale pour les modèles sentence-transformers."""

    model_name: str
    encoder: Any
    util: Any


class BaseModelDefinition:
    """
    Définition légère d'un modèle.

    Les sous-classes décrivent comment charger une ressource, mais ne doivent
    pas la charger à l'instanciation.
    """

    name: str = None
    description: str = None

    def load(self):
        """Charge et retourne la ressource runtime associée au modèle."""
        raise NotImplementedError


class SentenceTransformerModelDefinition(BaseModelDefinition):
    """Définition légère d'un modèle `sentence-transformers`."""

    def __init__(self, name: str, model_name: str, description: str | None = None):
        self.name = name
        self.model_name = model_name
        self.description = description or f"Modèle sentence-transformers '{model_name}'."

    def load(self) -> SentenceTransformerResource:
        try:
            sentence_transformers = importlib.import_module("sentence_transformers")
        except ImportError as exc:
            raise ImportError(
                "La dépendance 'sentence-transformers' est absente. "
                "Installez requirements.txt pour utiliser la métrique 'camembert'."
            ) from exc

        return SentenceTransformerResource(
            model_name=self.model_name,
            encoder=sentence_transformers.SentenceTransformer(self.model_name),
            util=sentence_transformers.util,
        )
