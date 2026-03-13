import pytest
from unittest.mock import AsyncMock, MagicMock

import httpx

from super_soccer_showdown.adapters.pokeapi_provider import PokeApiPlayerProvider
from super_soccer_showdown.domain.entities import Universe
from super_soccer_showdown.service.exceptions import TeamGenerationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_provider(session=None) -> PokeApiPlayerProvider:
    if session is None:
        session = AsyncMock(spec=httpx.AsyncClient)
    return PokeApiPlayerProvider(session=session)


def make_mock_response(status_code: int = 200, json_data: dict | None = None) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data or {}
    return mock


def make_pokemon_api_data(
    pokemon_id: int = 1,
    name: str = "bulbasaur",
    height: int = 7,
    weight: int = 69,
    abilities: list | None = None,
) -> dict:
    if abilities is None:
        abilities = [{"ability": {"name": "overgrow"}}, {"ability": {"name": "chlorophyll"}}]
    return {"id": pokemon_id, "name": name, "height": height, "weight": weight, "abilities": abilities}


VALID_POKEMON_DATA = make_pokemon_api_data()


# ---------------------------------------------------------------------------
# to_player
# ---------------------------------------------------------------------------

class TestToPlayer:
    def test_valid_data_returns_player_with_correct_fields(self):
        provider = make_provider()
        player = provider.to_player(VALID_POKEMON_DATA)

        assert player is not None
        assert player.name == "bulbasaur"
        assert player.source_id == 1
        assert player.height_cm == pytest.approx(70.0)   # height_dm=7 → *10
        assert player.weight_kg == pytest.approx(6.9)    # weight_hg=69 → /10
        assert player.universe == Universe.POKEMON
        assert player.power is not None
        # power = round(70 * 6.9 * max(2,1) / 100, 2) = 9.66
        assert player.power == pytest.approx(9.66)

    def test_empty_name_returns_none(self):
        provider = make_provider()
        data = {**VALID_POKEMON_DATA, "name": ""}
        assert provider.to_player(data) is None

    def test_whitespace_only_name_returns_none(self):
        provider = make_provider()
        data = {**VALID_POKEMON_DATA, "name": "   "}
        assert provider.to_player(data) is None

    def test_none_id_returns_none(self):
        provider = make_provider()
        data = {**VALID_POKEMON_DATA, "id": None}
        assert provider.to_player(data) is None

    def test_zero_height_returns_none(self):
        provider = make_provider()
        data = {**VALID_POKEMON_DATA, "height": 0}
        assert provider.to_player(data) is None

    def test_zero_weight_returns_none(self):
        provider = make_provider()
        data = {**VALID_POKEMON_DATA, "weight": 0}
        assert provider.to_player(data) is None

    def test_negative_height_returns_none(self):
        provider = make_provider()
        data = {**VALID_POKEMON_DATA, "height": -1}
        assert provider.to_player(data) is None

    def test_non_numeric_height_returns_none(self):
        provider = make_provider()
        data = {**VALID_POKEMON_DATA, "height": "unknown"}
        assert provider.to_player(data) is None

    def test_no_abilities_still_returns_player(self):
        """With zero abilities max(0, 1)=1 so power is still valid."""
        provider = make_provider()
        data = {**VALID_POKEMON_DATA, "abilities": []}
        player = provider.to_player(data)
        assert player is not None
        assert player.power == pytest.approx(round(70.0 * 6.9 * 1 / 100.0, 2))


# ---------------------------------------------------------------------------
# fetch_pokemon_by_url
# ---------------------------------------------------------------------------

class TestFetchPokemonByUrl:
    async def test_returns_json_on_200(self):
        session = AsyncMock()
        session.get = AsyncMock(return_value=make_mock_response(200, VALID_POKEMON_DATA))
        provider = make_provider(session)

        result = await provider.fetch_pokemon_by_url("https://pokeapi.co/api/v2/pokemon/1/")

        assert result == VALID_POKEMON_DATA

    async def test_returns_none_on_404(self):
        session = AsyncMock()
        session.get = AsyncMock(return_value=make_mock_response(404))
        provider = make_provider(session)

        result = await provider.fetch_pokemon_by_url("https://pokeapi.co/api/v2/pokemon/9999/")

        assert result is None

    async def test_returns_none_on_server_error(self):
        session = AsyncMock()
        session.get = AsyncMock(return_value=make_mock_response(500))
        provider = make_provider(session)

        result = await provider.fetch_pokemon_by_url("https://pokeapi.co/api/v2/pokemon/1/")

        assert result is None

    async def test_returns_none_on_http_error(self):
        session = AsyncMock()
        session.get = AsyncMock(side_effect=httpx.HTTPError("Connection refused"))
        provider = make_provider(session)

        result = await provider.fetch_pokemon_by_url("https://pokeapi.co/api/v2/pokemon/1/")

        assert result is None


# ---------------------------------------------------------------------------
# fetch_all_pokemon_entries
# ---------------------------------------------------------------------------

