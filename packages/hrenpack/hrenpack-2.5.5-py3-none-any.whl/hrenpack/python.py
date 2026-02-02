import importlib, pkgutil
from importlib import import_module


def import_all_submodules(package_name):
    """Динамически импортирует все подмодули в пакете."""
    package = import_module(package_name)

    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        full_module_name = f"{package_name}.{module_name}"
        try:
            importlib.import_module(full_module_name)
        except ImportError as e:
            print(f"Failed to import {full_module_name}: {e}")
