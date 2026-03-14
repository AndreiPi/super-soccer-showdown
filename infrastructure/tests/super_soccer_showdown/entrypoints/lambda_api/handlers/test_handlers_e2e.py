import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from super_soccer_showdown.domain.entities import Position, Universe
from super_soccer_showdown.domain.persistence.player_data import DomainPlayerData
from super_soccer_showdown.domain.persistence.showdown_action import DomainShowdownAction
from super_soccer_showdown.domain.persistence.soccer_match import DomainSoccerMatch
from super_soccer_showdown.domain.persistence.soccer_team import DomainSoccerTeam
from super_soccer_showdown.domain.persistence.team_composition import DomainTeamComposition
from super_soccer_showdown.service.jwt_service import generate_token
from super_soccer_showdown.entrypoints.lambda_api.handlers import docs_handlers, matches_handlers, team_handlers, user_handlers


def make_auth_headers(user_id: int = 1, username: str = "ash") -> dict[str, str]:
    token = generate_token(user_id, username)
    return {"Authorization": f"Bearer {token}"}


def run_async(coro):
    return asyncio.run(coro)


def parse_body(response: dict) -> dict:
    return json.loads(response["body"])


def make_player(
    source_id: int,
    name: str,
    universe: Universe,
    height_cm: float = 170.0,
    weight_kg: float = 70.0,
    power: float | None = 10.0,
) -> DomainPlayerData:
    return DomainPlayerData(
        source_id=source_id,
        name=name,
        height_cm=height_cm,
        weight_kg=weight_kg,
        universe=universe,
        power=power,
    )


def make_team(team_id: int, universe: Universe, owner_user_id: int) -> DomainSoccerTeam:
    goalie = make_player(team_id * 10 + 1, "Goalie", universe, height_cm=200, weight_kg=100)
    defender_1 = make_player(team_id * 10 + 2, "Defender One", universe, height_cm=180, weight_kg=90)
    defender_2 = make_player(team_id * 10 + 3, "Defender Two", universe, height_cm=175, weight_kg=85)
    attacker_1 = make_player(team_id * 10 + 4, "Attacker One", universe, height_cm=160, weight_kg=70)
    attacker_2 = make_player(team_id * 10 + 5, "Attacker Two", universe, height_cm=155, weight_kg=65)
    return DomainSoccerTeam(
        id=team_id,
        universe=universe,
        owner_user_id=owner_user_id,
        team_composition=[
            DomainTeamComposition(goalie, Position.GOALIE),
            DomainTeamComposition(defender_1, Position.DEFENCE),
            DomainTeamComposition(defender_2, Position.DEFENCE),
            DomainTeamComposition(attacker_1, Position.OFFENCE),
            DomainTeamComposition(attacker_2, Position.OFFENCE),
        ],
    )


def make_match() -> DomainSoccerMatch:
    action = DomainShowdownAction(
        id=1,
        soccer_match_id=50,
        action_number=1,
        team_id=1,
        team_universe=Universe.STARWARS,
        scorer="Luke",
        scorer_source_id=1,
        against="Pikachu",
        is_goal=True,
    )
    return DomainSoccerMatch(
        id=50,
        starwars_team_id=1,
        pokemon_team_id=2,
        created_at=datetime(2026, 3, 13, tzinfo=timezone.utc),
        winner_team_id=1,
        starwars_user_id=1,
        pokemon_user_id=2,
        showdown_actions=[action],
    )


