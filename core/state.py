"""
state.py — Estado del sistema.

El agente evalúa el estado antes de cada decisión.
Aquí se guarda: qué pasó, qué hay activo, qué datos existen,
qué errores ocurrieron, y cualquier señal relevante.
"""

from datetime import datetime
from collections import deque
from config import MAX_HISTORY


class State:
    """Estado mutable del sistema — el agente lo consulta antes de actuar."""

    def __init__(self):
        self.created_at = datetime.now()
        self.last_instruction = None
        self.last_result = None
        self.last_error = None
        self.history = deque(maxlen=MAX_HISTORY)
        self.context = {}          # Datos arbitrarios compartidos entre acciones
        self.pending_tasks = []    # Tareas en cola
        self.active_events = []    # Eventos que el agente está monitoreando
        self.action_count = 0      # Total de acciones ejecutadas en esta sesión
        self.error_count = 0       # Total de errores en esta sesión
        self.files_created = []    # Archivos creados por el agente
        self.session_notes = []    # Notas de sesión

    def update(self, instruction: str, result: str, action: str = None, success: bool = True):
        """Registra una instrucción ejecutada y su resultado."""
        self.last_instruction = instruction
        self.last_result = result
        self.last_error = None if success else result
        self.action_count += 1

        if not success:
            self.error_count += 1

        self.history.append({
            "instruction": instruction,
            "result": result[:500],    # Trunca para no saturar contexto
            "action": action,
            "success": success,
            "timestamp": datetime.now().isoformat(),
        })

    def track_file(self, filepath: str):
        """Registra un archivo creado por el agente."""
        if filepath not in self.files_created:
            self.files_created.append(filepath)

    def add_note(self, note: str):
        """Agrega una nota de sesión."""
        self.session_notes.append({
            "note": note,
            "timestamp": datetime.now().isoformat(),
        })

    def set(self, key: str, value):
        """Guarda dato en contexto compartido."""
        self.context[key] = value

    def get(self, key: str, default=None):
        """Consulta dato del contexto."""
        return self.context.get(key, default)

    def add_task(self, task: str):
        """Agrega tarea pendiente."""
        self.pending_tasks.append({
            "task": task,
            "added": datetime.now().isoformat(),
        })

    def complete_task(self, index: int = 0):
        """Marca tarea como completada."""
        if 0 <= index < len(self.pending_tasks):
            return self.pending_tasks.pop(index)
        return None

    def add_event(self, event_name: str, condition: str):
        """Registra un evento que el agente debe monitorear."""
        self.active_events.append({
            "name": event_name,
            "condition": condition,
            "registered": datetime.now().isoformat(),
        })

    def remove_event(self, event_name: str):
        """Elimina un evento del monitoreo."""
        self.active_events = [e for e in self.active_events if e["name"] != event_name]

    def get_success_rate(self) -> float:
        """Tasa de éxito de acciones."""
        if self.action_count == 0:
            return 100.0
        return ((self.action_count - self.error_count) / self.action_count) * 100

    def get_recent_history(self, n: int = 5) -> list:
        """Últimas n acciones del historial."""
        return list(self.history)[-n:]

    def summary(self) -> str:
        """Resumen compacto del estado para inyectar al modelo."""
        lines = [f"[Estado — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"]
        lines.append(f"  Acciones ejecutadas: {self.action_count} (éxito: {self.get_success_rate():.0f}%)")

        if self.last_instruction:
            instr = self.last_instruction[:80]
            lines.append(f"  Última instrucción: {instr}")

        if self.last_error:
            lines.append(f"  ⚠ Último error: {self.last_error[:100]}")

        if self.pending_tasks:
            lines.append(f"  Tareas pendientes: {len(self.pending_tasks)}")
            for i, t in enumerate(self.pending_tasks[:3]):
                lines.append(f"    {i+1}. {t['task'][:60]}")

        if self.active_events:
            lines.append(f"  Eventos activos: {[e['name'] for e in self.active_events]}")

        if self.context:
            keys = list(self.context.keys())[:10]
            lines.append(f"  Contexto: {keys}")

        if self.files_created:
            lines.append(f"  Archivos creados: {len(self.files_created)}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serializa el estado completo."""
        return {
            "created_at": self.created_at.isoformat(),
            "action_count": self.action_count,
            "error_count": self.error_count,
            "success_rate": self.get_success_rate(),
            "last_instruction": self.last_instruction,
            "last_result": self.last_result,
            "last_error": self.last_error,
            "history": list(self.history),
            "context": self.context,
            "pending_tasks": self.pending_tasks,
            "active_events": self.active_events,
            "files_created": self.files_created,
            "session_notes": self.session_notes,
        }

    def __repr__(self):
        return f"State(actions={self.action_count}, errors={self.error_count}, tasks={len(self.pending_tasks)})"
