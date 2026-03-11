from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from super_soccer_showdown.db.base import Base
from super_soccer_showdown.db.models.enums import PositionEnum


class StarWarsTeamComposition(Base):
    __tablename__ = "starwars_team_composition"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("soccer_team.id"), nullable=False)
    player_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("starwars_data.id"), nullable=False)
    position: Mapped[PositionEnum] = mapped_column(sa.Enum(PositionEnum), nullable=False)

    team: Mapped["SoccerTeam"] = relationship("SoccerTeam", back_populates="starwars_players")
    player: Mapped["StarWarsData"] = relationship("StarWarsData", back_populates="team_participation")
