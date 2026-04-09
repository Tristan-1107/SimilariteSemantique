"""
Gabarit de plugin de langue.

Ce fichier est volontairement prefixe par "_" pour etre ignore par le loader.
Copiez-le sous un autre nom (sans "_") puis remplacez les champs vides.
"""

from app.core.language_config import LanguageConfig


EXAMPLE_LANGUAGE = LanguageConfig(
    # Code ISO 639-1, par exemple "de" pour l'allemand.
    code="",
    # Nom affiche dans l'API et dans l'interface web.
    display_name="",
    # Nom du modele spaCy a charger pour cette langue.
    spacy_model="",
    # Nom du modele d'embedding a utiliser pour les metriques qui en ont besoin.
    embedding_model="",
)
