from app.core.model_definition import (
    BaseModelDefinition,
    SentenceTransformerModelDefinition,
)


CAMEMBERT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class ModelRegistry:
    """Registre de définitions de modèles avec chargement lazy et cache runtime."""

    def __init__(self):
        self._definitions: dict[str, BaseModelDefinition] = {}
        self._loaded_models: dict[str, object] = {}

    def register(self, definition: BaseModelDefinition) -> None:
        """
        Enregistre une définition légère.

        En cas de collision de nom, la dernière définition écrase la précédente
        et invalide la ressource déjà chargée pour ce nom.
        """
        self._validate(definition)
        self._definitions[definition.name] = definition
        self._loaded_models.pop(definition.name, None)

    def get_definition(self, name: str):
        return self._definitions.get(name)

    def get(self, name: str):
        definition = self._definitions.get(name)
        if definition is None:
            return None

        if name not in self._loaded_models:
            try:
                self._loaded_models[name] = definition.load()
            except Exception as exc:
                raise RuntimeError(
                    f"Impossible de charger le modèle '{name}' : {exc}"
                ) from exc

        return self._loaded_models[name]

    def list(self) -> list[dict]:
        return [
            {
                "name": definition.name,
                "description": definition.description,
                "loaded": definition.name in self._loaded_models,
            }
            for definition in self._definitions.values()
        ]

    @staticmethod
    def _validate(definition: BaseModelDefinition) -> None:
        name = getattr(definition, "name", None)
        if not name or not isinstance(name, str):
            raise ValueError(
                f"Définition de modèle invalide ({type(definition).__name__}) : "
                f"l'attribut 'name' doit être une string non vide."
            )

        if not getattr(definition, "description", None):
            print(f"AVERTISSEMENT: Le modèle '{name}' n'a pas de description.")

        if not callable(getattr(definition, "load", None)):
            raise ValueError(
                f"Définition de modèle invalide ('{name}') : "
                f"la méthode 'load' est absente ou non callable."
            )


model_registry = ModelRegistry()

model_registry.register(
    SentenceTransformerModelDefinition(
        name=CAMEMBERT_MODEL_NAME,
        model_name=CAMEMBERT_MODEL_NAME,
        description=(
            "Modèle de phrases multilingue utilisé par la métrique 'camembert'."
        ),
    )
)
