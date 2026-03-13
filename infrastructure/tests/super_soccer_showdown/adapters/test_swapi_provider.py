import pytest
from unittest.mock import AsyncMock, MagicMock

import httpx

from super_soccer_showdown.adapters.swapi_provider import SwapiPlayerProvider
from super_soccer_showdown.domain.entities import Universe
from super_soccer_showdown.service.exceptions import TeamGenerationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_provider(session=None) -> SwapiPlayerProvider:
    if session is None:
        session = AsyncMock(spec=httpx.AsyncClient)
    return SwapiPlayerProvider(session=session)


def make_mock_response(status_code: int = 200, json_data: dict | None = None) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data or {}
    return mock


def make_person_data(
    person_id: int = 1,
    name: str = "Luke Skywalker",
    mass: str = "77",
    height: str = "172",
    vehicles: list | None = None,
    starships: list | None = None,
) -> dict:
    return {
        "name": name,
        "mass": mass,
        "height": height,
        "vehicles": vehicles if vehicles is not None else ["url/v/14/", "url/v/30/"],
        "starships": starships if starships is not None else ["url/s/12/"],
        "url": f"https://swapi.dev/api/people/{person_id}/",
    }


VALID_PERSON_DATA = make_person_data()


# ---------------------------------------------------------------------------
# extract_id_from_url
# ---------------------------------------------------------------------------

class TestExtractIdFromUrl:
    def test_valid_url_with_trailing_slash_returns_id(self):
        provider = make_provider()
        assert provider.extract_id_from_url("https://swapi.dev/api/people/1/") == 1

    def test_valid_url_without_trailing_slash_returns_id(self):
        provider = make_provider()
        assert provider.extract_id_from_url("https://swapi.dev/api/people/42") == 42

    def test_empty_string_returns_none(self):
        provider = make_provider()
        assert provider.extract_id_from_url("") is None

    def test_non_numeric_last_segment_returns_none(self):
        provider = make_provider()
        assert provider.extract_id_from_url("https://swapi.dev/api/people/abc/") is None

    def test_zero_id_returns_none(self):
        provider = make_provider()
        assert provider.extract_id_from_url("https://swapi.dev/api/people/0/") is None

    def test_negative_id_returns_none(self):
        provider = make_provider()
        assert provider.extract_id_from_url("https://swapi.dev/api/people/-1/") is None


# ---------------------------------------------------------------------------
# to_player
# ---------------------------------------------------------------------------

class TestToPlayer:
    def test_valid_data_returns_player_with_correct_fields(self):
        provider = make_provider()
        player = provider.to_player(VALID_PERSON_DATA, player_id=1)

        assert player is not None
        assert player.name == "Luke Skywalker"
        assert player.source_id == 1
        assert player.weight_kg == pytest.approx(77.0)
        assert player.height_cm == pytest.approx(172.0)
        assert player.universe == Universe.STARWARS
        # power = round(172 * 77 * max(3, 1) / 100, 2) = 397.32
        assert player.power == pytest.approx(397.32)

    def test_unknown_mass_returns_none(self):
        provider = make_provider()
        data = {**VALID_PERSON_DATA, "mass": "unknown"}
        assert provider.to_player(data, player_id=1) is None

    def test_unknown_height_returns_none(self):
        provider = make_provider()
        data = {**VALID_PERSON_DATA, "height": "unknown"}
        assert provider.to_player(data, player_id=1) is None

    def test_zero_weight_returns_none(self):
        provider = make_provider()
        data = {**VALID_PERSON_DATA, "mass": "0"}
        assert provider.to_player(data, player_id=1) is None

    def test_zero_height_returns_none(self):
        provider = make_provider()
        data = {**VALID_PERSON_DATA, "height": "0"}
        assert provider.to_player(data, player_id=1) is None

    def test_mass_with_comma_separator_is_parsed(self):
        """Some characters have mass like '1,358' which must be normalised."""
        provider = make_provider()
        data = {**VALID_PERSON_DATA, "mass": "1,358", "vehicles": [], "starships": []}
        player = provider.to_player(data, player_id=1)
        assert player is not None
        assert player.weight_kg == pytest.approx(1358.0)

    def test_no_vehicles_or_starships_uses_multiplier_of_one(self):
        """With zero vehicles/starships max(0, 1)=1 so power is still positive."""
        provider = make_provider()
        data = {**VALID_PERSON_DATA, "vehicles": [], "starships": []}
        player = provider.to_player(data, player_id=1)
        assert player is not None
        expected_power = round(172.0 * 77.0 * 1 / 100.0, 2)
        assert player.power == pytest.approx(expected_power)


# ---------------------------------------------------------------------------
# fetch_people_page
# ---------------------------------------------------------------------------

class TestFetchPeoplePage:
    async def test_returns_json_data_on_200(self):
        page_data = {"count": 82, "results": [VALID_PERSON_DATA], "next": None}
        session = AsyncMock()
        session.get = AsyncMock(return_value=make_mock_response(200, page_data))
        provider = make_provider(session)

        result = await provider.fetch_people_page(1)

        assert result == page_data

    async def test_returns_none_on_non_200_status(self):
        session = AsyncMock()
        session.get = AsyncMock(return_value=make_mock_response(500))
        provider = make_provider(session)

        result = await provider.fetch_people_page(1)

        assert result is None

    async def test_returns_none_on_http_error(self):
        session = AsyncMock()
        session.get = AsyncMock(side_effect=httpx.HTTPError("Timeout"))
        provider = make_provider(session)

        result = await provider.fetch_people_page(1)

        assert result is None


