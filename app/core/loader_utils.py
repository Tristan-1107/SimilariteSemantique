import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_project_path(target_dir: str | Path) -> Path:
    """
    Résout un chemin de manière stable depuis la racine du dépôt.

    - Un chemin absolu est utilisé tel quel.
    - Un chemin relatif est résolu depuis PROJECT_ROOT, pas depuis le
      répertoire courant du processus.
    """
    target_path = Path(target_dir)
    if target_path.is_absolute():
        return target_path
    return (PROJECT_ROOT / target_path).resolve()


def import_module_from_path(filepath: Path, module_prefix: str):
    """Importe dynamiquement un fichier .py avec un nom de module stable."""
    module_name = f"{module_prefix}.{filepath.stem}"

    if module_name in sys.modules:
        del sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, filepath)
    if spec is None or spec.loader is None:
        raise ImportError(f"Impossible de créer un module Python depuis '{filepath}'.")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
