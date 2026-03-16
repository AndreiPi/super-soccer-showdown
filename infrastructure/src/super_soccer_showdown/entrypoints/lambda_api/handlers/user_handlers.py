import json
import logging
from typing import Any
from super_soccer_showdown.entrypoints.lambda_api.bootstrap import (
    build_refresh_jwt_token_use_case,
    build_register_user_use_case,
    run_handler,
)
from super_soccer_showdown.service.jwt_service import get_jwt_payload

from .handlers_utils import response, load_json_body

logger = logging.getLogger("super_soccer_showdown")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")



def register_user_handler(event, _context):
    return run_handler(register_user_async(event))


def refresh_jwt_token_handler(event, _context):
    return run_handler(refresh_jwt_token_async(event))


async def register_user_async(event: dict[str, Any]) -> dict[str, Any]:
    logger.info(f"Request to register_user_handler: {event}")
    try:
        body = load_json_body(event)
        username = body.get("username", "").strip()

        if not username:
            return response(400, {"message": "Username is required."})
        
        use_case = build_register_user_use_case()
        result = await use_case.execute(username)
        return response(
            201,
            {
                "user_id": result["user_id"],
                "username": result["username"],
                "jwt_token": result["jwt_token"],
            },
        )
    except json.JSONDecodeError:
        return response(400, {"message": "Request body must be valid JSON."})
    except ValueError as error:
        return response(409, {"message": str(error)})
    except Exception as error:
        logger.error(f"Unexpected error: {str(error)}")
        return response(500, {"message": "Unexpected server error."})


async def refresh_jwt_token_async(event: dict[str, Any]) -> dict[str, Any]:
    logger.info(f"Request to refresh_jwt_token_handler: {event}")
    try:
        user_id = (event.get("queryStringParameters", {}) or {}).get("user_id")
        logger.info(f"Extracted user_id from query parameters: {user_id}")
        if user_id in (None, "") or not user_id.isnumeric():
            jwt_payload = get_jwt_payload(event, verify_exp=False)
            user_id = jwt_payload.get("user_id")
            logger.info(f"Extracted user_id from JWT payload: {user_id}")

        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return response(400, {"message": "Query parameter 'user_id' must be an integer."})
        


        use_case = build_refresh_jwt_token_use_case()
        result = await use_case.execute(int(user_id))
        return response(
            200,
            {
                "user_id": result["user_id"],
                "username": result["username"],
                "jwt_token": result["jwt_token"],
            },
        )
    except ValueError as error:
        error_text = str(error)
        if "token" in error_text.lower() or "authorization" in error_text.lower():
            return response(401, {"message": f"User id invalid in path or token."})
        return response(404, {"message": error_text})
    except Exception as error:
        logger.error(f"Unexpected error: {str(error)}")
        return response(500, {"message": "Unexpected server error."})