# ---------------------------------------------------------------------------
# fetch_all_people
# ---------------------------------------------------------------------------

class TestFetchAllPeople:
    async def test_single_page_returns_all_people(self):
        page = {"count": 1, "results": [VALID_PERSON_DATA], "next": None}
        session = AsyncMock()
        session.get = AsyncMock(return_value=make_mock_response(200, page))
        provider = make_provider(session)

        people = await provider.fetch_all_people()

        assert len(people) == 1
        assert people[0]["name"] == "Luke Skywalker"

    async def test_multi_page_fetches_all_people(self):
        """With count=11 and PAGE_SIZE=10, two pages are fetched."""
        person2 = make_person_data(person_id=4, name="Darth Vader")
        page1 = {"count": 11, "results": [VALID_PERSON_DATA], "next": "https://swapi.dev/api/people/?page=2"}
        page2 = {"count": 11, "results": [person2], "next": None}
        session = AsyncMock()
        session.get = AsyncMock(side_effect=[
            make_mock_response(200, page1),
            make_mock_response(200, page2),
        ])
        provider = make_provider(session)

        people = await provider.fetch_all_people()

        assert len(people) == 2
        assert people[0]["name"] == "Luke Skywalker"
        assert people[1]["name"] == "Darth Vader"

    async def test_returns_cached_result_on_second_call(self):
        page = {"count": 1, "results": [VALID_PERSON_DATA], "next": None}
        session = AsyncMock()
        session.get = AsyncMock(return_value=make_mock_response(200, page))
        provider = make_provider(session)

        first = await provider.fetch_all_people()
        second = await provider.fetch_all_people()

        assert first is second
        assert session.get.call_count == 1

    async def test_returns_empty_list_when_first_page_fails(self):
        session = AsyncMock()
        session.get = AsyncMock(return_value=make_mock_response(503))
        provider = make_provider(session)

        people = await provider.fetch_all_people()

        assert people == []


# ---------------------------------------------------------------------------
# get_random_players
# ---------------------------------------------------------------------------

class TestGetRandomPlayers:
    async def test_returns_exact_requested_count(self):
        people = [
            make_person_data(person_id=i, name=f"Person {i}")
            for i in range(1, 6)
        ]
        provider = make_provider()
        provider._people_cache = people

        players = await provider.get_random_players(3)

        assert len(players) == 3
        assert all(p.universe == Universe.STARWARS for p in players)

    async def test_raises_when_all_entries_have_invalid_mass(self):
        bad_people = [
            make_person_data(person_id=i, name=f"Person{i}", mass="unknown")
            for i in range(1, 4)
        ]
        provider = make_provider()
        provider._people_cache = bad_people

        with pytest.raises(TeamGenerationError):
            await provider.get_random_players(3)

    async def test_raises_when_cache_is_empty(self):
        provider = make_provider()
        provider._people_cache = []

        with pytest.raises(TeamGenerationError):
            await provider.get_random_players(1)

    async def test_players_have_unique_names(self):
        people = [
            make_person_data(person_id=i, name=f"Person {i}")
            for i in range(1, 8)
        ]
        provider = make_provider()
        provider._people_cache = people

        players = await provider.get_random_players(5)

        names = [p.name for p in players]
        assert len(names) == len(set(names))


# ---------------------------------------------------------------------------
# get_all_players
# ---------------------------------------------------------------------------

class TestGetAllPlayers:
    async def test_returns_all_valid_players(self):
        people = [make_person_data(person_id=i, name=f"Person{i}") for i in range(1, 4)]
        provider = make_provider()
        provider._people_cache = people

        players = await provider.get_all_players()

        assert len(players) == 3
        assert all(p.universe == Universe.STARWARS for p in players)

    async def test_skips_entries_without_valid_url_id(self):
        people = [
            {**VALID_PERSON_DATA, "name": "Luke", "url": "https://swapi.dev/api/people/1/"},
            {**VALID_PERSON_DATA, "name": "Nobody", "url": "https://swapi.dev/api/people/abc/"},
        ]
        provider = make_provider()
        provider._people_cache = people

        players = await provider.get_all_players()

        assert len(players) == 1
        assert players[0].name == "Luke"

    async def test_skips_entries_with_invalid_data(self):
        people = [
            make_person_data(person_id=1, name="Luke"),
            make_person_data(person_id=2, name="Mystery", mass="unknown"),
        ]
        provider = make_provider()
        provider._people_cache = people

        players = await provider.get_all_players()

        assert len(players) == 1
        assert players[0].name == "Luke"

    async def test_deduplicates_players_by_source_id(self):
        """Two entries with the same URL ID yield only one player."""
        people = [
            make_person_data(person_id=1, name="Luke"),
            make_person_data(person_id=1, name="Luke Copy"),
        ]
        provider = make_provider()
        provider._people_cache = people

        players = await provider.get_all_players()

        assert len(players) == 1
        assert players[0].source_id == 1
