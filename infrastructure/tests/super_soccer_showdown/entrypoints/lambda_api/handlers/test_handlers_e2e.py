import json
import os
from datetime import datetime, timezone
from typing import Iterator
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from super_soccer_showdown.entrypoints.lambda_api import bootstrap
from super_soccer_showdown.entrypoints.lambda_api.handlers import matches_handlers, team_handlers, user_handlers


def parse_body(response: dict) -> dict:
    return json.loads(response["body"])


def _configure_test_db_env() -> None:
    os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-with-at-least-32-bytes")


async def _prepare_in_memory_database() -> None:
    db_base_module = __import__("super_soccer_showdown.db.base", fromlist=["Base"])
    __import__("super_soccer_showdown.db.models")
    base = db_base_module.Base

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(base.metadata.create_all)

    bootstrap._ENGINE = engine
    bootstrap._SESSION_FACTORY = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )


@pytest.fixture(autouse=True)
def clean_database_between_tests() -> Iterator[None]:
    _configure_test_db_env()
    loop = bootstrap.get_event_loop()

    if bootstrap._ENGINE is not None:
        loop.run_until_complete(bootstrap._ENGINE.dispose())

    bootstrap._TRACKED_SESSIONS = []
    bootstrap._ENGINE = None
    bootstrap._SESSION_FACTORY = None

    loop.run_until_complete(_prepare_in_memory_database())
    yield

    loop.run_until_complete(bootstrap.close_tracked_sessions())
    if bootstrap._ENGINE is not None:
        loop.run_until_complete(bootstrap._ENGINE.dispose())
    bootstrap._TRACKED_SESSIONS = []
    bootstrap._ENGINE = None
    bootstrap._SESSION_FACTORY = None


def _register_user(username: str) -> dict:
    event = {"body": json.dumps({"username": username})}
    response = user_handlers.register_user_handler(event, None)
    assert response["statusCode"] == 201
    return parse_body(response)


