import pytest
from unittest.mock import AsyncMock

from super_soccer_showdown.domain.entities import Universe
from super_soccer_showdown.domain.persistence.player_data import DomainPlayerData
from super_soccer_showdown.service.player_service import SyncPlayersCatalogUseCase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_player(source_id: int, name: str, universe: Universe) -> DomainPlayerData:
    return DomainPlayerData(
        source_id=source_id,
        name=name,
        height_cm=170.0,
        weight_kg=70.0,
        universe=universe,
        power=10.0,
    )


def _default_upsert_result(**overrides) -> dict:
    base = {
        "pokemon_fetched": 0,
        "starwars_fetched": 0,
        "pokemon_upserted": 0,
        "starwars_upserted": 0,
        "total_fetched": 0,
        "total_upserted": 0,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# SyncPlayersCatalogUseCase
# ---------------------------------------------------------------------------

class TestSyncPlayersCatalogUseCase:
    def _make(
        self,
        pokemon_players: list | None = None,
        starwars_players: list | None = None,
        upsert_result: dict | None = None,
    ):
        pokemon_provider  = AsyncMock()
        starwars_provider = AsyncMock()
        player_repo       = AsyncMock()

        pokemon_provider.get_all_players  = AsyncMock(return_value=pokemon_players  or [])
        starwars_provider.get_all_players = AsyncMock(return_value=starwars_players or [])
        player_repo.upsert_player_catalog = AsyncMock(
            return_value=upsert_result or _default_upsert_result()
        )

        use_case = SyncPlayersCatalogUseCase(
            providers={
                Universe.POKEMON:  pokemon_provider,
                Universe.STARWARS: starwars_provider,
            },
            player_repository=player_repo,
        )
        return use_case, pokemon_provider, starwars_provider, player_repo

    async def test_both_providers_are_called(self):
        use_case, poke_prov, sw_prov, _ = self._make()
        await use_case.execute()
        poke_prov.get_all_players.assert_awaited_once()
        sw_prov.get_all_players.assert_awaited_once()

    async def test_upsert_called_with_combined_player_list(self):
        pokemon_players  = [make_player(1, "Bulbasaur",      Universe.POKEMON)]
        starwars_players = [make_player(1, "Luke Skywalker", Universe.STARWARS)]
        use_case, _, _, player_repo = self._make(
            pokemon_players=pokemon_players,
            starwars_players=starwars_players,
        )
        await use_case.execute()
        call_args = player_repo.upsert_player_catalog.call_args[0][0]
        assert len(call_args) == 2

    async def test_returns_upsert_result_directly(self):
        expected = _default_upsert_result(
            pokemon_fetched=3, starwars_fetched=2,
            pokemon_upserted=3, starwars_upserted=2,
            total_fetched=5, total_upserted=5,
        )
        use_case, _, _, _ = self._make(upsert_result=expected)
        result = await use_case.execute()
        assert result == expected

    async def test_missing_pokemon_provider_raises_value_error(self):
        sw_provider = AsyncMock()
        player_repo = AsyncMock()
        use_case = SyncPlayersCatalogUseCase(
            providers={Universe.STARWARS: sw_provider},
            player_repository=player_repo,
        )
        with pytest.raises(ValueError, match="[Mm]issing"):
            await use_case.execute()

    async def test_missing_starwars_provider_raises_value_error(self):
        poke_provider = AsyncMock()
        player_repo   = AsyncMock()
        use_case = SyncPlayersCatalogUseCase(
            providers={Universe.POKEMON: poke_provider},
            player_repository=player_repo,
        )
        with pytest.raises(ValueError, match="[Mm]issing"):
            await use_case.execute()

    async def test_empty_providers_dict_raises_value_error(self):
        player_repo = AsyncMock()
        use_case = SyncPlayersCatalogUseCase(
            providers={},
            player_repository=player_repo,
        )
        with pytest.raises(ValueError):
            await use_case.execute()

    async def test_upsert_is_not_called_when_provider_is_missing(self):
        """Repository must not be touched if provider validation fails."""
        player_repo = AsyncMock()
        use_case = SyncPlayersCatalogUseCase(
            providers={},
            player_repository=player_repo,
        )
        with pytest.raises(ValueError):
            await use_case.execute()
        player_repo.upsert_player_catalog.assert_not_awaited()
