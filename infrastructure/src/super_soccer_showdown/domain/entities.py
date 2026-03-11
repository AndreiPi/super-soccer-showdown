from dataclasses import dataclass
from enum import Enum

from infrastructure.src.super_soccer_showdown.service.exceptions import InvalidLineupError


class Universe(str, Enum):
    STARWARS = "starwars"
    POKEMON = "pokemon"


class Position(str, Enum):
    GOALIE = "Goalie"
    DEFENCE = "Defence"
    OFFENCE = "Offence"


@dataclass(frozen=True)
class Player:
    name: str
    weight_kg: float
    height_cm: int


@dataclass(frozen=True)
class AssignedPlayer:
    name: str
    weight_kg: float
    height_cm: int
    position: Position


@dataclass(frozen=True)
class Lineup:
    defenders: int = 2
    attackers: int = 2

    def __post_init__(self) -> None:
        if self.defenders < 0 or self.attackers < 0:
            raise InvalidLineupError("Defenders and attackers must be non-negative integers.")
        if self.defenders + self.attackers != 4:
            raise InvalidLineupError("Lineup must satisfy defenders + attackers = 4.")


@dataclass(frozen=True)
class Team:
    universe: Universe
    lineup: Lineup
    players: list[AssignedPlayer]
