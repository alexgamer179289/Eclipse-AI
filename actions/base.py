"""
base.py — Clase base para acciones del agente.

Cada acción es algo que el agente puede ejecutar en el mundo real.
Hereda de Action, se registra automáticamente con el decorador @register.
"""

from abc import ABC, abstractmethod


class Action(ABC):
    """Clase base — toda acción del agente hereda de aquí."""

    name: str = "base"
    description: str = "Acción base"

    @abstractmethod
    def execute(self, **kwargs) -> dict:
        """
        Ejecuta la acción.
        SIEMPRE retorna:
          { "success": bool, "result": ... }
        o en error:
          { "success": False, "error": str }
        """
        pass

    def __repr__(self):
        return f"Action({self.name})"
