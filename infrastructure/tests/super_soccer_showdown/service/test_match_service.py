import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from super_soccer_showdown.domain.entities import Position, Universe
from super_soccer_showdown.domain.persistence.player_data import DomainPlayerData
from super_soccer_showdown.domain.persistence.soccer_match import DomainSoccerMatch
from super_soccer_showdown.domain.persistence.soccer_team import DomainSoccerTeam
from super_soccer_showdown.domain.persistence.team_composition import DomainTeamComposition
from super_soccer_showdown.service.match_service import (
    GenerateShowdownUseCase,
    ListMatchesUseCase,
    get_attackers,
    get_defenders,
    get_goalie,
    get_teams_by_universe,
    is_goal,
    player_power,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_player(
    source_id: int,
    name: str,
    height_cm: float = 170.0,
    weight_kg: float = 70.0,
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


def make_composition(player: DomainPlayerData, position: Position) -> DomainTeamComposition:
    return DomainTeamComposition(player=player, position=position)


def make_full_team(team_id: int, universe: Universe, owner_user_id: int = 1) -> DomainSoccerTeam:
    """Team with 1 goalie + 2 defenders + 2 attackers."""
    u = universe
    base = team_id * 10
    goalie  = make_player(base + 1, "Goalie",    200, 100, 10.0, u)
    def1    = make_player(base + 2, "Defender1", 170,  90,  8.0, u)
    def2    = make_player(base + 3, "Defender2", 160,  85,  7.0, u)
    att1    = make_player(base + 4, "Attacker1", 150,  70,  6.0, u)
    att2    = make_player(base + 5, "Attacker2", 140,  65,  5.0, u)
    return DomainSoccerTeam(
        id=team_id,
        universe=universe,
        owner_user_id=owner_user_id,
        team_composition=[
            make_composition(goalie, Position.GOALIE),
            make_composition(def1,   Position.DEFENCE),
            make_composition(def2,   Position.DEFENCE),
            make_composition(att1,   Position.OFFENCE),
            make_composition(att2,   Position.OFFENCE),
        ],
    )


def make_domain_match(starwars_team_id: int = 1, pokemon_team_id: int = 2) -> DomainSoccerMatch:
    return DomainSoccerMatch(
        id=99,
        starwars_team_id=starwars_team_id,
        pokemon_team_id=pokemon_team_id,
        created_at=datetime.now(timezone.utc),
        winner_team_id=None,
        starwars_user_id=1,
        pokemon_user_id=2,
        showdown_actions=[],
    )


# ---------------------------------------------------------------------------
# get_teams_by_universe
# ---------------------------------------------------------------------------

class TestGetTeamsByUniverse:
    def test_sw_first_returns_correct_order(self):
        sw   = make_full_team(1, Universe.STARWARS)
        poke = make_full_team(2, Universe.POKEMON)
        result_sw, result_poke = get_teams_by_universe(sw, poke)
        assert result_sw is sw
        assert result_poke is poke

    def test_pokemon_first_reorders_correctly(self):
        sw   = make_full_team(1, Universe.STARWARS)
        poke = make_full_team(2, Universe.POKEMON)
        result_sw, result_poke = get_teams_by_universe(poke, sw)
        assert result_sw is sw
        assert result_poke is poke

    def test_both_starwars_raises_value_error(self):
        team1 = make_full_team(1, Universe.STARWARS)
        team2 = make_full_team(2, Universe.STARWARS)
        with pytest.raises(ValueError, match="[Ss]howdown"):
            get_teams_by_universe(team1, team2)

    def test_both_pokemon_raises_value_error(self):
        team1 = make_full_team(1, Universe.POKEMON)
        team2 = make_full_team(2, Universe.POKEMON)
        with pytest.raises(ValueError):
            get_teams_by_universe(team1, team2)


# ---------------------------------------------------------------------------
# get_attackers / get_defenders / get_goalie
# ---------------------------------------------------------------------------

class TestGetAttackers:
    def test_returns_all_offence_players(self):
        team = make_full_team(1, Universe.POKEMON)
        attackers = get_attackers(team)
        assert len(attackers) == 2
        assert all(isinstance(p, DomainPlayerData) for p in attackers)

    def test_returns_empty_list_when_no_attackers(self):
        goalie = make_player(1, "Goalie")
        team = DomainSoccerTeam(
            id=1, universe=Universe.POKEMON, owner_user_id=1,
            team_composition=[make_composition(goalie, Position.GOALIE)],
        )
        assert get_attackers(team) == []


class TestGetDefenders:
    def test_returns_all_defence_players(self):
        team = make_full_team(1, Universe.STARWARS)
        defenders = get_defenders(team)
        assert len(defenders) == 2

    def test_returns_empty_list_when_no_defenders(self):
        goalie = make_player(1, "Goalie")
        team = DomainSoccerTeam(
            id=1, universe=Universe.POKEMON, owner_user_id=1,
            team_composition=[make_composition(goalie, Position.GOALIE)],
        )
        assert get_defenders(team) == []


class TestGetGoalie:
    def test_returns_the_goalie_player(self):
        team = make_full_team(1, Universe.POKEMON)
        goalie = get_goalie(team)
        assert goalie is not None
        assert goalie.name == "Goalie"

    def test_returns_none_when_no_goalie(self):
        attacker = make_player(1, "Attacker")
        team = DomainSoccerTeam(
            id=1, universe=Universe.POKEMON, owner_user_id=1,
            team_composition=[make_composition(attacker, Position.OFFENCE)],
        )
        assert get_goalie(team) is None


# ---------------------------------------------------------------------------
# player_power
# ---------------------------------------------------------------------------

class TestPlayerPower:
    def test_returns_player_power_when_positive(self):
        player = make_player(1, "Test", power=25.0)
        assert player_power(player) == 25.0

    def test_uses_height_weight_fallback_when_power_is_none(self):
        player = make_player(1, "Test", height_cm=180.0, weight_kg=90.0, power=None)
        with patch("super_soccer_showdown.service.match_service.random") as mock_rng:
            mock_rng.randint.return_value = 3
            result = player_power(player)
        assert result == 180.0 * 90.0 * 3

    def test_uses_fallback_when_power_is_zero(self):
        player = make_player(1, "Test", height_cm=150.0, weight_kg=60.0, power=0.0)
        with patch("super_soccer_showdown.service.match_service.random") as mock_rng:
            mock_rng.randint.return_value = 2
            result = player_power(player)
        assert result == 150.0 * 60.0 * 2


# ---------------------------------------------------------------------------
# is_goal
# ---------------------------------------------------------------------------

class TestIsGoal:
    def test_returns_true_when_attacker_overwhelms_defense(self):
        attacker = make_player(1, "Attacker", power=5000.0)
        defender = make_player(2, "Defender", power=1.0)
        goalie   = make_player(3, "Goalie",   power=1.0)
        with patch("super_soccer_showdown.service.match_service.random") as mock_rng:
            mock_rng.gauss.return_value = 1.0
            result = is_goal(attacker, defender, goalie)
        assert result is True

    def test_returns_false_when_defense_overwhelms_attacker(self):
        attacker = make_player(1, "Attacker", power=1.0)
        defender = make_player(2, "Defender", power=5000.0)
        goalie   = make_player(3, "Goalie",   power=5000.0)
        with patch("super_soccer_showdown.service.match_service.random") as mock_rng:
            mock_rng.gauss.return_value = 1.0
            result = is_goal(attacker, defender, goalie)
        assert result is False

    def test_returns_false_when_gauss_returns_zero(self):
        """Zero multiplier means zero attack value, never a goal."""
        attacker = make_player(1, "Attacker", power=1000.0)
        defender = make_player(2, "Defender", power=1.0)
        goalie   = make_player(3, "Goalie",   power=1.0)
        with patch("super_soccer_showdown.service.match_service.random") as mock_rng:
            mock_rng.gauss.return_value = 0.0
            result = is_goal(attacker, defender, goalie)
        assert result is False


# ---------------------------------------------------------------------------
# ListMatchesUseCase
# ---------------------------------------------------------------------------

class TestListMatchesUseCase:
    def _make(self, matches=None, total=0):
        repo = AsyncMock()
        repo.list_matches_paginated = AsyncMock(return_value=(matches or [], total))
        return ListMatchesUseCase(match_repository=repo), repo

    async def test_valid_params_returns_items_and_pagination(self):
        use_case, _ = self._make(matches=[], total=0)
        result = await use_case.execute(page=1, page_size=10)
        assert result["items"] == []
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["page_size"] == 10
        assert result["pagination"]["total_items"] == 0
        assert result["pagination"]["total_pages"] == 0

    async def test_total_pages_rounds_up_correctly(self):
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

    async def test_user_id_zero_raises_value_error(self):
        use_case, _ = self._make()
        with pytest.raises(ValueError, match="user_id"):
            await use_case.execute(page=1, page_size=10, user_id=0)

    async def test_user_id_filter_forwarded_to_repository(self):
        use_case, repo = self._make()
        await use_case.execute(page=2, page_size=5, user_id=42)
        repo.list_matches_paginated.assert_awaited_once_with(page=2, page_size=5, user_id=42)


# ---------------------------------------------------------------------------
# GenerateShowdownUseCase
# ---------------------------------------------------------------------------

class TestGenerateShowdownUseCase:
    def _make(self, sw_team=None, poke_team=None):
        sw   = sw_team   or make_full_team(1, Universe.STARWARS)
        poke = poke_team or make_full_team(2, Universe.POKEMON)

        team_repo  = AsyncMock()
        match_repo = AsyncMock()

        async def _get_team(team_id):
            return {1: sw, 2: poke}.get(team_id)

        team_repo.get_team_by_id            = AsyncMock(side_effect=_get_team)
        match_repo.create_match_with_actions = AsyncMock(return_value=make_domain_match())

        return (
            GenerateShowdownUseCase(team_repository=team_repo, match_repository=match_repo),
            team_repo,
            match_repo,
        )

    async def test_valid_teams_creates_and_returns_match(self):
        use_case, _, match_repo = self._make()
        result = await use_case.execute(team_1_id=1, team_2_id=2)
        match_repo.create_match_with_actions.assert_awaited_once()
        assert isinstance(result, DomainSoccerMatch)

    async def test_unknown_team_id_raises_value_error(self):
        team_repo  = AsyncMock()
        match_repo = AsyncMock()
        team_repo.get_team_by_id = AsyncMock(return_value=None)
        use_case = GenerateShowdownUseCase(team_repository=team_repo, match_repository=match_repo)
        with pytest.raises(ValueError, match="[Tt]eam"):
            await use_case.execute(team_1_id=99, team_2_id=100)

    async def test_both_teams_same_universe_raises_value_error(self):
        sw1 = make_full_team(1, Universe.STARWARS)
        sw2 = make_full_team(2, Universe.STARWARS)
        use_case, _, _ = self._make(sw_team=sw1, poke_team=sw2)
        with pytest.raises(ValueError):
            await use_case.execute(team_1_id=1, team_2_id=2)

    async def test_team_missing_goalie_raises_value_error(self):
        attacker = make_player(1, "Attacker", universe=Universe.STARWARS)
        defender = make_player(2, "Defender", universe=Universe.STARWARS)
        no_goalie = DomainSoccerTeam(
            id=1, universe=Universe.STARWARS, owner_user_id=1,
            team_composition=[
                make_composition(attacker, Position.OFFENCE),
                make_composition(defender, Position.DEFENCE),
            ],
        )
        use_case, _, _ = self._make(sw_team=no_goalie)
        with pytest.raises(ValueError, match="[Gg]oalie"):
            await use_case.execute(team_1_id=1, team_2_id=2)

    async def test_team_missing_attackers_raises_value_error(self):
        goalie  = make_player(1, "Goalie",  universe=Universe.STARWARS)
        defender = make_player(2, "Defender", universe=Universe.STARWARS)
        no_attackers = DomainSoccerTeam(
            id=1, universe=Universe.STARWARS, owner_user_id=1,
            team_composition=[
                make_composition(goalie,   Position.GOALIE),
                make_composition(defender, Position.DEFENCE),
            ],
        )
        use_case, _, _ = self._make(sw_team=no_attackers)
        with pytest.raises(ValueError, match="[Aa]ttacker"):
            await use_case.execute(team_1_id=1, team_2_id=2)

    async def test_team_missing_defenders_raises_value_error(self):
        goalie   = make_player(1, "Goalie",   universe=Universe.STARWARS)
        attacker = make_player(2, "Attacker", universe=Universe.STARWARS)
        no_defenders = DomainSoccerTeam(
            id=1, universe=Universe.STARWARS, owner_user_id=1,
            team_composition=[
                make_composition(goalie,   Position.GOALIE),
                make_composition(attacker, Position.OFFENCE),
            ],
        )
        use_case, _, _ = self._make(sw_team=no_defenders)
        with pytest.raises(ValueError, match="[Dd]efender"):
            await use_case.execute(team_1_id=1, team_2_id=2)
