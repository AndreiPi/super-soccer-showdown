import json
import os
from enum import Enum
from typing import Any
from pydantic import TypeAdapter
from super_soccer_showdown.domain.entities import Lineup


JSON_ADAPTER = TypeAdapter(Any)
TEAM_SIZE = int(os.environ.get("TEAM_SIZE", 5))

def _pydantic_fallback(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dict__"):
        return value.__dict__
    return str(value)


def to_jsonable(payload: Any) -> Any:
    return JSON_ADAPTER.dump_python(payload, mode="json", fallback=_pydantic_fallback)

def lineup_from_payload(payload: dict[str, Any]) -> Lineup:
    try:
        defenders = int(payload.get("defenders", 0))
        attackers = int(payload.get("attackers", 0))
    except (TypeError, ValueError):
        raise ValueError("Defenders and attackers must be integers.")
    if attackers + defenders == 0:
        attackers = (TEAM_SIZE - 1) // 2
        defenders = TEAM_SIZE - 1 - attackers
    elif attackers == 0:
        attackers = TEAM_SIZE - 1 - defenders
    elif defenders == 0:
        defenders = TEAM_SIZE - 1 - attackers
    

    if defenders + attackers + 1 > TEAM_SIZE:
        raise ValueError("Lineup exceeds team size limit.")
    if attackers + defenders < TEAM_SIZE - 1:
        raise ValueError("Lineup must fill all available positions.")
    if attackers < 1:
        raise ValueError("Lineup must have at least one attacker.")
    if defenders < 1:
        raise ValueError("Lineup must have at least one defender.")
    return Lineup(defenders=defenders, attackers=attackers)


def load_json_body(event: dict[str, Any]) -> dict[str, Any]:
    raw_body = event.get("body")
    if raw_body in (None, ""):
        return {}
    return json.loads(raw_body)


def response(status_code: int, payload: Any) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(to_jsonable(payload)),
    }