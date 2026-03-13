from __future__ import annotations

from super_soccer_showdown.db.models import PokemonData
from super_soccer_showdown.db.models.starwars_data import StarWarsData
from super_soccer_showdown.domain.entities import Universe


class DomainPlayerData:
    id: int | None
    # source_id maps to pokeapi_id for POKEMON or swapi_id for STARWARS
    source_id: int
    name: str
    height_cm: float
    weight_kg: float
    power: float | None
    universe: Universe

    def __init__(
        self,
        source_id: int,
        name: str,
        height_cm: float,
        weight_kg: float,
        universe: Universe,
        id: int | None = None,
        power: float | None = None,
    ) -> None:
        self.id = id
        self.source_id = source_id
        self.name = name
        self.height_cm = height_cm
        self.weight_kg = weight_kg
        self.power = power
        self.universe = universe


def pokemon_data_from_db(model: PokemonData) -> DomainPlayerData:
    return DomainPlayerData(
        id=model.pokeapi_id,
        source_id=model.pokeapi_id,
        name=model.name,
        height_cm=model.height_cm,
        weight_kg=model.weight_kg,
        power=model.power,
        universe=Universe.POKEMON,
    )


def starwars_data_from_db(model: StarWarsData) -> DomainPlayerData:
    return DomainPlayerData(
        id=model.swapi_id,
        source_id=model.swapi_id,
        name=model.name,
        height_cm=model.height_cm,
        weight_kg=model.weight_kg,
        power=model.power,
        universe=Universe.STARWARS,
    )


def player_data_to_db(entity: DomainPlayerData) -> PokemonData | StarWarsData:
    return (
        PokemonData(
            pokeapi_id=entity.source_id,
            name=entity.name,
            height_cm=entity.height_cm,
            weight_kg=entity.weight_kg,
            power=entity.power,
        )
        if entity.universe == Universe.POKEMON
        else StarWarsData(
            swapi_id=entity.source_id,
            name=entity.name,
            height_cm=entity.height_cm,
            weight_kg=entity.weight_kg,
            power=entity.power,
        )
    )
