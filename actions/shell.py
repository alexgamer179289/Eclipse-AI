"""
shell.py — Acción: ejecutar comandos shell.

Permite al agente interactuar con el sistema operativo.
"""

import subprocess
import platform
from actions.base import Action
from actions.registry import register
from config import SHELL_TIMEOUT, WORKSPACE_DIR


@register
class RunShell(Action):
    name = "run_shell"
    description = "Ejecuta un comando en la terminal del sistema"

    def execute(self, command: str = "", **kwargs) -> dict:
        if not command:
            return {"success": False, "error": "No se proporcionó comando"}

        try:
            # En Windows, usar PowerShell para mejor compatibilidad
            if platform.system() == "Windows":
                cmd = ["powershell", "-NoProfile", "-Command", command]
            else:
                cmd = command

            proc = subprocess.run(
                cmd,
                shell=not isinstance(cmd, list),
                capture_output=True,
                text=True,
                timeout=SHELL_TIMEOUT,
                cwd=WORKSPACE_DIR,
            )

            output = proc.stdout
            if proc.stderr:
                output += f"\n[stderr]: {proc.stderr}"

            # Truncar output largo
            if len(output) > 5000:
                output = output[:5000] + "\n\n[... output truncado ...]"

            return {
                "success": proc.returncode == 0,
                "result": output or "(sin salida)",
                "returncode": proc.returncode,
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout ({SHELL_TIMEOUT}s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}
