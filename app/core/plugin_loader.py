import inspect
import logging
from pathlib import Path

from app.core.loader_utils import import_module_from_path, resolve_project_path
from app.core.metrics import BaseMetric
from app.core.registry import registry


logger = logging.getLogger(__name__)


def _resolve_plugins_path(plugins_dir: str | Path) -> Path:
    """
    Résout le dossier des plugins de manière stable.

    - Un chemin absolu est utilisé tel quel.
    - Un chemin relatif est résolu depuis la racine du dépôt,
      pas depuis le répertoire courant du processus.
    """
    return resolve_project_path(plugins_dir)


def load_plugins(plugins_dir: str = "plugins/metrics") -> None:
    """
    Découvre et enregistre automatiquement tous les plugins présents
    dans le répertoire donné.

    Un plugin valide est un fichier .py contenant au moins une classe
    héritant de BaseMetric avec un attribut 'name' et une méthode 'compute'.

    Le chargement est tolérant aux erreurs : un plugin cassé est ignoré
    avec un avertissement, les autres continuent de charger.
    """
    plugins_path = _resolve_plugins_path(plugins_dir)

    if not plugins_path.exists():
        logger.info(
            "Répertoire de plugins introuvable : '%s'. Aucun plugin chargé.",
            plugins_dir,
        )
        return

    loaded, skipped = 0, 0

    for filepath in sorted(plugins_path.glob("*.py")):
        if filepath.name.startswith("_"):
            continue

        try:
            module = _import_module_from_path(filepath)
            metrics_found = _extract_metrics(module)

            for metric_class in metrics_found:
                try:
                    instance = metric_class()
                    registry.register(instance)
                    logger.info("Plugin chargé : '%s' (%s)", instance.name, filepath.name)
                    loaded += 1
                except Exception as exc:
                    logger.warning(
                        "Plugin ignoré (%s / %s) : %s",
                        filepath,
                        metric_class.__name__,
                        exc,
                    )
                    skipped += 1

        except Exception as exc:
            logger.warning(
                "Impossible de charger le fichier plugin '%s' : %s",
                filepath,
                exc,
            )
            skipped += 1

    logger.info("Plugins : %s chargé(s), %s ignoré(s).", loaded, skipped)


def _import_module_from_path(filepath: Path):
    """Importe dynamiquement un fichier .py comme module Python."""
    return import_module_from_path(filepath, "plugins.metrics")


def _extract_metrics(module) -> list[type[BaseMetric]]:
    """
    Inspecte un module et retourne toutes les classes qui :
    - héritent de BaseMetric,
    - ne sont pas BaseMetric elle-même,
    - sont définies dans ce module.
    """
    return [
        cls
        for _, cls in inspect.getmembers(module, inspect.isclass)
        if issubclass(cls, BaseMetric)
        and cls is not BaseMetric
        and cls.__module__ == module.__name__
    ]
