import os
import random
import asyncio
from typing import Any

import httpx

from super_soccer_showdown.domain.entities import Universe
from super_soccer_showdown.domain.persistence.player_data import DomainPlayerData
from super_soccer_showdown.service.exceptions import TeamGenerationError
from .interface.player_provider import PlayerProvider


class PokeApiPlayerProvider(PlayerProvider):
    BASE_URL = os.environ.get("POKEAPI_BASE_URL")
    FETCH_TIMEOUT_SECONDS = int(os.environ.get("POKEAPI_FETCH_TIMEOUT_SECONDS", 3))
    DETAIL_FETCH_WORKERS = max(1, int(os.environ.get("POKEAPI_DETAIL_FETCH_WORKERS", 20)))

    def __init__(self, session: httpx.AsyncClient) -> None:
        self._session = session
        self._pokemon_entries_cache: list[dict[str, Any]] | None = None

    async def get_random_players(self, count: int) -> list[DomainPlayerData]:
        players: list[DomainPlayerData] = []
        selected_names: set[str] = set()
        entries = [
            entry
            for entry in await self.fetch_all_pokemon_entries()
            if str(entry.get("url", "")).strip()
        ]

        while entries and len(players) < count:
            random_index = random.randint(0, len(entries) - 1)
            pokemon_url = str(entries.pop(random_index).get("url", "")).strip()
            if not pokemon_url:
                continue

            data = await self.fetch_pokemon_by_url(pokemon_url)
            if data is None:
                continue

            player = self.to_player(data)
            if player is None or player.name in selected_names:
                continue

            selected_names.add(player.name)
            players.append(player)

        if len(players) == count:
            return players

        raise TeamGenerationError("Could not fetch enough valid Pokemon players.")

    async def get_all_players(self) -> list[DomainPlayerData]:
        players: list[DomainPlayerData] = []
        seen_ids: set[int] = set()
        pokemon_urls = [
            str(entry.get("url", "")).strip()
            for entry in await self.fetch_all_pokemon_entries()
            if str(entry.get("url", "")).strip()
        ]

        for index in range(0, len(pokemon_urls), self.DETAIL_FETCH_WORKERS):
            batch = pokemon_urls[index : index + self.DETAIL_FETCH_WORKERS]
            payloads = await asyncio.gather(*(self.fetch_pokemon_by_url(url) for url in batch))

            for data in payloads:
                if data is None:
                    continue

                player = self.to_player(data)
                if player is None or player.source_id in seen_ids:
                    continue

                seen_ids.add(player.source_id)
                players.append(player)

        return players

    async def fetch_all_pokemon_entries(self) -> list[dict[str, Any]]:
        if self._pokemon_entries_cache is not None:
            return self._pokemon_entries_cache

        all_entries: list[dict[str, Any]] = []
        next_url: str | None = f"{self.BASE_URL}?limit=100"

        while next_url:
            try:
                response = await self._session.get(next_url, timeout=self.FETCH_TIMEOUT_SECONDS)
                if response.status_code != 200:
                    break
                payload = response.json()
            except httpx.HTTPError:
                break

            all_entries.extend(payload.get("results") or [])
            next_url = payload.get("next")

        self._pokemon_entries_cache = all_entries
        return all_entries

    async def fetch_pokemon_by_url(self, pokemon_url: str) -> dict[str, Any] | None:
        try:
            response = await self._session.get(pokemon_url, timeout=self.FETCH_TIMEOUT_SECONDS)
            if response.status_code == 404:
                return None
            if response.status_code != 200:
                return None
            return response.json()
        except httpx.HTTPError:
            return None

    def to_player(self, data: dict[str, Any]) -> DomainPlayerData | None:
        name = str(data.get("name", "")).strip()
        source_id_value = data.get("id")
        height_dm = str(data.get("height", "")).strip()
        weight_hg = str(data.get("weight", "")).strip()
        abilities = data.get("abilities", [])

        if not name or source_id_value in {None, ""} or height_dm in {None, ""} or weight_hg in {None, ""}:
            return None

        try:
            source_id = int(source_id_value)
            height_cm = float(height_dm) * 10.0
            weight_kg = float(weight_hg) / 10.0
            num_abilities = len(abilities)
        except (TypeError, ValueError):
            return None

        if source_id <= 0 or height_cm <= 0 or weight_kg <= 0:
            return None

        power = round(height_cm * weight_kg * max(num_abilities, 1) / 100.0, 2)

        return DomainPlayerData(
            source_id=source_id,
            name=name,
            weight_kg=weight_kg,
            height_cm=height_cm,
            power=power,
            universe=Universe.POKEMON,
        )
