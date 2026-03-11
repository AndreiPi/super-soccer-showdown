import json
from typing import Any

from super_soccer_showdown.domain.entities import Lineup, Team, Universe
from infrastructure.src.super_soccer_showdown.service.exceptions import DomainError
from super_soccer_showdown.entrypoints.lambda_api.bootstrap import (
    build_generate_showdown_use_case,
    build_generate_team_use_case,
)

_generate_team_use_case = build_generate_team_use_case()
_generate_showdown_use_case = build_generate_showdown_use_case()


def generate_universe_team_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    try:
        universe = Universe(event.get("pathParameters", {}).get("universe", "").lower())
        query = event.get("queryStringParameters") or {}
        lineup = _lineup_from_payload(query)

        team = _generate_team_use_case.execute(universe=universe, lineup=lineup)
        return _response(200, _team_to_dict(team))
    except ValueError as error:
        return _response(400, {"message": str(error)})
    except DomainError as error:
        return _response(422, {"message": str(error)})
    except Exception:
        return _response(500, {"message": "Unexpected server error."})


def generate_showdown_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    try:
        body = _load_json_body(event)

        starwars_lineup = _lineup_from_payload(body.get("starwars", {}))
        pokemon_lineup = _lineup_from_payload(body.get("pokemon", {}))

        teams = _generate_showdown_use_case.execute(
            starwars_lineup=starwars_lineup,
            pokemon_lineup=pokemon_lineup,
        )

        return _response(
            200,
            {
                "starwars": _team_to_dict(teams["starwars"]),
                "pokemon": _team_to_dict(teams["pokemon"]),
            },
        )
    except json.JSONDecodeError:
        return _response(400, {"message": "Request body must be valid JSON."})
    except ValueError as error:
        return _response(400, {"message": str(error)})
    except DomainError as error:
        return _response(422, {"message": str(error)})
    except Exception:
        return _response(500, {"message": "Unexpected server error."})


def _lineup_from_payload(payload: dict[str, Any]) -> Lineup:
    defenders = int(payload.get("defenders", 2))
    attackers = int(payload.get("attackers", 2))
    return Lineup(defenders=defenders, attackers=attackers)


def _load_json_body(event: dict[str, Any]) -> dict[str, Any]:
    raw_body = event.get("body")
    if raw_body in (None, ""):
        return {}
    return json.loads(raw_body)


def _team_to_dict(team: Team) -> dict[str, Any]:
    return {
        "universe": team.universe.value,
        "lineup": {
            "defenders": team.lineup.defenders,
            "attackers": team.lineup.attackers,
        },
        "players": [
            {
                "Name": player.name,
                "Weight": player.weight_kg,
                "Height": player.height_cm,
                "Position": player.position.value,
            }
            for player in team.players
        ],
    }


def _response(status_code: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }
