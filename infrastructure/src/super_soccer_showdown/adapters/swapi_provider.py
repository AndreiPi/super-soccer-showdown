import os
import random
import asyncio
from typing import Any

import httpx

from super_soccer_showdown.domain.entities import Universe
from super_soccer_showdown.domain.persistence.player_data import DomainPlayerData
from super_soccer_showdown.service.exceptions import TeamGenerationError
from .interface.player_provider import PlayerProvider


class SwapiPlayerProvider(PlayerProvider):
    BASE_URL = os.environ.get("SWAPI_BASE_URL")
    API_TIMEOUT_SECONDS = int(os.environ.get("SWAPI_API_TIMEOUT_SECONDS", 3))
    PAGE_SIZE = 10
    PAGE_FETCH_WORKERS = max(1, int(os.environ.get("SWAPI_PAGE_FETCH_WORKERS", 10)))

    def __init__(self, session: httpx.AsyncClient) -> None:
        self._session = session
        self._people_cache: list[dict[str, Any]] | None = None

    async def get_random_players(self, count: int) -> list[DomainPlayerData]:
        players: list[DomainPlayerData] = []
        selected_names: set[str] = set()
        people = list(await self.fetch_all_people())

        while people and len(players) < count:
            random_index = random.randint(0, len(people) - 1)
            data = people.pop(random_index)
            player_id = self.extract_id_from_url(str(data.get("url", "")))
            if player_id is None:
                continue

            player = self.to_player(data, player_id)
            if player is None or player.name in selected_names:
                continue

            selected_names.add(player.name)
            players.append(player)

        if len(players) == count:
            return players

        raise TeamGenerationError("Could not fetch enough valid Star Wars players.")

    async def get_all_players(self) -> list[DomainPlayerData]:
        players: list[DomainPlayerData] = []
        seen_ids: set[int] = set()

        for data in await self.fetch_all_people():
            player_id = self.extract_id_from_url(str(data.get("url", "")))
            if player_id is None:
                continue

            player = self.to_player(data, player_id)
            if player is None or player.source_id in seen_ids:
                continue

            seen_ids.add(player.source_id)
            players.append(player)

        return players

    async def fetch_all_people(self) -> list[dict[str, Any]]:
        if self._people_cache is not None:
            return self._people_cache

        first_page = await self.fetch_people_page(1)
        if first_page is None:
            return []

        all_people = list(first_page.get("results") or [])

        try:
            total_count = int(first_page.get("count") or 0)
        except (TypeError, ValueError):
            total_count = 0

        total_pages = max(1, (total_count + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        if total_pages == 1:
            self._people_cache = all_people
            return all_people

        page_numbers = list(range(2, total_pages + 1))
        for index in range(0, len(page_numbers), self.PAGE_FETCH_WORKERS):
            batch = page_numbers[index : index + self.PAGE_FETCH_WORKERS]
            payloads = await asyncio.gather(*(self.fetch_people_page(page) for page in batch))

            for payload in payloads:
                if payload is None:
                    continue
                all_people.extend(payload.get("results") or [])

        self._people_cache = all_people
        return all_people

    async def fetch_people_page(self, page_number: int) -> dict[str, Any] | None:
        try:
            response = await self._session.get(
                self.BASE_URL,
                params={"page": page_number},
                timeout=self.API_TIMEOUT_SECONDS,
            )
            if response.status_code != 200:
                return None
            return response.json()
        except httpx.HTTPError:
            return None

    def extract_id_from_url(self, url: str) -> int | None:
        if not url:
            return None
        parts = url.rstrip("/").split("/")
        if not parts:
            return None
        try:
            value = int(parts[-1])
        except ValueError:
            return None
        return value if value > 0 else None

    def to_player(self, data: dict[str, Any], player_id: int) -> DomainPlayerData | None:
        name = str(data.get("name", "")).strip()
        mass_value = str(data.get("mass", "")).replace(",", "").strip()
        height_value = str(data.get("height", "")).strip()
        vehicles = data.get("vehicles", [])
        starships = data.get("starships", [])

        try:
            source_id = player_id
            weight_kg = float(mass_value)
            height_cm = float(height_value)
            num_vehicles = len(vehicles) + len(starships)
        except ValueError:
            return None

        if source_id <= 0 or weight_kg <= 0 or height_cm <= 0:
            return None

        power = round(height_cm * weight_kg * max(num_vehicles, 1) / 100.0, 2)

        return DomainPlayerData(
            source_id=source_id,
            name=name,
            weight_kg=weight_kg,
            height_cm=height_cm,
            power=power,
            universe=Universe.STARWARS,
        )
