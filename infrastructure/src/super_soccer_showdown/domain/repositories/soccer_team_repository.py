from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from super_soccer_showdown.db.models import SoccerTeam, StarWarsTeamComposition, PokemonTeamComposition, UniverseEnum
from super_soccer_showdown.domain.entities import Universe
from super_soccer_showdown.domain.persistence.soccer_team import DomainSoccerTeam, soccer_team_from_db, soccer_team_to_db
from super_soccer_showdown.domain.repositories.player_repository import PlayerRepository

class SoccerTeamRepository:
    def __init__(self, session: AsyncSession, player_repository: PlayerRepository):
        self.session = session
        self.player_repository = player_repository

    async def create_team(self, team: DomainSoccerTeam) -> DomainSoccerTeam:
        try:
            await self.player_repository.upsert_static_players(team)
            db_team = soccer_team_to_db(team)
            self.session.add(db_team)
            await self.session.commit()
            stmt = (
                select(SoccerTeam)
                .where(SoccerTeam.id == db_team.id)
                .options(
                    selectinload(SoccerTeam.starwars_players).selectinload(StarWarsTeamComposition.player),
                    selectinload(SoccerTeam.pokemon_players).selectinload(PokemonTeamComposition.player),
                )
            )
            result = await self.session.execute(stmt)
            db_team = result.scalar_one()
            return soccer_team_from_db(db_team)
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f"Can't add team due to an error {e}.") from e

    async def get_team_by_id(self, team_id: int) -> DomainSoccerTeam | None:
        stmt = (
            select(SoccerTeam)
            .where(SoccerTeam.id == team_id)
            .options(
                selectinload(SoccerTeam.starwars_players).selectinload(StarWarsTeamComposition.player),
                selectinload(SoccerTeam.pokemon_players).selectinload(PokemonTeamComposition.player),
            )
        )
        result = await self.session.execute(stmt)
        db_team = result.scalar_one_or_none()
        if db_team is None:
            return None
        return soccer_team_from_db(db_team)

    async def list_teams_paginated(
        self,
        page: int,
        page_size: int,
        universe: Universe | None = None,
        owner_user_id: int | None = None,
    ) -> tuple[list[DomainSoccerTeam], int]:
        offset = (page - 1) * page_size

        total_stmt = select(func.count()).select_from(SoccerTeam)
        if universe is not None:
            total_stmt = total_stmt.where(SoccerTeam.universe == UniverseEnum(universe.value))
        if owner_user_id is not None:
            total_stmt = total_stmt.where(SoccerTeam.owner_user_id == owner_user_id)

        total_result = await self.session.execute(total_stmt)
        total = int(total_result.scalar_one())

        stmt = select(SoccerTeam)
        if universe is not None:
            stmt = stmt.where(SoccerTeam.universe == UniverseEnum(universe.value))
        if owner_user_id is not None:
            stmt = stmt.where(SoccerTeam.owner_user_id == owner_user_id)

        stmt = (
            stmt
            .order_by(SoccerTeam.id.desc())
            .offset(offset)
            .limit(page_size)
            .options(
                selectinload(SoccerTeam.starwars_players).selectinload(StarWarsTeamComposition.player),
                selectinload(SoccerTeam.pokemon_players).selectinload(PokemonTeamComposition.player),
            )
        )
        result = await self.session.execute(stmt)
        db_teams = result.scalars().all()
        teams = [soccer_team_from_db(team) for team in db_teams]
        return teams, total
