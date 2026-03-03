# app/core/language_config.py
from dataclasses import dataclass


@dataclass
class LanguageConfig:
    """
    Déclaration statique des paramètres d'une langue.
    Ajouter une langue = créer une nouvelle instance de cette classe.
    Aucune modification du moteur requise.
    """
    code: str              # ex: "fr", "en"
    display_name: str      # ex: "Français"
    spacy_model: str       # ex: "fr_core_news_md"
    embedding_model: str   # ex: "camembert-base" (pour Sprint 5+)