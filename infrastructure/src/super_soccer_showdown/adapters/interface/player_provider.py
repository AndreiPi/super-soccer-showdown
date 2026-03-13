from __future__ import annotations

from typing import Protocol

from super_soccer_showdown.domain.persistence.player_data import DomainPlayerData


class PlayerProvider(Protocol):
    async def get_random_players(self, count: int) -> list[DomainPlayerData]:
        """Return count unique and valid players for a universe."""

    async def get_all_players(self) -> list[DomainPlayerData]:
        """Return all valid players for a universe from the external provider."""
