import pytest
from unittest.mock import AsyncMock

from super_soccer_showdown.domain.entities import Lineup, Position, Universe
from super_soccer_showdown.domain.persistence.player_data import DomainPlayerData
from super_soccer_showdown.domain.persistence.soccer_team import DomainSoccerTeam
from super_soccer_showdown.service.exceptions import TeamGenerationError
from super_soccer_showdown.service.team_service import (
    GenerateTeamUseCase,
    ListTeamsUseCase,
    assign_positions,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_player(
    source_id: int,
    name: str,
    height_cm: float,
    weight_kg: float,
    power: float | None = 10.0,
    universe: Universe = Universe.POKEMON,
) -> DomainPlayerData:
    return DomainPlayerData(
        source_id=source_id,
        name=name,
        height_cm=height_cm,
        weight_kg=weight_kg,
        universe=universe,
        power=power,
    )


def make_five_players(universe: Universe = Universe.POKEMON) -> list[DomainPlayerData]:
    """
    Five players with deterministic ordering:
      - id=1: height=200 → tallest    → GOALIE
      - id=2: weight=100 → heaviest remaining → DEFENCE
      - id=3: weight=95  → second heaviest    → DEFENCE
      - id=4: height=130 → shortest remaining → OFFENCE
      - id=5: height=150 → second shortest    → OFFENCE
    """
    return [
        make_player(1, "Player1", height_cm=200, weight_kg=80,  universe=universe),
        make_player(2, "Player2", height_cm=160, weight_kg=100, universe=universe),
        make_player(3, "Player3", height_cm=170, weight_kg=95,  universe=universe),
        make_player(4, "Player4", height_cm=130, weight_kg=70,  universe=universe),
        make_player(5, "Player5", height_cm=150, weight_kg=65,  universe=universe),
    ]


# ---------------------------------------------------------------------------
# assign_positions
# ---------------------------------------------------------------------------

class TestAssignPositions:
    def test_tallest_player_is_assigned_goalie(self):
        players = make_five_players()
        result  = assign_positions(players, Lineup(defenders=2, attackers=2))
        goalie_comps = [c for c in result if c.position == Position.GOALIE]
        assert len(goalie_comps) == 1
        assert goalie_comps[0].player.source_id == 1   # height=200

    def test_heaviest_remaining_become_defenders(self):
        players = make_five_players()
        result  = assign_positions(players, Lineup(defenders=2, attackers=2))
        defender_ids = {c.player.source_id for c in result if c.position == Position.DEFENCE}
        assert defender_ids == {2, 3}   # weight=100, weight=95

    def test_shortest_remaining_become_attackers(self):
        players = make_five_players()
        result  = assign_positions(players, Lineup(defenders=2, attackers=2))
        attacker_ids = {c.player.source_id for c in result if c.position == Position.OFFENCE}
        assert attacker_ids == {4, 5}   # height=130, height=150

    def test_total_assigned_equals_input_count(self):
        players = make_five_players()
        result  = assign_positions(players, Lineup(defenders=2, attackers=2))
        assert len(result) == 5

    def test_one_defender_one_attacker_lineup_assigns_three_players(self):
        players = make_five_players()[:3]
        result  = assign_positions(players, Lineup(defenders=1, attackers=1))
        positions = [c.position for c in result]
        assert positions.count(Position.GOALIE)  == 1
        assert positions.count(Position.DEFENCE) == 1
        assert positions.count(Position.OFFENCE) == 1

    def test_goalie_is_not_also_assigned_as_defender_or_attacker(self):
        players = make_five_players()
        result  = assign_positions(players, Lineup(defenders=2, attackers=2))
        goalie_id = next(c.player.source_id for c in result if c.position == Position.GOALIE)
        other_ids = {c.player.source_id for c in result if c.position != Position.GOALIE}
        assert goalie_id not in other_ids


# ---------------------------------------------------------------------------
# GenerateTeamUseCase
# ---------------------------------------------------------------------------

class TestGenerateTeamUseCase:
    def _make(
        self,
        universe: Universe = Universe.POKEMON,
        provider_players=None,
        provider_error: Exception | None = None,
        static_players=None,
    ):
        mock_provider = AsyncMock()
        if provider_error is not None:
            mock_provider.get_random_players = AsyncMock(side_effect=provider_error)
        else:
            mock_provider.get_random_players = AsyncMock(
                return_value=provider_players or make_five_players(universe)
            )

        player_repo = AsyncMock()
        player_repo.get_random_static_players = AsyncMock(
            return_value=static_players or make_five_players(universe)
        )

        team_repo = AsyncMock()
        team_repo.create_team = AsyncMock(
            return_value=DomainSoccerTeam(id=1, universe=universe, owner_user_id=1)
        )

        use_case = GenerateTeamUseCase(
            providers={universe: mock_provider},
            team_repository=team_repo,
            player_repository=player_repo,
        )
        return use_case, mock_provider, player_repo, team_repo

    async def test_provider_success_creates_team_via_repository(self):
        use_case, _, _, team_repo = self._make()
        result = await use_case.execute(
            user_id=1, universe=Universe.POKEMON, lineup=Lineup(defenders=2, attackers=2)
        )
        team_repo.create_team.assert_awaited_once()
        assert isinstance(result, DomainSoccerTeam)

    async def test_provider_failure_falls_back_to_static_players(self):
        use_case, _, player_repo, team_repo = self._make(
            provider_error=TeamGenerationError("API unreachable")
        )
        await use_case.execute(
            user_id=1, universe=Universe.POKEMON, lineup=Lineup(defenders=2, attackers=2)
        )
        player_repo.get_random_static_players.assert_awaited_once_with(
            universe=Universe.POKEMON, count=5
        )
        team_repo.create_team.assert_awaited_once()

    async def test_missing_provider_raises_team_generation_error(self):
        player_repo = AsyncMock()
        team_repo   = AsyncMock()
        use_case = GenerateTeamUseCase(
            providers={},
            team_repository=team_repo,
            player_repository=player_repo,
        )
        with pytest.raises(TeamGenerationError, match="[Pp]rovider"):
            await use_case.execute(
                user_id=1, universe=Universe.POKEMON, lineup=Lineup(defenders=2, attackers=2)
            )

    async def test_not_enough_players_after_fallback_raises_error(self):
        use_case, _, _, _ = self._make(
            provider_error=TeamGenerationError("API down"),
            static_players=make_five_players()[:2],   # Only 2 — not enough
        )
        with pytest.raises(TeamGenerationError, match="[Nn]ot enough"):
            await use_case.execute(
                user_id=1, universe=Universe.POKEMON, lineup=Lineup(defenders=2, attackers=2)
            )

    async def test_team_is_created_with_correct_universe_and_owner(self):
        use_case, _, _, team_repo = self._make(universe=Universe.STARWARS)
        await use_case.execute(
            user_id=42, universe=Universe.STARWARS, lineup=Lineup(defenders=2, attackers=2)
        )
        call_args = team_repo.create_team.call_args[0][0]
        assert call_args.universe == Universe.STARWARS
        assert call_args.owner_user_id == 42


# ---------------------------------------------------------------------------
# ListTeamsUseCase
# ---------------------------------------------------------------------------

class TestListTeamsUseCase:
    def _make(self, teams=None, total: int = 0):
        team_repo = AsyncMock()
        team_repo.list_teams_paginated = AsyncMock(return_value=(teams or [], total))
        return ListTeamsUseCase(team_repository=team_repo), team_repo

    async def test_valid_params_returns_items_and_pagination(self):
        use_case, _ = self._make(total=0)
        result = await use_case.execute(page=1, page_size=10)
        assert result["items"] == []
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["page_size"] == 10
        assert result["pagination"]["total_items"] == 0
        assert result["pagination"]["total_pages"] == 0

    async def test_total_pages_rounds_up(self):
        use_case, _ = self._make(total=21)
        result = await use_case.execute(page=1, page_size=10)
        assert result["pagination"]["total_pages"] == 3   # ceil(21/10)

    async def test_page_below_one_raises_value_error(self):
        use_case, _ = self._make()
        with pytest.raises(ValueError, match="page"):
            await use_case.execute(page=0, page_size=10)

    async def test_page_size_zero_raises_value_error(self):
        use_case, _ = self._make()
        with pytest.raises(ValueError, match="page_size"):
            await use_case.execute(page=1, page_size=0)

    async def test_page_size_above_100_raises_value_error(self):
        use_case, _ = self._make()
        with pytest.raises(ValueError, match="page_size"):
            await use_case.execute(page=1, page_size=101)

    async def test_owner_user_id_zero_raises_value_error(self):
        use_case, _ = self._make()
        with pytest.raises(ValueError, match="user_id"):
            await use_case.execute(page=1, page_size=10, owner_user_id=0)

    async def test_filters_forwarded_to_repository(self):
        use_case, repo = self._make()
        await use_case.execute(
            page=2, page_size=5, universe=Universe.POKEMON, owner_user_id=7
        )
        repo.list_teams_paginated.assert_awaited_once_with(
            page=2, page_size=5, universe=Universe.POKEMON, owner_user_id=7
        )

    async def test_universe_included_in_pagination_response(self):
        use_case, _ = self._make()
        result = await use_case.execute(page=1, page_size=10, universe=Universe.STARWARS)
        assert result["pagination"]["universe"] == Universe.STARWARS.value

    async def test_no_universe_filter_pagination_shows_none(self):
        use_case, _ = self._make()
        result = await use_case.execute(page=1, page_size=10)
        assert result["pagination"]["universe"] is None
