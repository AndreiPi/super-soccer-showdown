
import os

from super_soccer_showdown.domain.repositories.player_repository import PlayerRepository
from super_soccer_showdown.domain.repositories.soccer_team_repository import SoccerTeamRepository
from super_soccer_showdown.domain.persistence.player_data import DomainPlayerData
from super_soccer_showdown.domain.persistence.team_composition import DomainTeamComposition
from super_soccer_showdown.domain.persistence.soccer_team import DomainSoccerTeam
from super_soccer_showdown.service.exceptions import TeamGenerationError
from super_soccer_showdown.adapters.interface.player_provider import PlayerProvider
from super_soccer_showdown.domain.entities import Position, Lineup, Universe

TEAM_SIZE = int(os.environ.get("TEAM_SIZE", 5))

class GenerateTeamUseCase:

    def __init__(
        self,
        providers: dict[Universe, PlayerProvider],
        team_repository: SoccerTeamRepository,
        player_repository: PlayerRepository,
    ) -> None:
        self._providers = providers
        self._team_repository = team_repository
        self._player_repository = player_repository

    async def execute(self, user_id: int, universe: Universe, lineup: Lineup) -> DomainSoccerTeam:
        provider = self._providers.get(universe)
        if provider is None:
            raise TeamGenerationError(f"No player provider configured for universe: {universe}")

        try:
            players = await provider.get_random_players(TEAM_SIZE)
        except TeamGenerationError:
            players = await self._player_repository.get_random_static_players(universe=universe, count=TEAM_SIZE)

        if len(players) < TEAM_SIZE:
            raise TeamGenerationError(f"Not enough valid players fetched for universe: {universe}")
        
        assigned_players = assign_positions(players=players, lineup=lineup)
        soccer_team = DomainSoccerTeam(universe=universe, owner_user_id =user_id, team_composition=assigned_players)
        return await self._team_repository.create_team(soccer_team)


class ListTeamsUseCase:

    def __init__(self, team_repository: SoccerTeamRepository) -> None:
        self._team_repository = team_repository

    async def execute(
        self,
        page: int = 1,
        page_size: int = 10,
        universe: Universe | None = None,
        owner_user_id: int | None = None,
    ) -> dict:
        if page < 1:
            raise ValueError("Query parameter 'page' must be >= 1.")
        if page_size < 1 or page_size > 100:
            raise ValueError("Query parameter 'page_size' must be between 1 and 100.")
        if owner_user_id is not None and owner_user_id < 1:
            raise ValueError("Query parameter 'user_id' must be >= 1.")

        teams, total = await self._team_repository.list_teams_paginated(
            page=page,
            page_size=page_size,
            universe=universe,
            owner_user_id=owner_user_id,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "items": teams,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "universe": universe.value if universe is not None else None,
                "user_id": owner_user_id,
                "total_items": total,
                "total_pages": total_pages,
            },
        }



def assign_positions(players: list[DomainPlayerData], lineup: Lineup) -> list[DomainTeamComposition]:

    # Goalie is always the tallest player.
    goalie_index = max(
        range(len(players)),
        key=lambda idx: (players[idx].height_cm, players[idx].weight_kg, players[idx].name),
    )
    goalie = players[goalie_index]

    remaining = players[:goalie_index] + players[goalie_index + 1 :]

    # Defence players are selected as the heaviest among non-goalie players.
    defenders = sorted(
        remaining,
        key=lambda p: (p.weight_kg, p.height_cm, p.name),
        reverse=True,
    )[: lineup.defenders]

    defender_names = {player.source_id for player in defenders}
    attacker_pool = [p for p in remaining if p.source_id not in defender_names]

    # Offence players are selected as the shortest among the remaining players.
    attackers = sorted(
        attacker_pool,
        key=lambda p: (p.height_cm, p.weight_kg, p.name),
    )[: lineup.attackers]

    assigned = [
        DomainTeamComposition(
            player = goalie,
            position=Position.GOALIE,
        )
    ]

    assigned.extend(
        DomainTeamComposition(
            player = player,
            position=Position.DEFENCE,
        )
        for player in defenders
    )

    assigned.extend(
        DomainTeamComposition(
            player = player,
            position=Position.OFFENCE,
        )
        for player in attackers
    )

    return assigned

