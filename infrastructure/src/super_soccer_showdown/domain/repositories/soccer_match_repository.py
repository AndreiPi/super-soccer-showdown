from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from super_soccer_showdown.db.models.soccer_match import SoccerMatch
from super_soccer_showdown.domain.persistence.showdown_action import (
    showdown_action_to_db,
)
from super_soccer_showdown.domain.persistence.soccer_match import (
    DomainSoccerMatch,
    soccer_match_from_db,
    soccer_match_to_db,
)


class SoccerMatchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_match_with_actions(
        self,
        match: DomainSoccerMatch,
    ) -> DomainSoccerMatch:
        try:
            db_match = soccer_match_to_db(match)
            self.session.add(db_match)
            await self.session.flush()

            for action in match.showdown_actions:
                db_goal = showdown_action_to_db(action, soccer_match_id=db_match.id)
                self.session.add(db_goal)

            await self.session.commit()
            stmt = (
                select(SoccerMatch)
                .where(SoccerMatch.id == db_match.id)
                .options(
                    selectinload(SoccerMatch.showdown_actions)
                )
            )
            result = await self.session.execute(stmt)
            db_match = result.scalar_one()

            persisted_match = soccer_match_from_db(db_match)
            return persisted_match
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f"Can't create match due to an error {e}.") from e

    async def list_matches_paginated(self, page: int, page_size: int, user_id: int | None = None) -> tuple[list[DomainSoccerMatch], int]:
        offset = (page - 1) * page_size

        total_stmt = select(func.count()).select_from(SoccerMatch)
        if user_id is not None:
            total_stmt = total_stmt.where(
                or_(
                    SoccerMatch.starwars_user_id == user_id,
                    SoccerMatch.pokemon_user_id == user_id,
                )
            )

        total_result = await self.session.execute(total_stmt)
        total = int(total_result.scalar_one())

        stmt = select(SoccerMatch)
        if user_id is not None:
            stmt = stmt.where(
                or_(
                    SoccerMatch.starwars_user_id == user_id,
                    SoccerMatch.pokemon_user_id == user_id,
                )
            )

        stmt = (
            stmt
            .order_by(SoccerMatch.id.desc())
            .offset(offset)
            .limit(page_size)
            .options(selectinload(SoccerMatch.showdown_actions))
        )

        result = await self.session.execute(stmt)
        db_matches = result.scalars().all()
        matches = [soccer_match_from_db(match) for match in db_matches]
        return matches, total
