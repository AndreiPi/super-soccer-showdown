import os
from typing import Any

import requests

from super_soccer_showdown.domain.entities import Player
from infrastructure.src.super_soccer_showdown.service.exceptions import TeamGenerationError
from .interface.player_provider import PlayerProvider
from .interface.random_provider import RandomProvider


class PokeApiPlayerProvider(PlayerProvider):
    BASE_URL = os.environ.get("POKEAPI_BASE_URL")
    MAX_POKEMON_ID = os.environ.get("MAX_POKEMON_ID")

    def __init__(self, session: requests.Session, random_provider: RandomProvider) -> None:
        self._session = session
        self._random = random_provider

    def get_random_players(self, count: int) -> list[Player]:
        players: list[Player] = []
        selected_names: set[str] = set()
        max_attempts = 120

        for _ in range(max_attempts):
            if len(players) == count:
                return players

            pokemon_id = self._random.randint(1, self.MAX_POKEMON_ID)
            data = self._fetch_pokemon(pokemon_id)
            if data is None:
                continue

            player = self._to_player(data)
            if player is None or player.name in selected_names:
                continue

            selected_names.add(player.name)
            players.append(player)

        raise TeamGenerationError("Could not fetch enough valid Pokemon players.")

    def _fetch_pokemon(self, pokemon_id: int) -> dict[str, Any] | None:
        response = self._session.get(f"{self.BASE_URL}/{pokemon_id}", timeout=8)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _to_player(data: dict[str, Any]) -> Player | None:
        name = str(data.get("name", "")).strip().replace("-", " ").title()
        height_dm = data.get("height")
        weight_hg = data.get("weight")

        if not name or height_dm in {None, ""} or weight_hg in {None, ""}:
            return None

        try:
            height_cm = int(height_dm) * 10
            weight_kg = float(weight_hg) / 10.0
        except (TypeError, ValueError):
            return None

        if height_cm <= 0 or weight_kg <= 0:
            return None

        return Player(name=name, weight_kg=weight_kg, height_cm=height_cm)
