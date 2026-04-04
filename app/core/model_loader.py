import inspect
import logging
from pathlib import Path

from app.core.loader_utils import import_module_from_path, resolve_project_path
from app.core.model_definition import BaseModelDefinition
from app.core.model_registry import model_registry


logger = logging.getLogger(__name__)


def _resolve_models_path(models_dir: str | Path) -> Path:
    """Résout le dossier des plugins de modèles de manière stable."""
    return resolve_project_path(models_dir)


def load_models(models_dir: str = "plugins/models") -> None:
    """
    Découvre et enregistre des définitions de modèles depuis un répertoire.

    Le chargement est tolérant aux erreurs : un fichier ou une définition
    cassée est ignoré(e), les autres continuent de charger.
    """
    models_path = _resolve_models_path(models_dir)

    if not models_path.exists():
        logger.info(
            "Répertoire de modèles introuvable : '%s'. Aucun modèle plugin chargé.",
            models_dir,
        )
        return

    loaded, skipped = 0, 0

    for filepath in sorted(models_path.glob("*.py")):
        if filepath.name.startswith("_"):
            continue

        try:
            module = import_module_from_path(filepath, "plugins.models")
            definitions_found = _extract_model_definitions(module)

            for definition_class in definitions_found:
                try:
                    definition = definition_class()
                    model_registry.register(definition)
                    logger.info(
                        "Modèle plugin chargé : '%s' (%s)",
                        definition.name,
                        filepath.name,
                    )
                    loaded += 1
                except Exception as exc:
                    logger.warning(
                        "Plugin modèle ignoré (%s / %s) : %s",
                        filepath,
                        definition_class.__name__,
                        exc,
                    )
                    skipped += 1

        except Exception as exc:
            logger.warning(
                "Impossible de charger le fichier modèle '%s' : %s",
                filepath,
                exc,
            )
            skipped += 1

    logger.info("Modèles plugins : %s chargé(s), %s ignoré(s).", loaded, skipped)


def _extract_model_definitions(module) -> list[type[BaseModelDefinition]]:
    return [
        cls
        for _, cls in inspect.getmembers(module, inspect.isclass)
        if issubclass(cls, BaseModelDefinition)
        and cls is not BaseModelDefinition
        and cls.__module__ == module.__name__
    ]
