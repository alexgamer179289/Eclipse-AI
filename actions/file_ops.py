"""
file_ops.py — Acciones: operaciones con archivos.

Leer, escribir, listar, eliminar, buscar archivos.
Todo dentro del workspace por defecto.
"""

import os
import glob
import shutil
from datetime import datetime

from actions.base import Action
from actions.registry import register
from config import WORKSPACE_DIR, MAX_FILE_READ


def _ensure_workspace():
    os.makedirs(WORKSPACE_DIR, exist_ok=True)


def _safe_path(path: str) -> str:
    """Resuelve path relativo al workspace. Permite paths absolutos."""
    _ensure_workspace()
    if os.path.isabs(path):
        return path
    return os.path.join(WORKSPACE_DIR, path)


@register
class WriteFile(Action):
    name = "write_file"
    description = "Escribe contenido a un archivo"

    def execute(self, path: str = "", content: str = "", **kwargs) -> dict:
        if not path:
            return {"success": False, "error": "Se requiere 'path'"}

        filepath = _safe_path(path)
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            size = os.path.getsize(filepath)
            return {
                "success": True,
                "result": f"Archivo escrito: {filepath} ({size} bytes)",
                "path": filepath,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


@register
class AppendFile(Action):
    name = "append_file"
    description = "Agrega contenido al final de un archivo"

    def execute(self, path: str = "", content: str = "", **kwargs) -> dict:
        if not path:
            return {"success": False, "error": "Se requiere 'path'"}

        filepath = _safe_path(path)
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(content)
            size = os.path.getsize(filepath)
            return {
                "success": True,
                "result": f"Contenido agregado a: {filepath} ({size} bytes total)",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


@register
class ReadFile(Action):
    name = "read_file"
    description = "Lee el contenido de un archivo"

    def execute(self, path: str = "", **kwargs) -> dict:
        if not path:
            return {"success": False, "error": "Se requiere 'path'"}

        filepath = _safe_path(path)
        if not os.path.exists(filepath):
            return {"success": False, "error": f"No existe: {filepath}"}

        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(MAX_FILE_READ)

            truncated = os.path.getsize(filepath) > MAX_FILE_READ
            result = content
            if truncated:
                result += f"\n\n[... truncado a {MAX_FILE_READ} caracteres ...]"

            return {
                "success": True,
                "result": result,
                "size": os.path.getsize(filepath),
                "truncated": truncated,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


@register
class ListFiles(Action):
    name = "list_files"
    description = "Lista archivos y carpetas de un directorio"

    def execute(self, path: str = "", **kwargs) -> dict:
        target = _safe_path(path) if path else WORKSPACE_DIR
        _ensure_workspace()

        if not os.path.exists(target):
            return {"success": False, "error": f"No existe: {target}"}

        try:
            entries = []
            for item in sorted(os.listdir(target)):
                full = os.path.join(target, item)
                is_dir = os.path.isdir(full)
                if is_dir:
                    count = len(os.listdir(full))
                    entries.append(f"📁 {item}/ ({count} items)")
                else:
                    size = os.path.getsize(full)
                    if size < 1024:
                        size_str = f"{size}b"
                    elif size < 1024 * 1024:
                        size_str = f"{size/1024:.1f}KB"
                    else:
                        size_str = f"{size/(1024*1024):.1f}MB"
                    entries.append(f"📄 {item} ({size_str})")

            result = "\n".join(entries) if entries else "(directorio vacío)"
            return {"success": True, "result": result, "count": len(entries)}
        except Exception as e:
            return {"success": False, "error": str(e)}


@register
class DeleteFile(Action):
    name = "delete_file"
    description = "Elimina un archivo o carpeta"

    def execute(self, path: str = "", recursive: str = "false", **kwargs) -> dict:
        if not path:
            return {"success": False, "error": "Se requiere 'path'"}

        filepath = _safe_path(path)
        if not os.path.exists(filepath):
            return {"success": False, "error": f"No existe: {filepath}"}

        try:
            if os.path.isdir(filepath):
                if recursive.lower() == "true":
                    shutil.rmtree(filepath)
                    return {"success": True, "result": f"Carpeta eliminada recursivamente: {filepath}"}
                else:
                    os.rmdir(filepath)
                    return {"success": True, "result": f"Carpeta eliminada: {filepath}"}
            else:
                os.remove(filepath)
                return {"success": True, "result": f"Archivo eliminado: {filepath}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


@register
class SearchFiles(Action):
    name = "search_files"
    description = "Busca archivos por nombre o patrón glob"

    def execute(self, path: str = "", pattern: str = "*", **kwargs) -> dict:
        target = _safe_path(path) if path else WORKSPACE_DIR

        if not os.path.exists(target):
            return {"success": False, "error": f"No existe: {target}"}

        try:
            search_pattern = os.path.join(target, "**", pattern)
            matches = glob.glob(search_pattern, recursive=True)
            matches = matches[:50]  # Limitar resultados

            if matches:
                entries = []
                for m in matches:
                    rel = os.path.relpath(m, target)
                    is_dir = os.path.isdir(m)
                    entries.append(f"{'📁' if is_dir else '📄'} {rel}")
                result = "\n".join(entries)
            else:
                result = f"No se encontraron archivos con patrón '{pattern}'"

            return {"success": True, "result": result, "count": len(matches)}
        except Exception as e:
            return {"success": False, "error": str(e)}
