# app/core/plugin_loader.py

import importlib
import importlib.util
import inspect
import sys
from pathlib import Path

from app.core.metrics import BaseMetric
from app.core.registry import registry

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_plugins_path(plugins_dir: str | Path) -> Path:
    """
    Résout le dossier des plugins de manière stable.

    - Un chemin absolu est utilisé tel quel.
    - Un chemin relatif est résolu depuis la racine du dépôt,
      pas depuis le répertoire courant du processus.
    """
    plugins_path = Path(plugins_dir)
    if plugins_path.is_absolute():
        return plugins_path
    return (PROJECT_ROOT / plugins_path).resolve()


def load_plugins(plugins_dir: str = "plugins/metrics") -> None:
    """
    Découvre et enregistre automatiquement tous les plugins présents
    dans le répertoire donné.

    Un plugin valide est un fichier .py contenant au moins une classe
    héritant de BaseMetric avec un attribut 'name' et une méthode 'compute'.

    Le chargement est tolérant aux erreurs : un plugin cassé est ignoré
    avec un message d'avertissement, les autres continuent de charger.
    """
    plugins_path = _resolve_plugins_path(plugins_dir)

    if not plugins_path.exists():
        print(f"INFO: Répertoire de plugins introuvable : '{plugins_dir}'. Aucun plugin chargé.")
        return

    plugin_files = sorted(plugins_path.glob("*.py"))

    loaded, skipped = 0, 0

    for filepath in plugin_files:
        if filepath.name.startswith("_"):
            continue  # ignorer __init__.py etc.

        try:
            module = _import_module_from_path(filepath)
            metrics_found = _extract_metrics(module)

            for metric_class in metrics_found:
                try:
                    instance = metric_class()
                    registry.register(instance)
                    print(f"Plugin chargé : '{instance.name}' ({filepath.name})")
                    loaded += 1
                except (ValueError, Exception) as e:
                    print(f"AVERTISSEMENT: Plugin ignoré ({filepath.name} / {metric_class.__name__}) : {e}")
                    skipped += 1

        except Exception as e:
            print(f"ERREUR: Impossible de charger le fichier plugin '{filepath.name}' : {e}")
            skipped += 1

    print(f"Plugins : {loaded} chargé(s), {skipped} ignoré(s).")


def _import_module_from_path(filepath: Path):
    """Importe dynamiquement un fichier .py comme module Python."""
    module_name = f"plugins.metrics.{filepath.stem}"

    # Si le module est déjà importé (rechargement), on le retire du cache
    if module_name in sys.modules:
        del sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _extract_metrics(module) -> list:
    """
    Inspecte un module et retourne toutes les classes qui :
    - héritent de BaseMetric,
    - ne sont pas BaseMetric elle-même,
    - sont définies dans ce module (pas importées depuis ailleurs).
    """
    return [
        cls
        for _, cls in inspect.getmembers(module, inspect.isclass)
        if issubclass(cls, BaseMetric)
        and cls is not BaseMetric
        and cls.__module__ == module.__name__
    ]
