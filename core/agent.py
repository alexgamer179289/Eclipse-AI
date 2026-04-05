"""
agent.py — El agente operativo.

Ciclo de operación:
  1. Recibe instrucción
  2. Evalúa estado actual
  3. Envía instrucción + contexto al modelo
  4. Parsea respuesta — detecta si hay acciones
  5. Ejecuta acciones automáticamente
  6. Si la acción genera output, lo retroalimenta al modelo
  7. Actualiza estado
  8. Repite si hay acciones encadenadas

No es un chat. Es un ciclo de operación.
"""

import time
from datetime import datetime
from core.gemini import GeminiClient
from core.state import State
from core.parser import parse_response, has_action
from actions import registry
from config import MAX_AUTO_ACTIONS


class Agent:
    """
    Agente operativo central.
    Recibe instrucciones → evalúa estado → ejecuta acciones → reporta.
    """

    def __init__(self, api_key: str = None, verbose: bool = True):
        self.brain = GeminiClient(api_key=api_key)
        self.state = State()
        self.verbose = verbose    # Imprime pasos en consola
        self._last_exec_time = 0  # Tiempo de última ejecución en ms

    def log(self, msg: str):
        """Log interno — solo si verbose está activo."""
        if self.verbose:
            print(f"  ⚙ {msg}")

    def instruct(self, instruction: str) -> str:
        """
        Punto de entrada principal.
        Procesa instrucción con ciclo completo de acción.
        """
        start_time = time.time()

        # 1. Construir mensaje con contexto de estado
        context = self.state.summary()
        full_message = f"{context}\n\n[Instrucción]: {instruction}"

        # 2. Enviar al modelo
        self.log("Enviando al modelo...")
        response = self.brain.chat(full_message)

        # 3. Ciclo de acciones automáticas
        auto_count = 0
        all_outputs = []

        while has_action(response) and auto_count < MAX_AUTO_ACTIONS:
            auto_count += 1
            actions, message = parse_response(response)

            if message:
                self.log(f"Modelo dice: {message[:100]}")
                all_outputs.append(message)

            for action in actions:
                self.log(f"[{auto_count}/{MAX_AUTO_ACTIONS}] Acción: {action.name}")
                result = self._execute_action(action.name, action.params)

                # Registrar en estado
                success = result.get("success", False)
                result_text = str(result.get("result", result.get("error", "")))

                self.state.update(
                    instruction=f"[AUTO] {action.name}",
                    result=result_text,
                    action=action.name,
                    success=success,
                )

                # Trackear archivos creados
                if action.name == "write_file" and success:
                    path = action.params.get("path", "")
                    if path:
                        self.state.track_file(path)

                # Retroalimentar resultado al modelo
                feedback = (
                    f"[Resultado de {action.name}]\n"
                    f"Éxito: {success}\n"
                    f"Output: {result_text[:2000]}\n\n"
                    f"¿Necesitas ejecutar otra acción o ya terminaste?"
                )
                self.log("Retroalimentando resultado...")
                response = self.brain.chat(feedback)

        # 4. Registro final
        final_text = response
        if has_action(response):
            _, final_text = parse_response(response)
            final_text = final_text or response

        self.state.update(
            instruction=instruction,
            result=final_text[:500],
            success=True,
        )

        self._last_exec_time = int((time.time() - start_time) * 1000)
        self.log(f"Completado en {self._last_exec_time}ms ({auto_count} acciones)")

        return final_text

    def instruct_stream(self, instruction: str):
        """
        Versión streaming — procesa instrucción y yield chunks.
        Para uso con interfaces web o APIs.
        """
        context = self.state.summary()
        full_message = f"{context}\n\n[Instrucción]: {instruction}"

        response_text = ""
        for chunk in self.brain.chat_stream(full_message):
            response_text += chunk
            yield chunk

        # Procesar acciones si las hay
        if has_action(response_text):
            actions, message = parse_response(response_text)
            for action in actions:
                result = self._execute_action(action.name, action.params)
                success = result.get("success", False)
                result_text = str(result.get("result", result.get("error", "")))

                self.state.update(
                    instruction=f"[STREAM] {action.name}",
                    result=result_text,
                    action=action.name,
                    success=success,
                )

                yield f"\n\n--- Ejecutado: {action.name} ---\n{result_text}\n"

    def _execute_action(self, name: str, params: dict) -> dict:
        """Ejecuta una acción registrada."""
        action_class = registry.get(name)
        if action_class is None:
            error = f"Acción '{name}' no encontrada. Disponibles: {registry.list_names()}"
            self.log(f"⚠ {error}")
            return {"success": False, "error": error}

        try:
            action = action_class()
            self.log(f"Ejecutando {name}...")
            result = action.execute(**params)
            status = "✅" if result.get("success") else "❌"
            self.log(f"{status} {name} completado")
            return result
        except Exception as e:
            error = f"Error ejecutando {name}: {e}"
            self.log(f"❌ {error}")
            return {"success": False, "error": error}

    def get_stats(self) -> dict:
        """Estadísticas de la sesión actual."""
        return {
            "actions": self.state.action_count,
            "errors": self.state.error_count,
            "success_rate": f"{self.state.get_success_rate():.1f}%",
            "files_created": len(self.state.files_created),
            "history_messages": self.brain.get_history_length(),
            "last_exec_ms": self._last_exec_time,
            "uptime": str(datetime.now() - self.state.created_at).split(".")[0],
        }

    def reset(self):
        """Reinicia sesión y estado."""
        self.brain.reset_session()
        self.state = State()
        self._last_exec_time = 0
        self.log("Agente reiniciado")

    def __repr__(self):
        return f"Agent(model={self.brain.model_name}, {self.state})"
