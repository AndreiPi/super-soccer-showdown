from __future__ import annotations

from super_soccer_showdown.db.models.enums import PositionEnum
from super_soccer_showdown.db.models import StarWarsTeamComposition
from super_soccer_showdown.db.models.pokemon_team_composition import PokemonTeamComposition
from super_soccer_showdown.domain.entities import Position
from super_soccer_showdown.domain.persistence.player_data import (
    DomainPlayerData,
    pokemon_data_from_db,
    starwars_data_from_db,
)

class DomainTeamComposition:
    player: DomainPlayerData
    position: Position

    def __init__(self, player: DomainPlayerData, position: Position) -> None:
        self.player = player
        self.position = position


def starwars_team_composition_from_db(model: StarWarsTeamComposition) -> DomainTeamComposition:
    return DomainTeamComposition(
        player=starwars_data_from_db(model.player),
        position=Position(model.position.value),
    )


def pokemon_team_composition_from_db(model: PokemonTeamComposition) -> DomainTeamComposition:
    return DomainTeamComposition(
        player=pokemon_data_from_db(model.player),
        position=Position(model.position.value),
    )



