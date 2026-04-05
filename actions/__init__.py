"""
Acciones del agente.

Al importar este paquete se cargan y registran automáticamente
todas las acciones disponibles.
"""

from actions import registry

# Importar módulos para que se auto-registren con @register
from actions import run_code
from actions import shell
from actions import file_ops
from actions import web
from actions import think
from actions import system_info