class TestFetchAllPokemonEntries:
    async def test_paginates_until_next_is_none(self):
        page1 = {
            "results": [{"name": "bulbasaur", "url": "https://pokeapi.co/api/v2/pokemon/1/"}],
            "next": "https://pokeapi.co/api/v2/pokemon?limit=100&offset=100",
        }
        page2 = {
            "results": [{"name": "ivysaur", "url": "https://pokeapi.co/api/v2/pokemon/2/"}],
            "next": None,
        }
        session = AsyncMock()
        session.get = AsyncMock(side_effect=[
            make_mock_response(200, page1),
            make_mock_response(200, page2),
        ])
        provider = make_provider(session)

        entries = await provider.fetch_all_pokemon_entries()

        assert len(entries) == 2
        assert entries[0]["name"] == "bulbasaur"
        assert entries[1]["name"] == "ivysaur"

    async def test_returns_empty_list_on_http_error(self):
        session = AsyncMock()
        session.get = AsyncMock(side_effect=httpx.HTTPError("Network error"))
        provider = make_provider(session)

        entries = await provider.fetch_all_pokemon_entries()

        assert entries == []

    async def test_returns_empty_list_on_non_200_status(self):
        session = AsyncMock()
        session.get = AsyncMock(return_value=make_mock_response(503))
        provider = make_provider(session)

        entries = await provider.fetch_all_pokemon_entries()

        assert entries == []


# ---------------------------------------------------------------------------
# get_random_players
# ---------------------------------------------------------------------------

class TestGetRandomPlayers:
    async def test_returns_exact_requested_count(self):
        provider = make_provider()
        provider._pokemon_entries_cache = [
            {"name": f"pokemon{i}", "url": f"https://pokeapi.co/api/v2/pokemon/{i}/"}
            for i in range(1, 10)
        ]

        async def mock_get(url, timeout=None):
            i = int(url.rstrip("/").split("/")[-1])
            return make_mock_response(200, make_pokemon_api_data(pokemon_id=i, name=f"pokemon{i}"))

        provider._session = AsyncMock()
        provider._session.get = mock_get

        players = await provider.get_random_players(3)

        assert len(players) == 3
        assert all(p.universe == Universe.POKEMON for p in players)

    async def test_raises_team_generation_error_when_no_entries(self):
        provider = make_provider()
        provider._pokemon_entries_cache = []

        with pytest.raises(TeamGenerationError):
            await provider.get_random_players(3)

    async def test_raises_team_generation_error_when_too_many_invalid_players(self):
        """Entries exist but all detail fetches return 404."""
        provider = make_provider()
        provider._pokemon_entries_cache = [
            {"name": f"pokemon{i}", "url": f"https://pokeapi.co/api/v2/pokemon/{i}/"}
            for i in range(1, 4)
        ]
        session = AsyncMock()
        session.get = AsyncMock(return_value=make_mock_response(404))
        provider._session = session

        with pytest.raises(TeamGenerationError):
            await provider.get_random_players(3)


# ---------------------------------------------------------------------------
# get_all_players
# ---------------------------------------------------------------------------

class TestGetAllPlayers:
    async def test_returns_all_valid_players(self):
        provider = make_provider()
        provider._pokemon_entries_cache = [
            {"name": f"pokemon{i}", "url": f"https://pokeapi.co/api/v2/pokemon/{i}/"}
            for i in range(1, 4)
        ]

        async def mock_get(url, timeout=None):
            i = int(url.rstrip("/").split("/")[-1])
            return make_mock_response(200, make_pokemon_api_data(pokemon_id=i, name=f"pokemon{i}"))

        provider._session = AsyncMock()
        provider._session.get = mock_get

        players = await provider.get_all_players()

        assert len(players) == 3
        assert all(p.universe == Universe.POKEMON for p in players)

    async def test_deduplicates_players_by_source_id(self):
        """Two entries pointing to the same Pokémon ID yield only one player."""
        provider = make_provider()
        provider._pokemon_entries_cache = [
            {"name": "bulbasaur", "url": "https://pokeapi.co/api/v2/pokemon/1/"},
            {"name": "bulbasaur-duplicate", "url": "https://pokeapi.co/api/v2/pokemon/1/"},
        ]

        async def mock_get(url, timeout=None):
            return make_mock_response(200, make_pokemon_api_data(pokemon_id=1, name="bulbasaur"))

        provider._session = AsyncMock()
        provider._session.get = mock_get

        players = await provider.get_all_players()

        assert len(players) == 1
        assert players[0].source_id == 1

    async def test_skips_entries_with_invalid_detail_data(self):
        """Entries that return 404 or invalid JSON are silently skipped."""
        provider = make_provider()
        provider._pokemon_entries_cache = [
            {"name": "bulbasaur", "url": "https://pokeapi.co/api/v2/pokemon/1/"},
            {"name": "ghost", "url": "https://pokeapi.co/api/v2/pokemon/9999/"},
        ]

        async def mock_get(url, timeout=None):
            if "9999" in url:
                return make_mock_response(404)
            return make_mock_response(200, make_pokemon_api_data(pokemon_id=1, name="bulbasaur"))

        provider._session = AsyncMock()
        provider._session.get = mock_get

        players = await provider.get_all_players()

        assert len(players) == 1
        assert players[0].name == "bulbasaur"
