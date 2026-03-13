from enum import Enum

class Universe(Enum):
    STARWARS = "starwars"
    POKEMON = "pokemon"


class Position(Enum):
    GOALIE = "Goalie"
    DEFENCE = "Defence"
    OFFENCE = "Offence"

class Lineup():
    attackers: 2
    defenders: 2

    def __init__(self, attackers: int, defenders:int):
        self.attackers = attackers
        self.defenders = defenders
