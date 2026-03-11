from typing import Protocol

from super_soccer_showdown.domain.entities import Player


class PlayerProvider(Protocol):
    def get_random_players(self, count: int) -> list[Player]:
        """Return count unique and valid players for a universe."""
