"""
run_code.py — Acción: ejecutar código Python.

El agente puede generar código y ejecutarlo directamente.
Corre en un subproceso aislado con timeout.
"""

import sys
import os
import subprocess
import tempfile

from actions.base import Action
from actions.registry import register
from config import CODE_TIMEOUT, WORKSPACE_DIR


@register
class RunPython(Action):
    name = "run_python"
    description = "Ejecuta código Python en un subproceso aislado"

    def execute(self, code: str = "", **kwargs) -> dict:
        if not code:
            return {"success": False, "error": "No se proporcionó código"}

        temp_path = None
        try:
            # Escribir a archivo temporal
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8",
                dir=WORKSPACE_DIR
            ) as f:
                f.write(code)
                temp_path = f.name

            # Ejecutar con el mismo Python que está corriendo el agente
            proc = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=CODE_TIMEOUT,
                cwd=WORKSPACE_DIR,
            )

            output = proc.stdout
            if proc.stderr:
                output += f"\n[stderr]: {proc.stderr}"

            # Truncar output si es muy largo
            if len(output) > 5000:
                output = output[:5000] + "\n\n[... output truncado ...]"

            return {
                "success": proc.returncode == 0,
                "result": output or "(sin salida)",
                "returncode": proc.returncode,
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout ({CODE_TIMEOUT}s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
