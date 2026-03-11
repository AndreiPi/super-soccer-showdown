from enum import Enum


class UniverseEnum(str, Enum):
    STARWARS = "starwars"
    POKEMON = "pokemon"


class PositionEnum(str, Enum):
    GOALIE = "Goalie"
    DEFENCE = "Defence"
    OFFENCE = "Offence"
