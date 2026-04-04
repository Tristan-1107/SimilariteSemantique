import logging
from pathlib import Path

from app.core.language_config import LanguageConfig
from app.core.language_manager import language_manager
from app.core.loader_utils import import_module_from_path, resolve_project_path


logger = logging.getLogger(__name__)


def _resolve_languages_path(languages_dir: str | Path) -> Path:
    """Résout le dossier des plugins de langues de manière stable."""
    return resolve_project_path(languages_dir)


def load_languages(languages_dir: str = "plugins/languages") -> None:
    """
    Découvre et enregistre des `LanguageConfig` depuis un répertoire.

    Le chargement est tolérant aux erreurs : un fichier ou une déclaration
    cassée est ignoré(e), les autres continuent de charger.
    """
    languages_path = _resolve_languages_path(languages_dir)

    if not languages_path.exists():
        logger.info(
            "Répertoire de langues introuvable : '%s'. Aucune langue plugin chargée.",
            languages_dir,
        )
        return

    loaded, skipped = 0, 0

    for filepath in sorted(languages_path.glob("*.py")):
        if filepath.name.startswith("_"):
            continue

        try:
            module = import_module_from_path(filepath, "plugins.languages")
            configs_found = _extract_language_configs(module)

            if not configs_found:
                logger.warning(
                    "Aucune déclaration LanguageConfig trouvée dans '%s'.",
                    filepath,
                )
                skipped += 1
                continue

            for config in configs_found:
                try:
                    language_manager.register(config)
                    logger.info(
                        "Langue plugin chargée : '%s' (%s)",
                        config.code,
                        filepath.name,
                    )
                    loaded += 1
                except Exception as exc:
                    logger.warning(
                        "Plugin langue ignoré (%s / %s) : %s",
                        filepath,
                        getattr(config, "code", type(config).__name__),
                        exc,
                    )
                    skipped += 1

        except Exception as exc:
            logger.warning(
                "Impossible de charger le fichier langue '%s' : %s",
                filepath,
                exc,
            )
            skipped += 1

    logger.info("Langues plugins : %s chargée(s), %s ignorée(s).", loaded, skipped)


def _extract_language_configs(module) -> list[LanguageConfig]:
    configs: list[LanguageConfig] = []
    seen_ids: set[int] = set()

    for value in module.__dict__.values():
        if isinstance(value, LanguageConfig):
            if id(value) not in seen_ids:
                configs.append(value)
                seen_ids.add(id(value))
            continue

        if isinstance(value, (list, tuple, set)):
            for item in value:
                if isinstance(item, LanguageConfig) and id(item) not in seen_ids:
                    configs.append(item)
                    seen_ids.add(id(item))

    return configs
