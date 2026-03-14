import json
from typing import Any


def _server_url(event: dict[str, Any]) -> str:
    stage = (event.get("requestContext") or {}).get("stage")
    if not stage or stage == "$default":
        return "/"
    return f"/{stage}"


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


def _build_openapi_spec(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Super Soccer Showdown API",
            "version": "1.0.0",
            "description": "REST API for registering users, generating universe teams, listing teams and matches, syncing player catalogs, and running showdowns.",
        },
        "servers": [{"url": _server_url(event)}],
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            },
            "schemas": {
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                    },
                    "required": ["message"],
                },
                "RegisterUserRequest": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string"},
                    },
                    "required": ["username"],
                },
                "AuthResponse": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "username": {"type": "string"},
                        "jwt_token": {"type": "string"},
                    },
                    "required": ["user_id", "username", "jwt_token"],
                },
                "LineupRequest": {
                    "type": "object",
                    "properties": {
                        "defenders": {"type": "integer", "minimum": 1},
                        "attackers": {"type": "integer", "minimum": 1},
                    },
                },
                "ShowdownRequest": {
                    "type": "object",
                    "properties": {
                        "team_1": {"type": "integer"},
                        "team_2": {"type": "integer"},
                    },
                    "required": ["team_1", "team_2"],
                },
                "GenericObject": {
                    "type": "object",
                    "additionalProperties": True,
                },
            },
        },
        "paths": {
            "/users/register": {
                "post": {
                    "summary": "Register a user",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/RegisterUserRequest"}
                            }
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "User created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AuthResponse"}
                                }
                            },
                        },
                        "400": {"description": "Invalid request"},
                        "409": {"description": "Username conflict"},
                    },
                }
            },
            "/users/token/refresh/{user_id}": {
                "get": {
                    "summary": "Refresh JWT token",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Refreshed token",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AuthResponse"}
                                }
                            },
                        },
                        "400": {"description": "Invalid user id"},
                        "404": {"description": "User not found"},
                    },
                }
            },
            "/teams": {
                "get": {
                    "summary": "List teams",
                    "security": [{"BearerAuth": []}],
                    "parameters": [
                        {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                        {"name": "page_size", "in": "query", "schema": {"type": "integer", "default": 10, "maximum": 100}},
                        {"name": "universe", "in": "query", "schema": {"type": "string", "enum": ["starwars", "pokemon"]}},
                        {"name": "user_id", "in": "query", "schema": {"type": "integer"}},
                    ],
                    "responses": {
                        "200": {
                            "description": "Paginated teams",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/GenericObject"}
                                }
                            },
                        },
                        "401": {"description": "Unauthorized"},
                    },
                }
            },
            "/teams/{universe}": {
                "post": {
                    "summary": "Generate a universe team",
                    "security": [{"BearerAuth": []}],
                    "parameters": [
                        {
                            "name": "universe",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "enum": ["starwars", "pokemon"]},
                        }
                    ],
                    "requestBody": {
                        "required": False,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/LineupRequest"}
                            }
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "Generated team",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/GenericObject"}
                                }
                            },
                        },
                        "400": {"description": "Invalid request"},
                        "401": {"description": "Unauthorized"},
                        "422": {"description": "Domain validation error"},
                    },
                }
            },
            "/showdown": {
                "post": {
                    "summary": "Generate a showdown",
                    "security": [{"BearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ShowdownRequest"}
                            }
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "Created showdown",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/GenericObject"}
                                }
                            },
                        },
                        "400": {"description": "Invalid request"},
                        "401": {"description": "Unauthorized"},
                        "422": {"description": "Domain validation error"},
                    },
                }
            },
            "/matches": {
                "get": {
                    "summary": "List matches",
                    "security": [{"BearerAuth": []}],
                    "parameters": [
                        {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                        {"name": "page_size", "in": "query", "schema": {"type": "integer", "default": 10, "maximum": 100}},
                        {"name": "user_id", "in": "query", "schema": {"type": "integer"}},
                    ],
                    "responses": {
                        "200": {
                            "description": "Paginated matches",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/GenericObject"}
                                }
                            },
                        },
                        "401": {"description": "Unauthorized"},
                    },
                }
            },
            "/players/sync": {
                "get": {
                    "summary": "Sync player catalogs",
                    "responses": {
                        "200": {
                            "description": "Sync result",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/GenericObject"}
                                }
                            },
                        },
                        "422": {"description": "Domain validation error"},
                    },
                }
            },
        },
    }


def _build_swagger_ui_html() -> str:
    return """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Super Soccer Showdown API Docs</title>
    <link rel=\"stylesheet\" href=\"https://unpkg.com/swagger-ui-dist@5/swagger-ui.css\" />
    <style>
      body { margin: 0; background: #faf7ef; }
      .topbar { display: none; }
    </style>
  </head>
  <body>
    <div id=\"swagger-ui\"></div>
    <script src=\"https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js\"></script>
    <script>
      window.onload = function() {
        window.ui = SwaggerUIBundle({
          url: 'openapi.json',
          dom_id: '#swagger-ui',
          deepLinking: true,
          displayRequestDuration: true,
          persistAuthorization: true,
        });
      };
    </script>
  </body>
</html>
"""


def docs_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    path = event.get("rawPath") or event.get("path") or ""
    if path.endswith("/openapi.json") or path == "/openapi.json":
        return _json_response(_build_openapi_spec(event))
    return _html_response(_build_swagger_ui_html())
