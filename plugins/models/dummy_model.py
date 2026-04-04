from app.core.model_definition import BaseModelDefinition


class DummyModelDefinition(BaseModelDefinition):
    """
    Modèle factice sans dépendance externe.

    Il sert à valider le registre de modèles et le lazy loading sans
    télécharger de vraie ressource ML.
    """

    name = "dummy_echo_model"
    description = "Modèle de test qui retourne un objet Python simple."

    def load(self):
        return {
            "kind": "dummy",
            "message": "dummy model loaded",
        }
