from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from super_soccer_showdown.db.base import Base

if TYPE_CHECKING:
    from super_soccer_showdown.db.models.soccer_match import SoccerMatch
    from super_soccer_showdown.db.models.soccer_team import SoccerTeam


class User(Base):
    __tablename__ = "app_user"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(sa.String(100), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    starwars_matches: Mapped[list["SoccerMatch"]] = relationship(
        "SoccerMatch",
        back_populates="starwars_user",
        foreign_keys="SoccerMatch.starwars_user_id",
    )
    pokemon_matches: Mapped[list["SoccerMatch"]] = relationship(
        "SoccerMatch",
        back_populates="pokemon_user",
        foreign_keys="SoccerMatch.pokemon_user_id",
    )
    soccer_teams: Mapped[list["SoccerTeam"]] = relationship(
        "SoccerTeam",
        back_populates="owner_user",
        foreign_keys="SoccerTeam.owner_user_id",
    )
