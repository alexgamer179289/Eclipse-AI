"""
registry.py — Registro de acciones.

Las acciones se registran aquí para que el agente las pueda
descubrir y ejecutar por nombre.
"""

_registry = {}


def register(action_class):
    """Decorador que registra una acción automáticamente."""
    _registry[action_class.name] = action_class
    return action_class


def get(name: str):
    """Obtiene una clase de acción por nombre."""
    return _registry.get(name)


def list_names() -> list:
    """Lista nombres de todas las acciones registradas."""
    return list(_registry.keys())


def list_all() -> dict:
    """Lista todas las acciones con su descripción."""
    return {name: cls.description for name, cls in _registry.items()}
