"""
gemini.py — Cliente del modelo Gemini.

Wrapper aislado sobre la SDK google-genai. El resto del sistema
nunca toca la SDK directamente — si cambia la API, se toca aquí.
Soporta: respuestas simples, sesiones con historial, y streaming.
"""

from google import genai
from google.genai import types
from config import GEMINI_API_KEY, MODEL_NAME, GENERATION_CONFIG, SYSTEM_INSTRUCTION


class GeminiClient:
    """Wrapper sobre Gemini — el modelo nativo del cerebro."""

    def __init__(self, api_key: str = None, model: str = None, system: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model or MODEL_NAME

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY no configurada. "
                "Exporta: set GEMINI_API_KEY=tu_clave"
            )

        self.client = genai.Client(api_key=self.api_key)
        self._system = system or SYSTEM_INSTRUCTION
        self._config = types.GenerateContentConfig(
            system_instruction=self._system,
            temperature=GENERATION_CONFIG.get("temperature", 0.4),
            max_output_tokens=GENERATION_CONFIG.get("max_output_tokens", 8192),
        )

        # Historial para sesión de chat
        self._history = []

    # ─── Respuesta directa (sin historial) ────────────────────────
    def send(self, instruction: str) -> str:
        """Una instrucción, una respuesta. Sin contexto previo."""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=instruction,
                config=self._config,
            )
            return response.text
        except Exception as e:
            return f"[Error del modelo]: {e}"

    # ─── Sesión con historial ─────────────────────────────────────
    def start_session(self, history: list = None):
        """Inicia sesión de chat. Opcionalmente con historial previo."""
        self._history = history or []

    def chat(self, message: str) -> str:
        """Envía mensaje dentro de sesión activa con historial manual."""
        # Construir contenido con historial
        contents = list(self._history)
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=message)],
        ))

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=self._config,
            )
            response_text = response.text

            # Agregar al historial
            self._history.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=message)],
            ))
            self._history.append(types.Content(
                role="model",
                parts=[types.Part.from_text(text=response_text)],
            ))

            # Truncar historial si es muy largo (mantener últimos 40 turnos)
            if len(self._history) > 80:
                self._history = self._history[-40:]

            return response_text

        except Exception as e:
            # Reintentar con historial reducido
            try:
                self._history = self._history[-10:] if self._history else []
                contents = list(self._history)
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=message)],
                ))
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=self._config,
                )
                response_text = response.text

                self._history.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=message)],
                ))
                self._history.append(types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=response_text)],
                ))

                return response_text
            except Exception as e2:
                return f"[Error del modelo]: {e2}"

    def get_history(self) -> list:
        """Retorna el historial de la sesión actual."""
        return self._history

    def get_history_length(self) -> int:
        """Retorna la cantidad de mensajes en el historial."""
        return len(self._history)

    def reset_session(self):
        """Mata la sesión actual."""
        self._history = []

    # ─── Streaming ─────────────────────────────────────────────────
    def stream(self, instruction: str):
        """
        Genera respuesta en streaming — retorna un generador de chunks.
        Útil para respuestas largas o feedback en tiempo real.
        """
        try:
            response = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=instruction,
                config=self._config,
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"[Error del modelo]: {e}"

    def chat_stream(self, message: str):
        """Streaming dentro de sesión con historial."""
        contents = list(self._history)
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=message)],
        ))

        full_response = ""
        try:
            response = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=self._config,
            )
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    yield chunk.text

            # Guardar en historial
            self._history.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=message)],
            ))
            self._history.append(types.Content(
                role="model",
                parts=[types.Part.from_text(text=full_response)],
            ))
        except Exception as e:
            yield f"[Error del modelo]: {e}"

    # ─── Multimodal ───────────────────────────────────────────────
    def send_with_media(self, instruction: str, media_path: str) -> str:
        """
        Envía instrucción + archivo multimedia (imagen, audio, video).
        Gemini es nativo multimodal — procesa todo en el mismo flujo.
        """
        try:
            media_file = self.client.files.upload(file=media_path)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[instruction, media_file],
                config=self._config,
            )
            return response.text
        except Exception as e:
            return f"[Error multimodal]: {e}"

    # ─── Info ─────────────────────────────────────────────────────
    def __repr__(self):
        return f"GeminiClient(model={self.model_name})"
