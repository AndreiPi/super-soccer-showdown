from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from super_soccer_showdown.db.base import Base

if TYPE_CHECKING:
    from super_soccer_showdown.db.models.showdown_action import ShowdownAction
    from super_soccer_showdown.db.models.soccer_team import SoccerTeam
    from super_soccer_showdown.db.models.user import User


class SoccerMatch(Base):
    __tablename__ = "soccer_match"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    starwars_team_id: Mapped[int | None] = mapped_column(sa.Integer, sa.ForeignKey("soccer_team.id"), nullable=False)
    pokemon_team_id: Mapped[int | None] = mapped_column(sa.Integer, sa.ForeignKey("soccer_team.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    winner_team_id: Mapped[int | None] = mapped_column(sa.Integer, sa.ForeignKey("soccer_team.id"), nullable=True)
    starwars_user_id: Mapped[int | None] = mapped_column(sa.Integer, sa.ForeignKey("app_user.id"), nullable=False)
    pokemon_user_id: Mapped[int | None] = mapped_column(sa.Integer, sa.ForeignKey("app_user.id"), nullable=False)

    starwars_user: Mapped["User"] = relationship(
        "User",
        back_populates="starwars_matches",
        foreign_keys=[starwars_user_id],
    )
    pokemon_user: Mapped["User"] = relationship(
        "User",
        back_populates="pokemon_matches",
        foreign_keys=[pokemon_user_id],
    )
    starwars_team: Mapped["SoccerTeam"] = relationship(
        "SoccerTeam",
        back_populates="as_starwars_in_matches",
        foreign_keys=[starwars_team_id],
    )
    pokemon_team: Mapped["SoccerTeam"] = relationship(
        "SoccerTeam",
        back_populates="as_pokemon_in_matches",
        foreign_keys=[pokemon_team_id],
    )
    showdown_actions: Mapped[list["ShowdownAction"]] = relationship(
        "ShowdownAction",
        back_populates="soccer_match",
        cascade="all, delete-orphan",
    )
