import importlib
import inspect
import pkgutil
from typing import Dict, Iterable, Type

import src.enrich.plugins


def _is_valid_plugin_class(obj: object) -> bool:
    """
    A valid enrichment plugin is a *class* that:
    - has a string 'name' attribute
    - has a callable 'enrich' method
    """
    return (
        inspect.isclass(obj)
        and hasattr(obj, "name")
        and isinstance(getattr(obj, "name"), str)
        and callable(getattr(obj, "enrich", None))
    )


def load_plugins(enabled: Iterable[str]) -> Dict[str, object]:
    """
    Load and instantiate enabled enrichment plugins.

    Plugins are discovered dynamically from src.enrich.plugins
    and instantiated exactly once.
    """
    enabled_set = set(enabled)
    plugins: Dict[str, object] = {}

    for module_info in pkgutil.iter_modules(src.enrich.plugins.__path__):
        module = importlib.import_module(
            f"src.enrich.plugins.{module_info.name}"
        )

        for obj in vars(module).values():
            if not _is_valid_plugin_class(obj):
                continue

            if obj.name not in enabled_set:
                continue

            if obj.name in plugins:
                raise RuntimeError(f"Duplicate plugin name detected: {obj.name}")

            plugins[obj.name] = obj()

    return plugins


def discover_plugins() -> Dict[str, Type[object]]:
    """
    Discover available enrichment plugins without instantiating them.
    Used for --list-plugins.
    """
    discovered: Dict[str, Type[object]] = {}

    for module_info in pkgutil.iter_modules(src.enrich.plugins.__path__):
        module = importlib.import_module(
            f"src.enrich.plugins.{module_info.name}"
        )

        for obj in vars(module).values():
            if _is_valid_plugin_class(obj):
                discovered[obj.name] = obj

    return discovered
