"""
main.py — Punto de entrada del cerebro.

Modos de operación:
  1. Interactivo: loop de instrucciones por consola
  2. Instrucción directa: ejecuta una instrucción y sale
  3. Programático: importa Agent y úsalo desde otro código

Uso:
  python main.py                          → Modo interactivo
  python main.py "crea un script que..."  → Instrucción directa
"""

import sys
import os
import json
from datetime import datetime

# Path setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Colores para Windows
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init()
except ImportError:
    # Fallback sin colores
    class _Dummy:
        def __getattr__(self, _): return ""
    Fore = _Dummy()
    Style = _Dummy()

from core.agent import Agent
from actions import registry
from config import LOGS_DIR


def get_api_key() -> str:
    """Obtiene API key de env o la pide al usuario."""
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key

    print(f"\n{Fore.YELLOW}⚠️  GEMINI_API_KEY no encontrada en variables de entorno.{Style.RESET_ALL}")
    print("   Opciones:")
    print("   1. set GEMINI_API_KEY=tu_clave  (Windows)")
    print("   2. export GEMINI_API_KEY=tu_clave  (Linux/Mac)")
    print("   3. Ingresarla ahora:\n")
    key = input(f"   {Fore.CYAN}API Key: {Style.RESET_ALL}").strip()
    return key


def print_banner():
    """Banner de inicio."""
    print()
    print(f"{Fore.CYAN}╔══════════════════════════════════════════════════╗")
    print(f"║           🧠 AI BRAIN — Agente Operativo         ║")
    print(f"║                                                  ║")
    print(f"║   No es un chatbot. Es un operador autónomo.     ║")
    print(f"║   Instrucción → Evaluación → Ejecución → Reporte ║")
    print(f"╚══════════════════════════════════════════════════╝{Style.RESET_ALL}")


def print_actions():
    """Muestra acciones disponibles."""
    actions = registry.list_all()
    print(f"\n  {Fore.GREEN}Acciones disponibles:{Style.RESET_ALL}")
    for name, desc in actions.items():
        print(f"    {Fore.YELLOW}•{Style.RESET_ALL} {Fore.WHITE}{name}{Style.RESET_ALL}: {desc}")
    print()


def save_log(agent: Agent):
    """Guarda log de la sesión."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(LOGS_DIR, f"session_{timestamp}.json")

    log_data = {
        "timestamp": timestamp,
        "model": agent.brain.model_name,
        "stats": agent.get_stats(),
        "state": agent.state.to_dict(),
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    print(f"  {Fore.GREEN}📝 Log guardado: {filepath}{Style.RESET_ALL}")


def print_stats(agent: Agent):
    """Muestra estadísticas de la sesión."""
    stats = agent.get_stats()
    print(f"\n  {Fore.CYAN}📊 Estadísticas de sesión:{Style.RESET_ALL}")
    print(f"    Acciones ejecutadas: {stats['actions']}")
    print(f"    Errores: {stats['errors']}")
    print(f"    Tasa de éxito: {stats['success_rate']}")
    print(f"    Archivos creados: {stats['files_created']}")
    print(f"    Mensajes en historial: {stats['history_messages']}")
    print(f"    Última ejec.: {stats['last_exec_ms']}ms")
    print(f"    Uptime: {stats['uptime']}")
    print()


def interactive_mode(agent: Agent):
    """Modo interactivo — loop de instrucciones."""
    print_actions()
    print(f"  {Fore.MAGENTA}Comandos especiales:{Style.RESET_ALL}")
    print(f"    {Fore.YELLOW}/estado{Style.RESET_ALL}   → Ver estado del agente")
    print(f"    {Fore.YELLOW}/stats{Style.RESET_ALL}    → Ver estadísticas")
    print(f"    {Fore.YELLOW}/acciones{Style.RESET_ALL} → Ver acciones disponibles")
    print(f"    {Fore.YELLOW}/reset{Style.RESET_ALL}    → Reiniciar agente")
    print(f"    {Fore.YELLOW}/log{Style.RESET_ALL}      → Guardar log de sesión")
    print(f"    {Fore.YELLOW}/salir{Style.RESET_ALL}    → Terminar")
    print()

    while True:
        try:
            instruction = input(f"{Fore.GREEN}📋 >{Style.RESET_ALL} ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not instruction:
            continue

        # Comandos especiales
        if instruction.startswith("/"):
            cmd = instruction.lower()
            if cmd in ("/salir", "/exit", "/quit"):
                break
            elif cmd == "/estado":
                print(f"\n{Fore.CYAN}{agent.state.summary()}{Style.RESET_ALL}\n")
                continue
            elif cmd == "/stats":
                print_stats(agent)
                continue
            elif cmd == "/acciones":
                print_actions()
                continue
            elif cmd == "/reset":
                agent.reset()
                print(f"  {Fore.GREEN}🔄 Agente reiniciado{Style.RESET_ALL}\n")
                continue
            elif cmd == "/log":
                save_log(agent)
                print()
                continue
            elif cmd == "/historial":
                history = agent.state.get_recent_history(10)
                if history:
                    print(f"\n  {Fore.CYAN}📜 Últimas acciones:{Style.RESET_ALL}")
                    for i, h in enumerate(history):
                        status = "✅" if h["success"] else "❌"
                        print(f"    {status} {h['instruction'][:60]}")
                else:
                    print("  (sin historial)")
                print()
                continue
            else:
                print(f"  {Fore.RED}Comando desconocido: {instruction}{Style.RESET_ALL}\n")
                continue

        # Procesar instrucción
        print()
        try:
            result = agent.instruct(instruction)
            print(f"\n{Fore.CYAN}{'─' * 50}{Style.RESET_ALL}")
            print(result)
            print(f"{Fore.CYAN}{'─' * 50}{Style.RESET_ALL}\n")
        except Exception as e:
            print(f"\n  {Fore.RED}❌ Error: {e}{Style.RESET_ALL}\n")


def direct_mode(agent: Agent, instruction: str):
    """Modo directo — ejecuta instrucción y sale."""
    try:
        result = agent.instruct(instruction)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    print_banner()

    # Obtener API key
    api_key = get_api_key()
    if not api_key:
        print(f"  {Fore.RED}❌ Sin API key no hay cerebro. Saliendo.{Style.RESET_ALL}")
        sys.exit(1)

    # Crear agente
    try:
        agent = Agent(api_key=api_key)
        print(f"\n  {Fore.GREEN}✅ Agente:{Style.RESET_ALL} {agent.brain}")
        print(f"  {Fore.GREEN}✅ Acciones:{Style.RESET_ALL} {registry.list_names()}")
    except Exception as e:
        print(f"\n  {Fore.RED}❌ Error al inicializar: {e}{Style.RESET_ALL}")
        sys.exit(1)

    # Decidir modo
    if len(sys.argv) > 1:
        # Modo directo: python main.py "instrucción"
        instruction = " ".join(sys.argv[1:])
        direct_mode(agent, instruction)
    else:
        # Modo interactivo
        interactive_mode(agent)

    # Guardar log al salir
    if agent.state.action_count > 0:
        save_log(agent)

    stats = agent.get_stats()
    print(f"\n  {Fore.CYAN}📊 Sesión: {stats['actions']} acciones, {stats['success_rate']} éxito, {stats['uptime']} uptime{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}👋 Cerebro apagado.{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()
