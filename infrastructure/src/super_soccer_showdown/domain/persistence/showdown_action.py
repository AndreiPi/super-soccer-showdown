from __future__ import annotations

from super_soccer_showdown.db.models.showdown_action import ShowdownAction
from super_soccer_showdown.db.models.enums import UniverseEnum
from super_soccer_showdown.domain.entities import Universe


class DomainShowdownAction:
    id: int | None
    soccer_match_id: int | None
    action_number: int
    team_id: int
    team_universe: Universe
    scorer: str
    scorer_source_id: int
    against: str
    is_goal: bool

    def __init__(
        self,
        action_number: int,
        team_id: int,
        team_universe: Universe,
        scorer: str,
        scorer_source_id: int,
        against: str,
        is_goal: bool,
        soccer_match_id: int | None = None,
        id: int | None = None,
    ) -> None:
        self.id = id
        self.soccer_match_id = soccer_match_id
        self.action_number = action_number
        self.team_id = team_id
        self.team_universe = team_universe
        self.scorer = scorer
        self.scorer_source_id = scorer_source_id
        self.against = against
        self.is_goal = is_goal


def showdown_action_from_db(model: ShowdownAction) -> DomainShowdownAction:
    return DomainShowdownAction(
        id=model.id,
        soccer_match_id=model.soccer_match_id,
        action_number=model.action_number,
        team_id=model.team_id,
        team_universe=Universe(model.team_universe.value),
        scorer=model.scorer,
        scorer_source_id=model.scorer_source_id,
        against=model.against,
        is_goal=model.is_goal,
    )


def showdown_action_to_db(
    entity: DomainShowdownAction,
    soccer_match_id: int | None = None,
) -> ShowdownAction:
    resolved_soccer_match_id = soccer_match_id if soccer_match_id is not None else entity.soccer_match_id
    if resolved_soccer_match_id is None:
        raise ValueError("soccer_match_id is required to persist a showdown action.")

    model = ShowdownAction(
        soccer_match_id=resolved_soccer_match_id,
        action_number=entity.action_number,
        team_id=entity.team_id,
        team_universe=UniverseEnum(entity.team_universe.value),
        scorer=entity.scorer,
        scorer_source_id=entity.scorer_source_id,
        against=entity.against,
        is_goal=entity.is_goal,
    )
    if entity.id is not None:
        model.id = entity.id
    return model
