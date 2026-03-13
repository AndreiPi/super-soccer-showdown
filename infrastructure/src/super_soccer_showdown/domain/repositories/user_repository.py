from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from super_soccer_showdown.db.models import User
from super_soccer_showdown.domain.persistence.user import DomainUser, user_from_db


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, username: str) -> DomainUser:
        try:
            user = User(
                username=username,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            return user_from_db(user)
        except IntegrityError as e:
            await self.session.rollback()
            raise ValueError(f"Username '{username}' already exists") from e

    async def get_user_by_username(self, username: str) -> DomainUser | None:
        stmt = select(User).where(User.username == username)
        result = await self.session.scalar(stmt)
        return user_from_db(result) if result else None

    async def get_user_by_id(self, user_id: int) -> DomainUser | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.scalar(stmt)
        return user_from_db(result) if result else None
