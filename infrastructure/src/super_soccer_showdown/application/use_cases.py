from super_soccer_showdown.domain.entities import Lineup, Team, Universe
from infrastructure.src.super_soccer_showdown.service.exceptions import TeamGenerationError
from infrastructure.src.super_soccer_showdown.service.services import assign_positions
from super_soccer_showdown.ports.player_provider import PlayerProvider


class GenerateTeamUseCase:
    def __init__(self, providers: dict[Universe, PlayerProvider]) -> None:
        self._providers = providers

    def execute(self, universe: Universe, lineup: Lineup) -> Team:
        provider = self._providers.get(universe)
        if provider is None:
            raise TeamGenerationError(f"No player provider configured for universe: {universe}")

        players = provider.get_random_players(5)
        assigned_players = assign_positions(players=players, lineup=lineup)
        return Team(universe=universe, lineup=lineup, players=assigned_players)


class GenerateShowdownUseCase:
    def __init__(self, generate_team_use_case: GenerateTeamUseCase) -> None:
        self._generate_team_use_case = generate_team_use_case

    def execute(self, starwars_lineup: Lineup, pokemon_lineup: Lineup) -> dict[str, Team]:
        return {
            Universe.STARWARS.value: self._generate_team_use_case.execute(
                Universe.STARWARS,
                starwars_lineup,
            ),
            Universe.POKEMON.value: self._generate_team_use_case.execute(
                Universe.POKEMON,
                pokemon_lineup,
            ),
        }
