import logging
from typing import Any

from super_soccer_showdown.entrypoints.lambda_api.bootstrap import build_sync_players_catalog_use_case, run_handler
from super_soccer_showdown.service.exceptions import DomainError
from super_soccer_showdown.service.jwt_service import get_jwt_payload

from .handlers_utils import response

logger = logging.getLogger("super_soccer_showdown")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def player_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    return run_handler(sync_players_catalog(event))


async def sync_players_catalog(event: dict[str, Any]) -> dict[str, Any]:
    logger.info(f"Request to player_handler: {event}")
    try:
        use_case = build_sync_players_catalog_use_case()
        result = await use_case.execute()
        return response(200, result)
    except ValueError as error:
        return response(400, {"message": str(error)})
    except DomainError as error:
        return response(422, {"message": str(error)})
    except Exception as error:
        logger.error(f"Unexpected error: {str(error)}")
        return response(500, {"message": "Unexpected server error."})