def _auth_header_from_register_payload(register_payload: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {register_payload['jwt_token']}"}


async def _seed_team_and_match_data(starwars_user_id: int, pokemon_user_id: int) -> dict[str, int]:
    models = __import__("super_soccer_showdown.db.models", fromlist=["*"])
    enums = __import__("super_soccer_showdown.db.models.enums", fromlist=["UniverseEnum", "PositionEnum"])

    session = bootstrap.get_db_session()
    try:
        session.add_all(
            [
                models.StarWarsData(swapi_id=101, name="Luke", height_cm=172.0, weight_kg=77.0, power=95.0),
                models.StarWarsData(swapi_id=102, name="Han", height_cm=180.0, weight_kg=80.0, power=88.0),
                models.StarWarsData(swapi_id=103, name="Leia", height_cm=150.0, weight_kg=49.0, power=90.0),
                models.PokemonData(pokeapi_id=201, name="Pikachu", height_cm=40.0, weight_kg=6.0, power=93.0),
                models.PokemonData(pokeapi_id=202, name="Charizard", height_cm=170.0, weight_kg=90.5, power=98.0),
                models.PokemonData(pokeapi_id=203, name="Bulbasaur", height_cm=70.0, weight_kg=6.9, power=84.0),
            ]
        )

        starwars_team = models.SoccerTeam(
            universe=enums.UniverseEnum.STARWARS,
            owner_user_id=starwars_user_id,
        )
        pokemon_team = models.SoccerTeam(
            universe=enums.UniverseEnum.POKEMON,
            owner_user_id=pokemon_user_id,
        )
        session.add_all([starwars_team, pokemon_team])
        await session.flush()

        session.add_all(
            [
                models.StarWarsTeamComposition(team_id=starwars_team.id, player_id=101, position=enums.PositionEnum.GOALIE),
                models.StarWarsTeamComposition(team_id=starwars_team.id, player_id=102, position=enums.PositionEnum.DEFENCE),
                models.StarWarsTeamComposition(team_id=starwars_team.id, player_id=103, position=enums.PositionEnum.OFFENCE),
                models.PokemonTeamComposition(team_id=pokemon_team.id, player_id=202, position=enums.PositionEnum.GOALIE),
                models.PokemonTeamComposition(team_id=pokemon_team.id, player_id=201, position=enums.PositionEnum.DEFENCE),
                models.PokemonTeamComposition(team_id=pokemon_team.id, player_id=203, position=enums.PositionEnum.OFFENCE),
            ]
        )

        soccer_match = models.SoccerMatch(
            starwars_team_id=starwars_team.id,
            pokemon_team_id=pokemon_team.id,
            created_at=datetime.now(timezone.utc),
            winner_team_id=starwars_team.id,
            starwars_user_id=starwars_user_id,
            pokemon_user_id=pokemon_user_id,
        )
        session.add(soccer_match)
        await session.flush()

        session.add(
            models.ShowdownAction(
                soccer_match_id=soccer_match.id,
                action_number=1,
                team_id=starwars_team.id,
                team_universe=enums.UniverseEnum.STARWARS,
                scorer="Luke",
                scorer_source_id=101,
                against="Pikachu",
                is_goal=True,
            )
        )
        await session.commit()

        return {
            "starwars_team_id": int(starwars_team.id),
            "pokemon_team_id": int(pokemon_team.id),
            "match_id": int(soccer_match.id),
        }
    finally:
        await session.close()


async def _seed_static_players_only() -> None:
    models = __import__("super_soccer_showdown.db.models", fromlist=["*"])

    session = bootstrap.get_db_session()
    try:
        session.add_all(
            [
                models.PokemonData(pokeapi_id=301, name="Squirtle", height_cm=50.0, weight_kg=9.0, power=75.0),
                models.PokemonData(pokeapi_id=302, name="Charmander", height_cm=60.0, weight_kg=8.5, power=79.0),
                models.PokemonData(pokeapi_id=303, name="Bulbasaur", height_cm=70.0, weight_kg=6.9, power=74.0),
                models.PokemonData(pokeapi_id=304, name="Eevee", height_cm=30.0, weight_kg=6.5, power=71.0),
                models.PokemonData(pokeapi_id=305, name="Snorlax", height_cm=210.0, weight_kg=460.0, power=99.0),
                models.StarWarsData(swapi_id=401, name="Luke", height_cm=172.0, weight_kg=77.0, power=95.0),
                models.StarWarsData(swapi_id=402, name="Han", height_cm=180.0, weight_kg=80.0, power=88.0),
                models.StarWarsData(swapi_id=403, name="Leia", height_cm=150.0, weight_kg=49.0, power=90.0),
                models.StarWarsData(swapi_id=404, name="Chewbacca", height_cm=228.0, weight_kg=112.0, power=99.0),
                models.StarWarsData(swapi_id=405, name="Yoda", height_cm=66.0, weight_kg=17.0, power=97.0),
            ]
        )
        await session.commit()
    finally:
        await session.close()


class TestEndpointsE2E:
    def test_register_user_persists_in_database(self):
        username = f"e2e_user_{uuid4().hex[:8]}"

        response = user_handlers.register_user_handler(
            {"body": json.dumps({"username": username})},
            None,
        )
        body = parse_body(response)

        assert response["statusCode"] == 201
        assert body["username"] == username
        assert int(body["user_id"]) > 0
        assert body["jwt_token"]

    def test_register_user_allows_unique_usernames(self):
        first_username = f"unique_a_{uuid4().hex[:8]}"
        second_username = f"unique_b_{uuid4().hex[:8]}"

        first_response = user_handlers.register_user_handler({"body": json.dumps({"username": first_username})}, None)
        second_response = user_handlers.register_user_handler({"body": json.dumps({"username": second_username})}, None)

        first_body = parse_body(first_response)
        second_body = parse_body(second_response)

        assert first_response["statusCode"] == 201
        assert second_response["statusCode"] == 201
        assert first_body["username"] == first_username
        assert second_body["username"] == second_username
        assert first_body["user_id"] != second_body["user_id"]

    def test_generate_universe_team_endpoint_returns_created_team(self):
        registration = _register_user(f"generate_team_{uuid4().hex[:8]}")
        bootstrap.get_event_loop().run_until_complete(_seed_static_players_only())
        event = {
            "headers": _auth_header_from_register_payload(registration),
            "pathParameters": {"universe": "pokemon"},
            "body": json.dumps({"defenders": 2, "attackers": 2}),
        }

        response = team_handlers.generate_universe_team_handler(event, None)
        body = parse_body(response)

        assert response["statusCode"] == 201
        assert body["universe"] == "pokemon"
        assert body["owner_user_id"] == int(registration["user_id"])
        assert len(body["team_composition"]) == 5

    def test_list_teams_endpoint_returns_paginated_payload(self):
        starwars_registration = _register_user(f"teams_sw_{uuid4().hex[:8]}")
        pokemon_registration = _register_user(f"teams_pk_{uuid4().hex[:8]}")
        bootstrap.get_event_loop().run_until_complete(
            _seed_team_and_match_data(
                starwars_user_id=int(starwars_registration["user_id"]),
                pokemon_user_id=int(pokemon_registration["user_id"]),
            )
        )

        event = {
            "headers": _auth_header_from_register_payload(starwars_registration),
            "queryStringParameters": {
                "page": "1",
                "page_size": "10",
                "universe": "starwars",
                "user_id": starwars_registration["user_id"],
            },
        }

        response = team_handlers.list_teams_handler(event, None)
        body = parse_body(response)

        assert response["statusCode"] == 200
        assert body["pagination"]["page"] == 1
        assert body["pagination"]["page_size"] == 10
        assert body["pagination"]["universe"] == "starwars"
        assert body["pagination"]["user_id"] == int(starwars_registration["user_id"])
        assert body["pagination"]["total_items"] >= 1
        assert body["pagination"]["total_pages"] >= 1
        assert len(body["items"]) >= 1
        assert body["items"][0]["universe"] == "starwars"

    def test_list_matches_endpoint_returns_paginated_payload(self):
        starwars_registration = _register_user(f"matches_sw_{uuid4().hex[:8]}")
        pokemon_registration = _register_user(f"matches_pk_{uuid4().hex[:8]}")
        seeded = bootstrap.get_event_loop().run_until_complete(
            _seed_team_and_match_data(
                starwars_user_id=int(starwars_registration["user_id"]),
                pokemon_user_id=int(pokemon_registration["user_id"]),
            )
        )

        event = {
            "headers": _auth_header_from_register_payload(starwars_registration),
            "queryStringParameters": {
                "page": "1",
                "page_size": "10",
                "user_id": starwars_registration["user_id"],
            },
        }

        response = matches_handlers.list_matches_handler(event, None)
        body = parse_body(response)

        assert response["statusCode"] == 200
        assert body["pagination"]["page"] == 1
        assert body["pagination"]["page_size"] == 10
        assert body["pagination"]["user_id"] == int(starwars_registration["user_id"])
        assert body["pagination"]["total_items"] >= 1
        assert body["pagination"]["total_pages"] >= 1
        assert len(body["items"]) >= 1
        assert body["items"][0]["id"] == seeded["match_id"]
        assert body["items"][0]["showdown_actions"][0]["is_goal"] is True

    def test_generate_showdown_endpoint_returns_created_match(self):
        starwars_registration = _register_user(f"showdown_sw_{uuid4().hex[:8]}")
        pokemon_registration = _register_user(f"showdown_pk_{uuid4().hex[:8]}")
        seeded = bootstrap.get_event_loop().run_until_complete(
            _seed_team_and_match_data(
                starwars_user_id=int(starwars_registration["user_id"]),
                pokemon_user_id=int(pokemon_registration["user_id"]),
            )
        )

        event = {
            "headers": _auth_header_from_register_payload(starwars_registration),
            "body": json.dumps(
                {
                    "team_1": seeded["starwars_team_id"],
                    "team_2": seeded["pokemon_team_id"],
                }
            ),
        }

        response = matches_handlers.generate_showdown_handler(event, None)
        body = parse_body(response)

        assert response["statusCode"] == 201
        assert int(body["id"]) > 0
        assert body["starwars_team_id"] == seeded["starwars_team_id"]
        assert body["pokemon_team_id"] == seeded["pokemon_team_id"]
        assert body["starwars_user_id"] == int(starwars_registration["user_id"])
        assert body["pokemon_user_id"] == int(pokemon_registration["user_id"])
        assert isinstance(body["showdown_actions"], list)
