from super_soccer_showdown.domain.entities import AssignedPlayer, Lineup, Player, Position
from infrastructure.src.super_soccer_showdown.service.exceptions import TeamGenerationError


def assign_positions(players: list[Player], lineup: Lineup) -> list[AssignedPlayer]:
    if len(players) != 5:
        raise TeamGenerationError("Each team must contain exactly 5 players.")

    if len({player.name for player in players}) != 5:
        raise TeamGenerationError("Player names must be unique inside a team.")

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

    defender_names = {player.name for player in defenders}
    attacker_pool = [p for p in remaining if p.name not in defender_names]

    # Offence players are selected as the shortest among the remaining players.
    attackers = sorted(
        attacker_pool,
        key=lambda p: (p.height_cm, p.weight_kg, p.name),
    )[: lineup.attackers]

    assigned = [
        AssignedPlayer(
            name=goalie.name,
            weight_kg=goalie.weight_kg,
            height_cm=goalie.height_cm,
            position=Position.GOALIE,
        )
    ]

    assigned.extend(
        AssignedPlayer(
            name=player.name,
            weight_kg=player.weight_kg,
            height_cm=player.height_cm,
            position=Position.DEFENCE,
        )
        for player in defenders
    )

    assigned.extend(
        AssignedPlayer(
            name=player.name,
            weight_kg=player.weight_kg,
            height_cm=player.height_cm,
            position=Position.OFFENCE,
        )
        for player in attackers
    )

    if len(assigned) != 5:
        raise TeamGenerationError("Failed to allocate exactly 5 players by position.")

    return assigned
