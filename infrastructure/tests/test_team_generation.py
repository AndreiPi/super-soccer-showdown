import unittest

from super_soccer_showdown.application.use_cases import GenerateTeamUseCase
from super_soccer_showdown.domain.entities import Lineup, Player, Position, Universe
from super_soccer_showdown.domain.exceptions import InvalidLineupError
from super_soccer_showdown.domain.services import assign_positions


class FakeProvider:
    def __init__(self, players: list[Player]) -> None:
        self._players = players

    def get_random_players(self, count: int) -> list[Player]:
        return self._players[:count]


class TeamGenerationTests(unittest.TestCase):
    def test_lineup_requires_four_outfield_players(self) -> None:
        with self.assertRaises(InvalidLineupError):
            Lineup(defenders=3, attackers=2)

    def test_assign_positions_respects_business_rules(self) -> None:
        players = [
            Player(name="A", weight_kg=75, height_cm=180),
            Player(name="B", weight_kg=95, height_cm=190),
            Player(name="C", weight_kg=90, height_cm=172),
            Player(name="D", weight_kg=60, height_cm=165),
            Player(name="E", weight_kg=70, height_cm=168),
        ]

        lineup = Lineup(defenders=2, attackers=2)
        assigned = assign_positions(players=players, lineup=lineup)

        self.assertEqual(5, len(assigned))

        goalie = [p for p in assigned if p.position == Position.GOALIE]
        defenders = [p for p in assigned if p.position == Position.DEFENCE]
        attackers = [p for p in assigned if p.position == Position.OFFENCE]

        self.assertEqual(1, len(goalie))
        self.assertEqual(2, len(defenders))
        self.assertEqual(2, len(attackers))
        self.assertEqual("B", goalie[0].name)
        self.assertEqual({"C", "A"}, {p.name for p in defenders})
        self.assertEqual({"D", "E"}, {p.name for p in attackers})

    def test_generate_team_use_case_returns_expected_universe(self) -> None:
        players = [
            Player(name="P1", weight_kg=10, height_cm=100),
            Player(name="P2", weight_kg=20, height_cm=110),
            Player(name="P3", weight_kg=30, height_cm=120),
            Player(name="P4", weight_kg=40, height_cm=130),
            Player(name="P5", weight_kg=50, height_cm=140),
        ]

        use_case = GenerateTeamUseCase(providers={Universe.POKEMON: FakeProvider(players)})

        team = use_case.execute(universe=Universe.POKEMON, lineup=Lineup(defenders=1, attackers=3))

        self.assertEqual(Universe.POKEMON, team.universe)
        self.assertEqual(5, len(team.players))


if __name__ == "__main__":
    unittest.main()
