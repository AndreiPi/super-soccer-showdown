from __future__ import annotations
from datetime import datetime

from super_soccer_showdown.db.models import SoccerMatch
from super_soccer_showdown.domain.persistence.showdown_action import (
    DomainShowdownAction,
    showdown_action_from_db,
    showdown_action_to_db,
)


class DomainSoccerMatch:
    id: int | None
    starwars_team_id: int
    pokemon_team_id: int
    created_at: datetime
    winner_team_id: int | None
    starwars_user_id: int
    pokemon_user_id: int
    showdown_actions: list[DomainShowdownAction]

    def __init__(
        self,
        starwars_team_id: int,
        pokemon_team_id: int,
        created_at: datetime,
        winner_team_id: int | None,
        starwars_user_id: int,
        pokemon_user_id: int,
        showdown_actions: list[DomainShowdownAction] | None = None,
        id: int | None = None,
    ) -> None:
        self.id = id
        self.starwars_team_id = starwars_team_id
        self.pokemon_team_id = pokemon_team_id
        self.created_at = created_at
        self.winner_team_id = winner_team_id
        self.starwars_user_id = starwars_user_id
        self.pokemon_user_id = pokemon_user_id
        self.showdown_actions = showdown_actions or []


def soccer_match_from_db(model: SoccerMatch) -> DomainSoccerMatch:
    return DomainSoccerMatch(
        id=model.id,
        starwars_team_id=model.starwars_team_id,
        pokemon_team_id=model.pokemon_team_id,
        created_at=model.created_at,
        winner_team_id=model.winner_team_id,
        starwars_user_id=model.starwars_user_id,
        pokemon_user_id=model.pokemon_user_id,
        showdown_actions=[showdown_action_from_db(action) for action in model.showdown_actions],
    )


def soccer_match_to_db(entity: DomainSoccerMatch) -> SoccerMatch:
    model = SoccerMatch(
        starwars_team_id=entity.starwars_team_id,
        pokemon_team_id=entity.pokemon_team_id,
        created_at=entity.created_at,
        winner_team_id=entity.winner_team_id,
        starwars_user_id=entity.starwars_user_id,
        pokemon_user_id=entity.pokemon_user_id,
    )
    if entity.id is not None:
        model.id = entity.id
    if entity.id is not None and entity.showdown_actions:
        model.showdown_actions = [
            showdown_action_to_db(action, soccer_match_id=entity.id)
            for action in entity.showdown_actions
        ]
    return model
