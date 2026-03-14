import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any


def _server_url(event: dict[str, Any]) -> str:
    headers = event.get("headers") or {}
    host = headers.get("host") or headers.get("Host") or ""
    proto = headers.get("x-forwarded-proto") or headers.get("X-Forwarded-Proto") or "https"
    request_context = event.get("requestContext") or {}
    stage = (request_context.get("stage") or "").strip()

    is_local = not host or "localhost" in host or "127.0.0.1" in host
    if is_local:
        return f"http://{host}" if host else "/"

    base = f"{proto}://{host}"
    if stage and stage != "$default":
        return f"{base}/{stage}"
    return base


def _json_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def _html_response(html: str) -> dict[str, Any]:
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/html; charset=utf-8"},
        "body": html,
    }


@lru_cache(maxsize=1)
def _load_openapi_template() -> dict[str, Any]:
    spec_path = Path(__file__).with_name("openapi_spec.json")
    return json.loads(spec_path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_swagger_ui_html() -> str:
  html_path = Path(__file__).with_name("swagger_ui.html")
  return html_path.read_text(encoding="utf-8")


def _build_openapi_spec(event: dict[str, Any]) -> dict[str, Any]:
    spec = deepcopy(_load_openapi_template())
    spec["servers"] = [{"url": _server_url(event)}]
    return spec


def _build_swagger_ui_html() -> str:
    return _load_swagger_ui_html()


def docs_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    path = event.get("rawPath") or event.get("path") or ""
    if path.endswith("/openapi.json") or path == "/openapi.json":
        return _json_response(_build_openapi_spec(event))
    return _html_response(_build_swagger_ui_html())
