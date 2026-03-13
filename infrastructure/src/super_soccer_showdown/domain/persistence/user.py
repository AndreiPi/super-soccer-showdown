from __future__ import annotations
from datetime import datetime

from super_soccer_showdown.db.models import User


class DomainUser:
    id: int | None
    username: str
    created_at: datetime
    updated_at: datetime

    def __init__(
        self,
        username: str,
        created_at: datetime,
        updated_at: datetime,
        id: int | None = None,
    ) -> None:
        self.id = id
        self.username = username
        self.created_at = created_at
        self.updated_at = updated_at


def user_from_db(model: User) -> DomainUser:
    return DomainUser(
        id=model.id,
        username=model.username,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def user_to_db(entity: DomainUser) -> User:
    model = User(
        username=entity.username,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
    if entity.id is not None:
        model.id = entity.id
    return model
