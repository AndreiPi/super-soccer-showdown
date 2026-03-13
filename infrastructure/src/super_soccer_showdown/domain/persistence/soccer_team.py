from __future__ import annotations

from super_soccer_showdown.db.models import PositionEnum, SoccerTeam, UniverseEnum
from super_soccer_showdown.db.models.pokemon_team_composition import PokemonTeamComposition
from super_soccer_showdown.db.models.starwars_team_composition import StarWarsTeamComposition
from super_soccer_showdown.domain.entities import Universe
from super_soccer_showdown.domain.persistence.team_composition import (
    DomainTeamComposition,
    starwars_team_composition_from_db,
    pokemon_team_composition_from_db,
)

class DomainSoccerTeam:
    id: int | None
    universe: Universe
    owner_user_id: int
    team_composition: list[DomainTeamComposition]

    def __init__(
        self,
        universe: Universe,
        owner_user_id: int,
        team_composition: list[DomainTeamComposition] | None = None,
        id: int | None = None,
    ) -> None:
        self.id = id
        self.universe = universe
        self.owner_user_id = owner_user_id
        self.team_composition = list(team_composition or [])


def soccer_team_from_db(model: SoccerTeam) -> DomainSoccerTeam:
    if model.universe == UniverseEnum.STARWARS:
        composition = [starwars_team_composition_from_db(c) for c in model.starwars_players]
    else:
        composition = [pokemon_team_composition_from_db(c) for c in model.pokemon_players]
    return DomainSoccerTeam(
        id=model.id,
        universe=Universe(model.universe.value),
        owner_user_id=model.owner_user_id,
        team_composition=composition,
    )


def soccer_team_to_db(entity: DomainSoccerTeam) -> SoccerTeam:
    model = SoccerTeam(
        universe=UniverseEnum(entity.universe.value),
        owner_user_id=entity.owner_user_id,
    )
    if entity.id is not None:
        model.id = entity.id
    if model.universe == UniverseEnum.STARWARS:
        model.starwars_players = [starwars_composition_to_db(comp) for comp in entity.team_composition]
    else:
        model.pokemon_players = [pokemon_composition_to_db(comp) for comp in entity.team_composition]
    return model


def starwars_composition_to_db(entity: DomainTeamComposition) -> StarWarsTeamComposition:
    model = StarWarsTeamComposition(
        player_id=entity.player.source_id,
        position=PositionEnum(entity.position.value),
    )
    return model


def pokemon_composition_to_db(entity: DomainTeamComposition) -> PokemonTeamComposition:
    model = PokemonTeamComposition(
        player_id=entity.player.source_id,
        position=PositionEnum(entity.position.value),
    )
    return model
