from dataclasses import dataclass
from typing import Any, Optional

from app.core.language_config import LanguageConfig
from app.core.spacy_compat import spacy


@dataclass
class LanguageContext:
    """
    Contexte d'exécution résolu pour une langue donnée.
    C'est cet objet qui est passé aux métriques lors du calcul.
    """

    config: LanguageConfig
    pipeline: Any


class LanguageManager:
    """
    Gère le cycle de vie des ressources linguistiques.
    - Enregistre des LanguageConfig.
    - Charge les pipelines spaCy à la demande.
    - Sert de point d'entrée unique pour l'accès aux ressources NLP.
    """

    def __init__(self, default_language: str = "fr"):
        self._configs: dict[str, LanguageConfig] = {}
        self._pipelines: dict[str, Any] = {}
        self._default_language = default_language

    def register(self, config: LanguageConfig) -> None:
        """
        Déclare une langue supportée.

        En cas de collision de code, la dernière déclaration écrase la
        précédente et invalide le pipeline déjà mis en cache.
        """
        self._validate_config(config)
        self._configs[config.code] = config
        self._pipelines.pop(config.code, None)

    def get_context(self, code: Optional[str] = None) -> LanguageContext:
        code = code or self._default_language

        if code not in self._configs:
            raise ValueError(
                f"Langue non supportée : '{code}'. "
                f"Langues disponibles : {list(self._configs.keys())}"
            )

        if code not in self._pipelines:
            self._pipelines[code] = self._load_pipeline(self._configs[code])

        return LanguageContext(
            config=self._configs[code],
            pipeline=self._pipelines[code],
        )

    def list_languages(self) -> list[dict]:
        return [
            {"code": config.code, "display_name": config.display_name}
            for config in self._configs.values()
        ]

    @staticmethod
    def _load_pipeline(config: LanguageConfig) -> Any:
        try:
            return spacy.load(config.spacy_model)
        except OSError:
            print(
                f"ATTENTION: Le modèle spaCy '{config.spacy_model}' est introuvable. "
                f"Utilisation d'un modèle vide pour '{config.code}'."
            )
            return spacy.blank(config.code)

    @staticmethod
    def _validate_config(config: LanguageConfig) -> None:
        if not isinstance(config, LanguageConfig):
            raise TypeError(
                "Une langue doit être déclarée avec une instance de LanguageConfig."
            )

        if not config.code or not isinstance(config.code, str):
            raise ValueError("Une langue doit définir un code non vide.")

        if not config.display_name or not isinstance(config.display_name, str):
            raise ValueError(
                f"La langue '{config.code}' doit définir un display_name non vide."
            )

        if not config.spacy_model or not isinstance(config.spacy_model, str):
            raise ValueError(
                f"La langue '{config.code}' doit définir un spacy_model non vide."
            )


language_manager = LanguageManager(default_language="fr")

language_manager.register(
    LanguageConfig(
        code="fr",
        display_name="Français",
        spacy_model="fr_core_news_md",
        embedding_model="camembert-base",
    )
)
