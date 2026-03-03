# app/core/language_manager.py
import spacy
from dataclasses import dataclass, field
from typing import Any, Optional

from app.core.language_config import LanguageConfig


@dataclass
class LanguageContext:
    """
    Contexte d'exécution résolu pour une langue donnée.
    C'est cet objet qui est passé aux métriques lors du calcul.
    Il contient le pipeline spaCy déjà chargé, prêt à l'emploi.
    """
    config: LanguageConfig
    pipeline: Any  # instance spaCy nlp chargée


class LanguageManager:
    """
    Gère le cycle de vie des ressources linguistiques.
    - Enregistre des LanguageConfig (déclaratif).
    - Charge les pipelines spaCy à la demande (lazy loading).
    - Sert de point d'entrée unique pour tout accès aux ressources NLP.
    """

    def __init__(self, default_language: str = "fr"):
        self._configs: dict[str, LanguageConfig] = {}
        self._pipelines: dict[str, Any] = {}   # cache des pipelines chargés
        self._default_language = default_language

    def register(self, config: LanguageConfig) -> None:
        """Déclare une langue supportée."""
        self._configs[config.code] = config

    def get_context(self, code: Optional[str] = None) -> LanguageContext:
        """
        Retourne le LanguageContext pour le code donné.
        Si code est None, utilise la langue par défaut.
        Charge le pipeline spaCy si ce n'est pas déjà fait (lazy loading).
        """
        code = code or self._default_language

        if code not in self._configs:
            raise ValueError(
                f"Langue non supportée : '{code}'. "
                f"Langues disponibles : {list(self._configs.keys())}"
            )

        # Lazy loading : on ne charge le pipeline qu'une seule fois
        if code not in self._pipelines:
            self._pipelines[code] = self._load_pipeline(self._configs[code])

        return LanguageContext(
            config=self._configs[code],
            pipeline=self._pipelines[code],
        )

    def list_languages(self) -> list[dict]:
        """Liste les langues déclarées (pour un futur endpoint /languages)."""
        return [
            {"code": c.code, "display_name": c.display_name}
            for c in self._configs.values()
        ]

    @staticmethod
    def _load_pipeline(config: LanguageConfig) -> Any:
        """Charge le pipeline spaCy pour une config donnée."""
        try:
            return spacy.load(config.spacy_model)
        except OSError:
            print(
                f"ATTENTION: Le modèle spaCy '{config.spacy_model}' est introuvable. "
                f"Utilisation d'un modèle vide pour '{config.code}'."
            )
            return spacy.blank(config.code)


# ---------------------------------------------------------------------------
# Instance globale + configuration de la V1 (français uniquement)
# ---------------------------------------------------------------------------

language_manager = LanguageManager(default_language="fr")

language_manager.register(LanguageConfig(
    code="fr",
    display_name="Français",
    spacy_model="fr_core_news_md",
    embedding_model="camembert-base",
))

# Pour ajouter l'anglais en V2, il suffira d'ajouter :
# language_manager.register(LanguageConfig(
#     code="en",
#     display_name="English",
#     spacy_model="en_core_web_md",
#     embedding_model="all-MiniLM-L6-v2",
# ))