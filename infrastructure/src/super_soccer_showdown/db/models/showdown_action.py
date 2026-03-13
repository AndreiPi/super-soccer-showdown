from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from super_soccer_showdown.db.base import Base
from super_soccer_showdown.db.models.enums import UniverseEnum

if TYPE_CHECKING:
    from super_soccer_showdown.db.models.soccer_match import SoccerMatch


class ShowdownAction(Base):
    __tablename__ = "showdown_action"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    soccer_match_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("soccer_match.id"), nullable=False)
    action_number: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    team_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("soccer_team.id"), nullable=False)
    team_universe: Mapped[UniverseEnum] = mapped_column(
        sa.Enum(
            UniverseEnum,
            name="universeenum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    scorer: Mapped[str] = mapped_column(sa.String(length=200), nullable=False)
    scorer_source_id: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    against: Mapped[str] = mapped_column(sa.String(length=200), nullable=False)
    is_goal: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)

    soccer_match: Mapped["SoccerMatch"] = relationship("SoccerMatch", back_populates="showdown_actions")
