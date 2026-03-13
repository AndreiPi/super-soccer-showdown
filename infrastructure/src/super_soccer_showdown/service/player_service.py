import asyncio

from super_soccer_showdown.adapters.interface.player_provider import PlayerProvider
from super_soccer_showdown.domain.entities import Universe
from super_soccer_showdown.domain.repositories.player_repository import PlayerRepository


class SyncPlayersCatalogUseCase:
    def __init__(self, providers: dict[Universe, PlayerProvider], player_repository: PlayerRepository) -> None:
        self._providers = providers
        self._player_repository = player_repository

    async def execute(self) -> dict[str, int]:
        pokemon_provider = self._providers.get(Universe.POKEMON)
        starwars_provider = self._providers.get(Universe.STARWARS)

        if pokemon_provider is None or starwars_provider is None:
            raise ValueError("Missing provider configuration for one or more universes.")

        pokemon_players, starwars_players = await asyncio.gather(
            pokemon_provider.get_all_players(),
            starwars_provider.get_all_players(),
        )

        return await self._player_repository.upsert_player_catalog(pokemon_players + starwars_players)
