"""
parser.py — Parser de respuestas del modelo.

El agente habla en un formato estructurado con bloques [ACTION:...].
Este módulo extrae las acciones de la respuesta para que el agente
las pueda ejecutar.
"""

import re
from dataclasses import dataclass


@dataclass
class ParsedAction:
    """Acción parseada de la respuesta del modelo."""
    name: str
    params: dict
    raw: str


def parse_response(text: str) -> tuple:
    """
    Parsea la respuesta del modelo.

    Retorna:
      (actions: list[ParsedAction], message: str)

    actions = lista de acciones detectadas
    message = texto libre (sin los bloques de acción)
    """
    actions = []
    message = text

    # Buscar bloques [ACTION:nombre]...[/ACTION]
    pattern = r'\[ACTION:(\w+)\]\s*(.*?)\s*\[/ACTION\]'
    matches = re.finditer(pattern, text, re.DOTALL)

    for match in matches:
        action_name = match.group(1).strip()
        params_raw = match.group(2).strip()

        # Parsear parámetros (formato "key: value" por línea)
        params = {}
        current_key = None
        current_value_lines = []

        for line in params_raw.split("\n"):
            # Detectar nueva key con formato "key: value"
            key_match = re.match(r'^(\w+):\s*(.*)', line)
            if key_match:
                # Guardar key anterior si existe
                if current_key is not None:
                    params[current_key] = "\n".join(current_value_lines).strip()
                current_key = key_match.group(1)
                current_value_lines = [key_match.group(2)]
            else:
                # Continuación de valor multilínea
                if current_key is not None:
                    current_value_lines.append(line)

        # Guardar última key
        if current_key is not None:
            params[current_key] = "\n".join(current_value_lines).strip()

        actions.append(ParsedAction(
            name=action_name,
            params=params,
            raw=match.group(0),
        ))

        # Quitar el bloque de acción del mensaje
        message = message.replace(match.group(0), "").strip()

    return actions, message


def has_action(text: str) -> bool:
    """Verifica rápidamente si la respuesta contiene acciones."""
    return bool(re.search(r'\[ACTION:\w+\]', text))
