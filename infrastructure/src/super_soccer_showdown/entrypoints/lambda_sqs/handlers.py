import json
import logging
from typing import Any

from super_soccer_showdown.domain.entities import Lineup
from infrastructure.src.super_soccer_showdown.service.exceptions import DomainError
from super_soccer_showdown.entrypoints.lambda_api.bootstrap import build_generate_showdown_use_case

logger = logging.getLogger(__name__)

_generate_showdown_use_case = build_generate_showdown_use_case()


def process_showdown_queue_handler(event: dict[str, Any], _context: Any) -> None:
    for record in event.get("Records", []):
        _process_record(record)


def _process_record(record: dict[str, Any]) -> None:
    message_id = record.get("messageId", "<unknown>")
    try:
        body = json.loads(record.get("body", "{}"))
        starwars_lineup = _lineup_from_payload(body.get("starwars", {}))
        pokemon_lineup = _lineup_from_payload(body.get("pokemon", {}))

        teams = _generate_showdown_use_case.execute(
            starwars_lineup=starwars_lineup,
            pokemon_lineup=pokemon_lineup,
        )

        logger.info(
            "Showdown generated for message %s: starwars=%s pokemon=%s",
            message_id,
            teams["starwars"].players,
            teams["pokemon"].players,
        )
    except json.JSONDecodeError:
        logger.error("Message %s has invalid JSON body — skipping.", message_id)
    except ValueError as error:
        logger.error("Message %s has invalid lineup values: %s — skipping.", message_id, error)
    except DomainError as error:
        logger.error("Domain error for message %s: %s — skipping.", message_id, error)
    except Exception:
        logger.exception("Unexpected error processing message %s.", message_id)
        raise


def _lineup_from_payload(payload: dict[str, Any]) -> Lineup:
    defenders = int(payload.get("defenders", 2))
    attackers = int(payload.get("attackers", 2))
    return Lineup(defenders=defenders, attackers=attackers)
