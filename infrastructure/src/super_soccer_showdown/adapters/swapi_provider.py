import os
from typing import Any

import requests

from super_soccer_showdown.domain.entities import Player
from infrastructure.src.super_soccer_showdown.service.exceptions import TeamGenerationError
from .interface.player_provider import PlayerProvider
from .interface.random_provider import RandomProvider


class SwapiPlayerProvider(PlayerProvider):
    BASE_URL = os.environ.get("SWAPI_BASE_URL")
    MAX_SW_ID = os.environ.get("MAX_SW_ID")

    def __init__(self, session: requests.Session, random_provider: RandomProvider) -> None:
        self._session = session
        self._random = random_provider
        self._count_cache: int | None = None

    def get_random_players(self, count: int) -> list[Player]:
        players: list[Player] = []
        selected_names: set[str] = set()
        max_attempts = 120

        for _ in range(max_attempts):
            if len(players) == count:
                return players

            player_id = self._random.randint(1, int(self.MAX_SW_ID))
            data = self._fetch_person(player_id)
            if data is None:
                continue

            player = self._to_player(data)
            if player is None or player.name in selected_names:
                continue

            selected_names.add(player.name)
            players.append(player)

        raise TeamGenerationError("Could not fetch enough valid Star Wars players.")

    def _fetch_person(self, person_id: int) -> dict[str, Any] | None:
        response = self._session.get(f"{self.BASE_URL}/{person_id}/", timeout=8)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _to_player(data: dict[str, Any]) -> Player | None:
        name = str(data.get("name", "")).strip()
        mass_value = str(data.get("mass", "")).replace(",", "").strip()
        height_value = str(data.get("height", "")).strip()

        if not name or mass_value in {"", "unknown", "n/a"} or height_value in {"", "unknown", "n/a"}:
            return None

        try:
            weight_kg = float(mass_value)
            height_cm = int(height_value)
        except ValueError:
            return None

        if weight_kg <= 0 or height_cm <= 0:
            return None

        return Player(name=name, weight_kg=weight_kg, height_cm=height_cm)
