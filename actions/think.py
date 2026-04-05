"""
think.py — Acción: razonamiento interno.

El agente puede "pensar" sin ejecutar nada.
Útil para planificar pasos o analizar una situación.
"""

from actions.base import Action
from actions.registry import register


@register
class Think(Action):
    name = "think"
    description = "Razonamiento interno del agente — no ejecuta nada"

    def execute(self, thought: str = "", **kwargs) -> dict:
        return {
            "success": True,
            "result": f"[Pensamiento registrado]: {thought}",
        }


@register
class Wait(Action):
    name = "wait"
    description = "Espera N segundos antes de continuar"

    def execute(self, seconds: str = "1", **kwargs) -> dict:
        import time
        try:
            secs = float(seconds)
            secs = min(secs, 300)  # Máximo 5 minutos
            time.sleep(secs)
            return {
                "success": True,
                "result": f"Esperó {secs} segundos",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
