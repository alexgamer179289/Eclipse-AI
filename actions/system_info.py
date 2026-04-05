"""
system_info.py — Acción: información del sistema.

El agente puede consultar recursos del sistema:
CPU, RAM, disco, red, SO, etc.
"""

import platform
import os

from actions.base import Action
from actions.registry import register


@register
class SystemInfo(Action):
    name = "system_info"
    description = "Obtiene información del sistema (CPU, RAM, disco, SO)"

    def execute(self, **kwargs) -> dict:
        try:
            info_lines = []

            # SO
            info_lines.append(f"🖥️ Sistema: {platform.system()} {platform.release()}")
            info_lines.append(f"   Versión: {platform.version()}")
            info_lines.append(f"   Máquina: {platform.machine()}")
            info_lines.append(f"   Procesador: {platform.processor()}")
            info_lines.append(f"   Python: {platform.python_version()}")
            info_lines.append(f"   Usuario: {os.getenv('USERNAME', os.getenv('USER', 'desconocido'))}")
            info_lines.append(f"   Home: {os.path.expanduser('~')}")

            # psutil (si disponible)
            try:
                import psutil

                # CPU
                cpu_percent = psutil.cpu_percent(interval=0.5)
                cpu_count = psutil.cpu_count()
                cpu_freq = psutil.cpu_freq()
                info_lines.append(f"\n⚡ CPU:")
                info_lines.append(f"   Uso: {cpu_percent}%")
                info_lines.append(f"   Núcleos: {cpu_count}")
                if cpu_freq:
                    info_lines.append(f"   Frecuencia: {cpu_freq.current:.0f} MHz")

                # RAM
                mem = psutil.virtual_memory()
                info_lines.append(f"\n💾 Memoria RAM:")
                info_lines.append(f"   Total: {mem.total / (1024**3):.1f} GB")
                info_lines.append(f"   Usada: {mem.used / (1024**3):.1f} GB ({mem.percent}%)")
                info_lines.append(f"   Libre: {mem.available / (1024**3):.1f} GB")

                # Disco
                disk = psutil.disk_usage("/")
                info_lines.append(f"\n💽 Disco (/):")
                info_lines.append(f"   Total: {disk.total / (1024**3):.1f} GB")
                info_lines.append(f"   Usado: {disk.used / (1024**3):.1f} GB ({disk.percent}%)")
                info_lines.append(f"   Libre: {disk.free / (1024**3):.1f} GB")

                # Red
                net = psutil.net_if_addrs()
                info_lines.append(f"\n🌐 Interfaces de red: {len(net)}")
                for name, addrs in list(net.items())[:5]:
                    for addr in addrs:
                        if addr.family.name == "AF_INET":
                            info_lines.append(f"   {name}: {addr.address}")

                # Uptime
                import time
                boot = psutil.boot_time()
                uptime_secs = time.time() - boot
                hours = int(uptime_secs // 3600)
                mins = int((uptime_secs % 3600) // 60)
                info_lines.append(f"\n⏱️ Uptime: {hours}h {mins}m")

            except ImportError:
                info_lines.append("\n(psutil no instalado — instalar para más detalles)")

            result = "\n".join(info_lines)
            return {"success": True, "result": result}

        except Exception as e:
            return {"success": False, "error": str(e)}
