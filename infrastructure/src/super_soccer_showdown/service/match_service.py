
from datetime import datetime, timezone
import os
import random

from super_soccer_showdown.domain.persistence.soccer_match import DomainSoccerMatch
from super_soccer_showdown.domain.entities import Position, Universe
from super_soccer_showdown.domain.persistence.player_data import DomainPlayerData
from super_soccer_showdown.domain.persistence.showdown_action import DomainShowdownAction
from super_soccer_showdown.domain.persistence.soccer_team import DomainSoccerTeam
from super_soccer_showdown.domain.repositories.soccer_match_repository import SoccerMatchRepository
from super_soccer_showdown.domain.repositories.soccer_team_repository import SoccerTeamRepository

SHOWDOWN_ACTIONS = int(os.environ.get("SHOWDOWN_ACTIONS", 20))
SHOWDOWN_ATTACK_PROBABILITY = float(os.environ.get("SHOWDOWN_ATTACK_PROBABILITY", 0.5))
ATTACKER_POWER_MU = float(os.environ.get("ATTACKER_POWER_MU", 5))
ATTACKER_POWER_SIGMA = float(os.environ.get("ATTACKER_POWER_SIGMA", 2.5))

class GenerateShowdownUseCase:
    def __init__(self, team_repository: SoccerTeamRepository, match_repository: SoccerMatchRepository) -> None:
        self._team_repository = team_repository
        self._match_repository = match_repository

    async def execute(self, team_1_id: int, team_2_id: int, user_id: int) -> DomainSoccerMatch:
        team_1 = await self._team_repository.get_team_by_id(team_1_id)
        team_2 = await self._team_repository.get_team_by_id(team_2_id)

        if team_1 is None or team_2 is None:
            raise ValueError("One or both team IDs do not exist.")
        
        if team_1.owner_user_id != user_id and team_2.owner_user_id != user_id:
            raise ValueError("User must own at least one of the teams to initiate a showdown.")
        
        starwars_team, pokemon_team = get_teams_by_universe(team_1, team_2)

        team_1_attackers = get_attackers(team_1)
        team_2_attackers = get_attackers(team_2)
        team_1_defenders = get_defenders(team_1)
        team_2_defenders = get_defenders(team_2)
        team_1_goalie = get_goalie(team_1)
        team_2_goalie = get_goalie(team_2)

        if not team_1_attackers or not team_2_attackers:
            raise ValueError("Both teams must have at least one attacker.")

        if team_1_goalie is None or team_2_goalie is None:
            raise ValueError("Both teams must have one goalie.")

        if not team_1_defenders or not team_2_defenders:
            raise ValueError("Both teams must have at least one defender.")
        
        goals: list[DomainShowdownAction] = []
        goal_balance= 0
        for action in range(1, SHOWDOWN_ACTIONS + 1):
            if random.random() < SHOWDOWN_ATTACK_PROBABILITY:
                continue
            team_1_attacking = random.random() < 0.5
            if team_1_attacking:
                attacker = random.choice(team_1_attackers)
                defender = random.choice(team_2_defenders)
                goalie = team_2_goalie

            else:
                attacker = random.choice(team_2_attackers)
                defender = random.choice(team_1_defenders)
                goalie = team_1_goalie
            goal_result = is_goal(attacker, defender, goalie)
            if goal_result:
                goal_balance += 1 if team_1_attacking else -1

            attacking_team = team_1 if team_1_attacking else team_2
            goals.append(
                DomainShowdownAction(
                    action_number=action,
                    team_id=attacking_team.id,
                    team_universe=attacking_team.universe,
                    scorer=attacker.name,
                    scorer_source_id=attacker.source_id,
                    against=defender.name,
                    is_goal=goal_result,
                )
            )

        match = DomainSoccerMatch(
            starwars_team_id=starwars_team.id,
            pokemon_team_id=pokemon_team.id,
            starwars_user_id=starwars_team.owner_user_id,
            pokemon_user_id=pokemon_team.owner_user_id,
            created_at=datetime.now(timezone.utc),
            winner_team_id=team_1.id if goal_balance > 0 else team_2.id if goal_balance < 0 else None,
            showdown_actions=goals,
        )

        return await self._match_repository.create_match_with_actions(match)


class ListMatchesUseCase:
    def __init__(self, match_repository: SoccerMatchRepository) -> None:
        self._match_repository = match_repository

    async def execute(self, page: int = 1, page_size: int = 10, user_id: int | None = None) -> dict:
        if page < 1:
            raise ValueError("Query parameter 'page' must be >= 1.")
        if page_size < 1 or page_size > 100:
            raise ValueError("Query parameter 'page_size' must be between 1 and 100.")
        if user_id is not None and user_id < 1:
            raise ValueError("Query parameter 'user_id' must be >= 1.")

        matches, total = await self._match_repository.list_matches_paginated(
            page=page,
            page_size=page_size,
            user_id=user_id,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "items": matches,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "user_id": user_id,
                "total_items": total,
                "total_pages": total_pages,
            },
        }


def get_teams_by_universe(team_1: DomainSoccerTeam, team_2: DomainSoccerTeam) -> tuple[DomainSoccerTeam, DomainSoccerTeam]:
    if team_1.universe == Universe.STARWARS and team_2.universe == Universe.POKEMON:
        return team_1, team_2
    if team_1.universe == Universe.POKEMON and team_2.universe == Universe.STARWARS:
        return team_2, team_1
    raise ValueError("Showdown requires one Star Wars team and one Pokemon team.")


def get_attackers(team: DomainSoccerTeam) -> list[DomainPlayerData]:
    return [
        composition.player
        for composition in team.team_composition
        if composition.position == Position.OFFENCE
    ]


def get_defenders(team: DomainSoccerTeam) -> list[DomainPlayerData]:
    return [
        composition.player
        for composition in team.team_composition
        if composition.position == Position.DEFENCE
    ]


def get_goalie(team: DomainSoccerTeam) -> DomainPlayerData | None:
    for composition in team.team_composition:
        if composition.position == Position.GOALIE:
            return composition.player
    return None


def player_power(player: DomainPlayerData) -> float:
    if player.power is not None and player.power > 0:
        return player.power
    fallback = player.height_cm * player.weight_kg * random.randint(1, 5)
    return fallback


def is_goal(attacker: DomainPlayerData, defender: DomainPlayerData, goalie: DomainPlayerData) -> bool:
    attack_value = player_power(attacker) * abs(random.gauss(ATTACKER_POWER_MU, ATTACKER_POWER_SIGMA))
    defense_value = player_power(defender) + player_power(goalie)
    return attack_value > defense_value
