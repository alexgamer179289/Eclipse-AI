"""
web.py — Acciones: peticiones HTTP y web scraping.

El agente puede hacer requests a cualquier URL y
extraer contenido de páginas web.
"""

import json
import requests

from actions.base import Action
from actions.registry import register
from config import HTTP_TIMEOUT


@register
class HttpRequest(Action):
    name = "http_request"
    description = "Realiza una petición HTTP (GET, POST, etc)"

    def execute(self, url: str = "", method: str = "GET", body: str = "",
                headers: str = "", **kwargs) -> dict:
        if not url:
            return {"success": False, "error": "Se requiere 'url'"}

        method = method.upper()

        # Parsear headers si vienen como string
        req_headers = {"User-Agent": "AI-Brain/1.0"}
        if headers:
            try:
                req_headers.update(json.loads(headers))
            except Exception:
                pass

        # Parsear body si viene como string
        req_body = None
        if body:
            try:
                req_body = json.loads(body)
            except Exception:
                req_body = body

        try:
            response = requests.request(
                method=method,
                url=url,
                json=req_body if isinstance(req_body, dict) else None,
                data=req_body if isinstance(req_body, str) else None,
                headers=req_headers,
                timeout=HTTP_TIMEOUT,
            )

            # Intentar parsear como JSON
            try:
                data = response.json()
                result_text = json.dumps(data, indent=2, ensure_ascii=False)
            except Exception:
                result_text = response.text

            # Truncar si es muy largo
            if len(result_text) > 3000:
                result_text = result_text[:3000] + "\n\n[... truncado ...]"

            return {
                "success": response.ok,
                "result": result_text,
                "status_code": response.status_code,
            }

        except requests.Timeout:
            return {"success": False, "error": f"Timeout ({HTTP_TIMEOUT}s)"}
        except requests.ConnectionError:
            return {"success": False, "error": f"No se pudo conectar a {url}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


@register
class ScrapeWeb(Action):
    name = "scrape_web"
    description = "Extrae texto o datos de una página web"

    def execute(self, url: str = "", selector: str = "", **kwargs) -> dict:
        if not url:
            return {"success": False, "error": "Se requiere 'url'"}

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return {"success": False, "error": "beautifulsoup4 no instalado. pip install beautifulsoup4"}

        try:
            response = requests.get(
                url,
                headers={"User-Agent": "AI-Brain/1.0"},
                timeout=HTTP_TIMEOUT,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Remover scripts y estilos
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            if selector:
                elements = soup.select(selector)
                if elements:
                    result = "\n\n".join(el.get_text(strip=True) for el in elements)
                else:
                    result = f"No se encontraron elementos con selector '{selector}'"
            else:
                # Extraer texto principal
                result = soup.get_text(separator="\n", strip=True)

            # Limpiar líneas vacías excesivas
            lines = [line for line in result.split("\n") if line.strip()]
            result = "\n".join(lines)

            # Truncar
            if len(result) > 4000:
                result = result[:4000] + "\n\n[... truncado ...]"

            return {
                "success": True,
                "result": result,
                "title": soup.title.string if soup.title else "(sin título)",
            }

        except requests.Timeout:
            return {"success": False, "error": f"Timeout ({HTTP_TIMEOUT}s)"}
        except requests.ConnectionError:
            return {"success": False, "error": f"No se pudo conectar a {url}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
