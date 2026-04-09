"""
Gabarit de plugin de modele.

Ce fichier est volontairement prefixe par "_" pour etre ignore par le loader.
Copiez-le sous un autre nom (sans "_") puis completez la definition.
"""

from app.core.model_definition import BaseModelDefinition


class ExampleModelDefinition(BaseModelDefinition):
    # Nom unique du modele dans le registre.
    name = ""
    # Description courte du role de ce modele.
    description = ""

    def load(self):
        # Retourner ici la ressource runtime chargee par le modele.
        raise NotImplementedError("Remplacez ce gabarit par votre logique de chargement.")
