from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from super_soccer_showdown.domain.persistence.soccer_team import DomainSoccerTeam
from super_soccer_showdown.db.models.pokemon_data import PokemonData
from super_soccer_showdown.db.models.starwars_data import StarWarsData
from super_soccer_showdown.domain.entities import Universe
from super_soccer_showdown.domain.persistence.player_data import (
    DomainPlayerData,
    player_data_to_db,
    pokemon_data_from_db,
    starwars_data_from_db,
)


class PlayerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_random_static_players(self, universe: Universe, count: int) -> list[DomainPlayerData]:
        if universe == Universe.POKEMON:
            stmt = select(PokemonData).order_by(func.random()).limit(count)
            result = await self.session.execute(stmt)
            return [pokemon_data_from_db(row) for row in result.scalars().all()]

        if universe == Universe.STARWARS:
            stmt = select(StarWarsData).order_by(func.random()).limit(count)
            result = await self.session.execute(stmt)
            return [starwars_data_from_db(row) for row in result.scalars().all()]

        return []

    async def upsert_static_players(self, team: DomainSoccerTeam) -> None:
        pokemon_rows_by_id: dict[int, dict] = {}
        starwars_rows_by_id: dict[int, dict] = {}

        for composition in team.team_composition:
            player = composition.player
            if player.universe == Universe.POKEMON:
                pokemon_rows_by_id[player.source_id] = {
                    "pokeapi_id": player.source_id,
                    "name": player.name,
                    "height_cm": player.height_cm,
                    "weight_kg": player.weight_kg,
                    "power": player.power,
                }
                continue

            if player.universe == Universe.STARWARS:
                starwars_rows_by_id[player.source_id] = {
                    "swapi_id": player.source_id,
                    "name": player.name,
                    "height_cm": player.height_cm,
                    "weight_kg": player.weight_kg,
                    "power": player.power,
                }
                continue

        pokemon_rows = list(pokemon_rows_by_id.values())
        if pokemon_rows:
            pokemon_stmt = pg_insert(PokemonData).values(pokemon_rows)
            pokemon_stmt = pokemon_stmt.on_conflict_do_update(
                index_elements=[PokemonData.pokeapi_id],
                set_={"name": pokemon_stmt.excluded.name, 
                      "height_cm": pokemon_stmt.excluded.height_cm, 
                      "weight_kg": pokemon_stmt.excluded.weight_kg, 
                      "power": pokemon_stmt.excluded.power},
            )
            await self.session.execute(pokemon_stmt)

        starwars_rows = list(starwars_rows_by_id.values())
        if starwars_rows:
            starwars_stmt = pg_insert(StarWarsData).values(starwars_rows)
            starwars_stmt = starwars_stmt.on_conflict_do_update(
                index_elements=[StarWarsData.swapi_id],
                set_={"name": starwars_stmt.excluded.name, 
                      "height_cm": starwars_stmt.excluded.height_cm, 
                      "weight_kg": starwars_stmt.excluded.weight_kg, 
                      "power": starwars_stmt.excluded.power},
            )
            await self.session.execute(starwars_stmt)

    async def upsert_player_catalog(self, players: list[DomainPlayerData]) -> dict[str, int]:
        pokemon_rows_by_id: dict[int, dict] = {}
        starwars_rows_by_id: dict[int, dict] = {}

        for player in players:
            if player.universe == Universe.POKEMON:
                pokemon_rows_by_id[player.source_id] = {
                    "pokeapi_id": player.source_id,
                    "name": player.name,
                    "height_cm": player.height_cm,
                    "weight_kg": player.weight_kg,
                    "power": player.power,
                }
                continue

            if player.universe == Universe.STARWARS:
                starwars_rows_by_id[player.source_id] = {
                    "swapi_id": player.source_id,
                    "name": player.name,
                    "height_cm": player.height_cm,
                    "weight_kg": player.weight_kg,
                    "power": player.power,
                }

        pokemon_upserted = 0
        starwars_upserted = 0

        if pokemon_rows_by_id and len(pokemon_rows_by_id) > 0:
            pokemon_rows = list(pokemon_rows_by_id.values())
            pokemon_stmt = pg_insert(PokemonData).values(pokemon_rows)
            pokemon_stmt = pokemon_stmt.on_conflict_do_update(
                index_elements=[PokemonData.pokeapi_id],
                set_={
                    "name": pokemon_stmt.excluded.name,
                    "height_cm": pokemon_stmt.excluded.height_cm,
                "weight_kg": pokemon_stmt.excluded.weight_kg,
                "power": pokemon_stmt.excluded.power,
            },
            )
            await self.session.execute(pokemon_stmt)
            pokemon_upserted = len(pokemon_rows)

        if starwars_rows_by_id and len(starwars_rows_by_id) > 0:
            starwars_rows = list(starwars_rows_by_id.values())
            starwars_stmt = pg_insert(StarWarsData).values(starwars_rows)
            starwars_stmt = starwars_stmt.on_conflict_do_update(
                index_elements=[StarWarsData.swapi_id],
                set_={
                    "name": starwars_stmt.excluded.name,
                    "height_cm": starwars_stmt.excluded.height_cm,
                    "weight_kg": starwars_stmt.excluded.weight_kg,
                    "power": starwars_stmt.excluded.power,
                },
            )
            await self.session.execute(starwars_stmt)
            starwars_upserted = len(starwars_rows)

        await self.session.commit()

        return {
            "pokemon_fetched": len(pokemon_rows_by_id),
            "starwars_fetched": len(starwars_rows_by_id),
            "pokemon_upserted": pokemon_upserted,
            "starwars_upserted": starwars_upserted,
            "total_fetched": len(pokemon_rows_by_id) + len(starwars_rows_by_id),
            "total_upserted": pokemon_upserted + starwars_upserted,
        }