class TestEndpointsE2E:
    def test_generate_universe_team_endpoint_returns_created_team(self, monkeypatch):
        generated_team = make_team(team_id=10, universe=Universe.POKEMON, owner_user_id=7)
        use_case = AsyncMock()
        use_case.execute = AsyncMock(return_value=generated_team)

        monkeypatch.setattr(team_handlers, "run_handler", run_async)
        monkeypatch.setattr(team_handlers, "build_generate_team_use_case", lambda: use_case)

        event = {
            "headers": make_auth_headers(user_id=7, username="misty"),
            "pathParameters": {"universe": "pokemon"},
            "body": json.dumps({"defenders": 2, "attackers": 2}),
        }

        response = team_handlers.generate_universe_team_handler(event, None)
        body = parse_body(response)

        assert response["statusCode"] == 201
        assert body["id"] == 10
        assert body["universe"] == "pokemon"
        assert body["owner_user_id"] == 7
        assert len(body["team_composition"]) == 5

    def test_list_teams_endpoint_returns_paginated_payload(self, monkeypatch):
        listed_team = make_team(team_id=11, universe=Universe.STARWARS, owner_user_id=4)
        use_case = AsyncMock()
        use_case.execute = AsyncMock(
            return_value={
                "items": [listed_team],
                "pagination": {
                    "page": 1,
                    "page_size": 10,
                    "universe": "starwars",
                    "user_id": 4,
                    "total_items": 1,
                    "total_pages": 1,
                },
            }
        )

        monkeypatch.setattr(team_handlers, "run_handler", run_async)
        monkeypatch.setattr(team_handlers, "build_list_teams_use_case", lambda: use_case)

        event = {
            "headers": make_auth_headers(user_id=4, username="luke"),
            "queryStringParameters": {"page": "1", "page_size": "10", "universe": "starwars", "user_id": "4"},
        }

        response = team_handlers.list_teams_handler(event, None)
        body = parse_body(response)

        assert response["statusCode"] == 200
        assert body["pagination"]["universe"] == "starwars"
        assert body["pagination"]["user_id"] == 4
        assert len(body["items"]) == 1
        assert body["items"][0]["id"] == 11

    def test_generate_showdown_endpoint_returns_created_match(self, monkeypatch):
        created_match = make_match()
        use_case = AsyncMock()
        use_case.execute = AsyncMock(return_value=created_match)

        monkeypatch.setattr(matches_handlers, "run_handler", run_async)
        monkeypatch.setattr(matches_handlers, "build_generate_showdown_use_case", lambda: use_case)

        event = {
            "headers": make_auth_headers(user_id=1, username="obiwan"),
            "body": json.dumps({"team_1": 1, "team_2": 2}),
        }

        response = matches_handlers.generate_showdown_handler(event, None)
        body = parse_body(response)

        assert response["statusCode"] == 201
        assert body["id"] == 50
        assert body["winner_team_id"] == 1
        assert len(body["showdown_actions"]) == 1
        assert body["showdown_actions"][0]["is_goal"] is True

    def test_list_matches_endpoint_returns_paginated_payload(self, monkeypatch):
        listed_match = make_match()
        use_case = AsyncMock()
        use_case.execute = AsyncMock(
            return_value={
                "items": [listed_match],
                "pagination": {
                    "page": 1,
                    "page_size": 10,
                    "user_id": 2,
                    "total_items": 1,
                    "total_pages": 1,
                },
            }
        )

        monkeypatch.setattr(matches_handlers, "run_handler", run_async)
        monkeypatch.setattr(matches_handlers, "build_list_matches_use_case", lambda: use_case)

        event = {
            "headers": make_auth_headers(user_id=2, username="han"),
            "queryStringParameters": {"page": "1", "page_size": "10", "user_id": "2"},
        }

        response = matches_handlers.list_matches_handler(event, None)
        body = parse_body(response)

        assert response["statusCode"] == 200
        assert body["pagination"]["user_id"] == 2
        assert body["items"][0]["id"] == 50
        assert body["items"][0]["showdown_actions"][0]["scorer"] == "Luke"

    def test_refresh_jwt_token_endpoint_returns_new_token_payload(self, monkeypatch):
        use_case = AsyncMock()
        use_case.execute = AsyncMock(
            return_value={
                "user_id": "9",
                "username": "leia",
                "jwt_token": "fresh-token",
            }
        )

        monkeypatch.setattr(user_handlers, "run_handler", run_async)
        monkeypatch.setattr(user_handlers, "build_refresh_jwt_token_use_case", lambda: use_case)

        event = {
            "headers": make_auth_headers(user_id=9, username="leia"),
            "pathParameters": {"user_id": "9"},
        }

        response = user_handlers.refresh_jwt_token_handler(event, None)
        body = parse_body(response)

        assert response["statusCode"] == 200
        assert body["user_id"] == "9"
        assert body["username"] == "leia"
        assert body["jwt_token"] == "fresh-token"

    def test_docs_endpoint_returns_swagger_ui_html(self):
        response = docs_handlers.docs_handler({"path": "/docs"}, None)

        assert response["statusCode"] == 200
        assert response["headers"]["Content-Type"] == "text/html; charset=utf-8"
        assert "SwaggerUIBundle" in response["body"]
        assert "openapi.json" in response["body"]

    def test_openapi_endpoint_returns_spec_with_expected_paths(self):
        event = {"path": "/openapi.json", "requestContext": {"stage": "Prod"}}

        response = docs_handlers.docs_handler(event, None)
        body = parse_body(response)

        assert response["statusCode"] == 200
        assert response["headers"]["Content-Type"] == "application/json"
        assert body["openapi"] == "3.0.3"
        assert body["servers"][0]["url"] == "/Prod"
        assert "/teams/{universe}" in body["paths"]
        assert "/users/register" in body["paths"]
        assert "/showdown" in body["paths"]
