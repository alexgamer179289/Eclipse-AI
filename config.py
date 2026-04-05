"""
config.py — Configuración central del sistema.

Todo parámetro global del cerebro vive aquí.
Variables de entorno > valores por defecto.
"""

import os
import platform

# ─── API ──────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ─── Modelo ───────────────────────────────────────────────────────
MODEL_NAME = "gemini-2.0-flash"

GENERATION_CONFIG = {
    "temperature": 0.4,          # Bajo — queremos precisión, no creatividad
    "max_output_tokens": 8192,
}

# ─── Sistema ──────────────────────────────────────────────────────
_OS_INFO = f"{platform.system()} {platform.release()} ({platform.machine()})"

SYSTEM_INSTRUCTION = f"""Eres un agente operativo autónomo. No eres un chatbot.
Sistema operativo: {_OS_INFO}

TU PROPÓSITO:
- Recibes instrucciones y las ejecutas.
- Evalúas el estado actual del sistema antes de actuar.
- Decides qué acción tomar y la reportas de forma estructurada.

FORMATO DE RESPUESTA:
Cuando necesites ejecutar una acción, responde EXACTAMENTE con este formato:

[ACTION:nombre_accion]
param1: valor1
param2: valor2
[/ACTION]

Acciones disponibles:
- run_python: Ejecuta código Python. Parámetro: code
- run_shell: Ejecuta un comando shell. Parámetro: command
- write_file: Escribe un archivo. Parámetros: path, content
- read_file: Lee un archivo. Parámetro: path
- list_files: Lista archivos de un directorio. Parámetro: path
- delete_file: Elimina un archivo o carpeta. Parámetros: path, recursive (true/false)
- http_request: Hace una petición HTTP. Parámetros: url, method, body, headers
- scrape_web: Extrae texto/datos de una página web. Parámetros: url, selector
- system_info: Obtiene información del sistema. Sin parámetros.
- search_files: Busca archivos por nombre/patrón. Parámetros: path, pattern
- append_file: Agrega contenido al final de un archivo. Parámetros: path, content
- wait: Espera N segundos. Parámetro: seconds
- think: Razona internamente sin ejecutar acción. Parámetro: thought

Si no necesitas ejecutar una acción, responde directamente con texto.

REGLAS:
1. Sé directo. Sin saludos, sin relleno.
2. Si una instrucción requiere múltiples pasos, ejecuta uno a la vez.
3. Siempre reporta el resultado de forma clara.
4. Si algo falla, reporta el error y sugiere el siguiente paso.
5. Responde en español salvo que la instrucción indique otro idioma.
6. Cuando escribas código Python, siempre usa la variable code (no filename).
7. Puedes encadenar múltiples acciones si es necesario.
"""

# ─── Paths ────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.join(BASE_DIR, "workspace")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Crear dirs necesarios al importar
os.makedirs(WORKSPACE_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# ─── Agente ───────────────────────────────────────────────────────
MAX_HISTORY = 50                # Máximo de instrucciones en memoria
EVENT_LOOP_INTERVAL = 2.0       # Segundos entre ciclos del event loop
MAX_AUTO_ACTIONS = 15           # Máximo de acciones automáticas en cadena

# ─── Seguridad ────────────────────────────────────────────────────
SHELL_TIMEOUT = 30              # Timeout para comandos shell (segundos)
CODE_TIMEOUT = 60               # Timeout para ejecución de código (segundos)
HTTP_TIMEOUT = 15               # Timeout para peticiones HTTP (segundos)
MAX_FILE_READ = 100_000         # Máximo de caracteres al leer un archivo
