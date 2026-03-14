import json
import logging
from typing import Any

from super_soccer_showdown.service.exceptions import DomainError
from super_soccer_showdown.entrypoints.lambda_api.bootstrap import (
    build_generate_showdown_use_case,
    build_list_matches_use_case,
    run_handler,
)
from super_soccer_showdown.service.jwt_service import get_jwt_payload

from .handlers_utils import response, load_json_body

logger = logging.getLogger("super_soccer_showdown")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def generate_showdown_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    return run_handler(generate_showdown(event))


def list_matches_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    return run_handler(_list_matches(event))


async def generate_showdown(event: dict[str, Any]) -> dict[str, Any]:
    logger.info(f"Request to generate_showdown_handler: {event}")
    try:
        get_jwt_payload(event)
    except Exception as auth_error:
        logger.error(f"Unauthorized access: {auth_error}")
        return response(401, {"message": "Unauthorized: " + str(auth_error)})

    try:
        body = load_json_body(event)

        team_1_id = body.get("team_1", None)
        team_2_id = body.get("team_2", None)
        if team_1_id is None or team_2_id is None:
            return response(400, {"message": "Both team_1 and team_2 must be provided in the request body."})
        

        generate_showdown_use_case = build_generate_showdown_use_case()
        showdown = await generate_showdown_use_case.execute(
            team_1_id=team_1_id,
            team_2_id=team_2_id,
        )
        return response(201, showdown)
    except json.JSONDecodeError:
        return response(400, {"message": "Request body must be valid JSON."})
    except ValueError as error:
        return response(400, {"message": str(error)})
    except DomainError as error:
        return response(422, {"message": str(error)})
    except Exception as error:
        logger.error(f"Unexpected server error: {error}")
        return response(500, {"message": "Unexpected server error."})


async def _list_matches(event: dict[str, Any]) -> dict[str, Any]:
    logger.info(f"Request to list_matches_handler: {event}")
    try:
        get_jwt_payload(event)
    except Exception as auth_error:
        logger.error(f"Unauthorized access: {auth_error}")
        return response(401, {"message": "Unauthorized: " + str(auth_error)})

    try:
        query = event.get("queryStringParameters") or {}
        page = int(query.get("page", "1"))
        page_size = int(query.get("page_size", "10"))

        user_id = None
        user_id_raw = query.get("user_id")
        if user_id_raw not in (None, ""):
            user_id = int(user_id_raw)

        list_matches_use_case = build_list_matches_use_case()
        payload = await list_matches_use_case.execute(page=page, page_size=page_size, user_id=user_id)
        return response(200, payload)
    except ValueError as error:
        return response(400, {"message": str(error)})
    except DomainError as error:
        return response(422, {"message": str(error)})
    except Exception as error:
        logger.error(f"Unexpected server error: {error}")
        return response(500, {"message": "Unexpected server error."})


