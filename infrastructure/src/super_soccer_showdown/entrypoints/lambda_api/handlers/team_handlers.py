import logging
from typing import Any

from super_soccer_showdown.domain.entities import Universe
from super_soccer_showdown.service.exceptions import DomainError
from super_soccer_showdown.entrypoints.lambda_api.bootstrap import (
    build_generate_team_use_case,
    build_list_teams_use_case,
    run_handler,
)
from super_soccer_showdown.service.jwt_service import get_jwt_payload

from .handlers_utils import lineup_from_payload, load_json_body, response


logger = logging.getLogger("super_soccer_showdown")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

def generate_universe_team_handler(event, _context):
    return run_handler(generate_universe_team(event))


def list_teams_handler(event, _context):
    return run_handler(list_teams(event))

async def generate_universe_team(event: dict[str, Any]) -> dict[str, Any]:
    logger.info(f"Request to generate_universe_team_handler: {event}")
    try:
        jwt_payload = get_jwt_payload(event)
        user_id = jwt_payload.get("user_id")
        if user_id is None:
            return response(401, {"message": "Unauthorized: Invalid user"})
    except Exception as auth_error:
        logger.error(f"Unauthorized access: {auth_error}")
        return response(401, {"message": "Unauthorized: " + str(auth_error)})

    try:
        universe = Universe(event.get("pathParameters", {}).get("universe", "").lower())
        body = load_json_body(event)
        lineup = lineup_from_payload(body)
        generate_team_use_case = build_generate_team_use_case()
        team = await generate_team_use_case.execute(user_id=user_id, universe=universe, lineup=lineup)
        return response(201, team)
    except ValueError as error:
        return response(400, {"message": str(error)})
    except DomainError as error:
        return response(422, {"message": str(error)})
    except Exception as error:
        logger.error(f"Unexpected error: {str(error)}")
        return response(500, {"message": "Unexpected server error."})


async def list_teams(event: dict[str, Any]) -> dict[str, Any]:
    logger.info(f"Request to list_teams_handler: {event}")
    try:
        get_jwt_payload(event)
    except Exception as auth_error:
        logger.error(f"Unauthorized access: {auth_error}")
        return response(401, {"message": "Unauthorized: " + str(auth_error)})

    try:
        query = event.get("queryStringParameters") or {}
        page = int(query.get("page", "1"))
        page_size = int(query.get("page_size", "10"))
        universe_raw = query.get("universe")
        user_id_raw = query.get("user_id")

        universe = None
        if universe_raw not in (None, ""):
            universe = Universe(str(universe_raw).lower())

        owner_user_id = None
        if user_id_raw not in (None, ""):
            owner_user_id = int(user_id_raw)

        list_teams_use_case = build_list_teams_use_case()
        teams_payload = await list_teams_use_case.execute(
            page=page,
            page_size=page_size,
            universe=universe,
            owner_user_id=owner_user_id,
        )
        return response(200, teams_payload)
    except ValueError as error:
        return response(400, {"message": str(error)})
    except DomainError as error:
        return response(422, {"message": str(error)})
    except Exception as error:
        logger.error(f"Unexpected error: {str(error)}")
        return response(500, {"message": "Unexpected server error."})


